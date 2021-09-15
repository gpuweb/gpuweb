all: index.html grammar/grammar.js

index.html: index.bs
	bikeshed --die-on=everything spec index.bs

grammar/grammar.js: index.bs extract-grammar.py
	python3 extract-grammar.py index.bs grammar/grammar.js

online:
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F output=err
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F force=1 > index.html
