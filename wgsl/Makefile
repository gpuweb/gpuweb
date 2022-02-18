all: index.html grammar/grammar.js


GHC=https://github.com/gpuweb/gpuweb/blob
index.html: index.pre.html Makefile
	# Append another line to the "This version:" metadata at the top.
	sed -e "s,gpuweb/wgsl/</a>,gpuweb/wgsl/</a><br><a href=\"$(GHC)/$(shell git rev-parse HEAD)/wgsl/index.bs\">$(GHC)/$(shell git rev-parse HEAD)/wgsl/index.bs</a>," <index.pre.html >index.html

index.pre.html: index.bs Makefile
	bikeshed --die-on=everything spec index.bs index.pre.html

grammar/grammar.js: index.bs extract-grammar.py
	python3 extract-grammar.py index.bs grammar/grammar.js

online:
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F output=err
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F force=1 > index.html
