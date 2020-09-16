all: index.html

index.html: index.bs
	bikeshed --die-on=everything spec index.bs

online:
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F output=err
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F force=1 > index.html

grammar: wgsl.scan.c wgsl.tab.c wgsl.tab.h

wgsl.scan.c : wgsl.l wgsl.tab.h
	flex -o $@ $<

wgsl.tab.c wgsl.tab.h: wgsl.y
	bison -d -b wgsl $<

wgsl.y wgsl.l: extract_grammar.pl index.bs Makefile
	perl extract_grammar.pl index.bs



