all: index.html

index.html: index.bs
	bikeshed --die-on=everything spec index.bs

online:
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F output=err
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F force=1 > index.html

grammar: wgsl.y wgsl.scan.c

wgsl.scan.c : wgsl.l
	flex -o $@ $<

wgsl.y wgsl.l: extract_grammar.pl index.bs
	perl extract_grammar.pl index.bs



