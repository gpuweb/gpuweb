#!/usr/bin/env perl
# Extract the grammar from the WSGL spec source.
# This uses a bunch of heuristics to work around irregularities.
#
# Usage:
#    perl extract_grammar.pl index.bs

use strict;
use Data::Dumper;

my $show_raw = 1;
my $show_dump = 1;

my @grammar_lines = GetGrammarLines(<>);
my $raw_grammar = Parse(@grammar_lines);
print Dumper($raw_grammar) if $show_dump;
exit 0;

# Returns the list of grammar-defining lines from the WGSL spec source.
# Input is the list of lines from the WGSL spec source.
sub GetGrammarLines(@) {
  my (@input) = @_;
  my $in_grammar = 0;
  my @grammar_lines = ();
  foreach (@input) {
    chomp;
    my $line = $_;
    if ($line =~ m/^<pre\s+class='def'/) {
      $in_grammar = 1;
    } elsif ($line =~ m/^<\/pre>/) {
      $in_grammar = 0;
    } elsif ($in_grammar) {
      #    $line =~ s/--.*//; # For comments like "-- Capability"
      $line =~ s/\s+/ /g;
      push (@grammar_lines, $line) if is_valid($line);
    }
  }
  return @grammar_lines;
}

# Transforms a list of grammar lines into a structured representation
# of the grammar.
sub Parse(@) {
  my (@grammar_lines) = @_;
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
  foreach my $line (@grammar_lines) {
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
  my @symbols = sort keys %symbol;
  return [symbol => [@symbols] , rule => \%rule];
}

# Returns 0 if the line is invalid, and 1 otherwise.
sub is_valid {
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
