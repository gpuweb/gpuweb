#!/usr/bin/env perl
# Extract the grammar from the WSGL spec source.
# This uses a bunch of heuristics to work around irregularities.
#
# Usage:
#    perl extract_grammar.pl index.bs

use strict;
use Data::Dumper;

my $prefix = "wgsl_parse_";

my $show_raw = 0;
my $show_dump = 0;

#### TODO: Must rewrite the ( ) ? and + in grammar rules, then remove this.
my $santize_re_in_rules = 1;

my ($tokens_ref, $grammar_lines_ref) = GetTokensAndGrammarLines(<>);
my $raw_grammar = Parse($tokens_ref, $grammar_lines_ref);
open(my $flex_fh, ">", "wgsl.l") or die "can't open wgsl.l for writing: $!";
WriteLexer($flex_fh, $tokens_ref);
close $flex_fh;
open(my $bison_fh, ">", "wgsl.y") or die "can't open wgsl.y for writing: $!";
WriteGrammar($bison_fh, $tokens_ref, $raw_grammar);
close $bison_fh;
print Dumper($raw_grammar) if $show_dump;

exit 0;

# Writes the Flex definition to the given file.
sub WriteLexer($$) {
  my ($flex_fh, $tokens_ref) = @_;
  # Write flex file
  foreach my $key (sort {$a cmp $b } keys %$tokens_ref) {
    my $rule = ${$tokens_ref}{$key};
    if (($key eq 'IDENT') or  ($key =~ m/_LITERAL/)) {
      # Escape "
      $rule =~ s/(")/\\$1/g;
      $rule =~ s/MINUS/\\-/g;
      $rule =~ s/PLUS/\\+/g;
      $rule =~ s/PERIOD/\\./g;
    } else {
      # Escape characters: [ ] ( ) . * ? + { } / | ^
      $rule =~ s/([\[\]\(\)\.\*\?\+\{\}\/\|\^])/\\$1/g;
    }
    print $flex_fh  "$key  $rule\n";
  }
  print $flex_fh "\n%%\n";
  # The list of deferred rules.  They must go later or they may shadow
  # a previous definition.
  my @deferred = ();
  foreach my $key (sort {$a cmp $b } keys %$tokens_ref) {
    if ($key eq 'IDENT') {
      push @deferred, "{$key}  { return $key; }\n";
    } else {
      print $flex_fh "{$key}  { return $key; }\n";
    }
  }
  print $flex_fh @deferred;
  # Flex has a special representation for EOF.
  print $flex_fh "<<EOF>>  { return EOF; }\n";
  print $flex_fh "\n%%\n";
}

sub WriteGrammar($$$) {
  my ($bison_fh, $tokens_ref, $grammar) = @_;
  foreach my $key (sort {$a cmp $b } keys %$tokens_ref) {
    print $bison_fh "%token $key\n";
  }
  print $bison_fh "%token EOF\n";
  print $bison_fh "\n%%\n\n";

  my $rules_ref = $grammar->{'rule'};
  foreach my $rule_key ( sort keys %$rules_ref ) {
    print $bison_fh $rule_key, ":";
    # get the list of right hand sides
    my @rhs_list = @{$rules_ref->{$rule_key}};
    my $first = 1;
    foreach my $rhs (@rhs_list) {
      print $bison_fh " |" unless $first;
      $first = 0;
      my @words = @$rhs;
      if ($santize_re_in_rules) {
        @words = (map { s/[()?+*]//g; $_ } (@words));
      }
      print $bison_fh ' ', join(' ', @words), "\n";
    }
    print $bison_fh "\n";
  }
}

# Returns the list of token definitions and grammar-defining lines
# from the WGSL spec source.
# Input is the list of lines from the WGSL spec source.
sub GetTokensAndGrammarLines(@) {
  my (@input) = @_;
  my $in_grammar = 0;
  my $in_tokens = 0;
  my @grammar_lines = ();
  # Key is token name, value is regexp
  my %token = ();
  foreach (@input) {
    chomp;
    my $line = $_;
    if ($line =~ m/<td>Token<td>/) {
      $in_tokens = 1;
    } elsif ($line =~ m/# Syntactic Tokens #/i) {
      $in_tokens = 1;
    } elsif ($in_tokens && ($line =~ m/<tr><td>`(\S+?)`<td>(.*)/)) {
      # This is a token definition from a regular expression
      # Preprocess into Bison/Flex form.
      my $name = $1;
      my $re = $2;
      $re =~ s/\s*#.*//; # Remove trailing comment
      $re =~ s/^`//; # Remove leading tick, if present
      $re =~ s/`$//; # Remove trailing tick, if present
      $re =~ s/\s+//g;  # Remove spaces
      $token{$name} = $re;
    } elsif ($in_tokens && ($line =~ m/<\/table>/)) {
      $in_tokens = 0;
    } elsif ($line =~ m/^<pre\s+class='def'/) {
      $in_grammar = 1;
    } elsif ($line =~ m/^<\/pre>/) {
      $in_grammar = 0;
    } elsif ($in_grammar) {
      #    $line =~ s/--.*//; # For comments like "-- Capability"
      $line =~ s/\s+/ /g;
      push (@grammar_lines, $line) if is_valid_grammar_line($line);
    }
  }
  return (\%token, \@grammar_lines);
}

# Transforms a list of grammar lines into a structured representation
# of the grammar.
sub Parse($$) {
  my ($tokens_ref, $grammar_lines_ref) = @_;

  # Key is a terminal or nonterminal in the grammar.
  # The value is insignificant.
  my %symbol = ();
  # Key is the production result, value is right-hand-sides
  # Each right-hand-side is a list of tokens.
  my %rule = ();

  # Name of the nonterminal on the left-hand-side of rules
  # that we are currently parsing.
  my $lhs = undef;
  # A reference to the most recently addeded rule right-hand-side.
  my $last_rhs = undef;
  foreach my $line (@$grammar_lines_ref) {
    print $line,"\n" if $show_raw;
    if ($line =~ m/^(\S+)$/) {
      my $name = $1;
      die "more than one definition for $name" if exists $rule{$name};
      $lhs = $name;
      $symbol{$lhs} = 1;
      $rule{$name} = [];
    } elsif ($line =~ m/^ [:|]/) {
      my @parts = split(/\s+/, $line);
      shift @parts; # Skip the initial ' '
      shift @parts; # Skip the initial : or |
      @parts = split_re(@parts);
      foreach my $part (@parts) { $symbol{$part} = 1; }
      $last_rhs = [@parts];
      push @{$rule{$lhs}}, $last_rhs;
    } elsif ($line =~ m/^ [\(|\w]/) {
      # Assume this is a continuation of the most recent RHS
      my @parts = split(/\s+/, $line);
      shift @parts; # Skip the initial ' '
      @parts = split_re(@parts);
      die unless defined $last_rhs;
      push @$last_rhs, @parts;
    } else {
      die "unknown line: $line";
    }
  }
  my @symbols = grep { is_valid_symbol($_) } (sort { $a cmp $b } keys %symbol);
  # Make sure each symbol has a token definition
  my @errors = ();
  foreach my $symbol (@symbols) {
    next if $symbol eq 'EOF'; # Handled specially.
    push(@errors, "error: token $symbol has no definition\n")
       unless exists ${$tokens_ref}{$symbol};
  }
  die @errors if $#errors >=0;
  return {tokens => $tokens_ref, symbol => [@symbols] , rule => \%rule};
}

# Returns 1 if the line is a valid grammar line, and 0 otherwise.
sub is_valid_grammar_line {
  my ($line) = @_;
  return 0 if $line =~ m/\WOp[A-Z]/;
  return 0 if $line =~ m/TODO/;
  return 0 if $line =~ m/^`/;
  return 0 if $line =~ m/Otherwise,/;
  return 0 if $line =~ m/^ R\d/; # image format
  return 0 if $line =~ m/^ Rg/; # image format
  return 0 if $line =~ m/^ \?\?\?/; # image format
  return 0 if $line eq '';
  return 1;
}

# Transforms a list of strings to break up regular expression
# meta-symbols into their own individual tokens. For example,
# an input like:
#    '(ab', '|', 'c)?'
# becomes
#    '(', 'ab', '|', 'c', ')', '?'
sub split_re {
  # First split between word and non-word boundaries.
  my @result = map {split(/\b/)} @_;
  @result = map {
    if ($_ =~ m/^\W/) {
      # Split non-words by character
      split(//);
    } else {
      # Keep words together
      $_;
    }
  } @result;
  return @result;
}

sub is_valid_symbol($) {
  return $_ =~ m/^[A-Z_]+$/;
}
