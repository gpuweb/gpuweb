all: index.html

index.html: index.bs
	bikeshed --die-on=everything spec index.bs

online:
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F force=1 > index.html
