all: index.html webgpu.idl

GHC=https://github.com/gpuweb/gpuweb/blob
index.html: index.pre.html Makefile
	# Append another line to the "This version:" metadata at the top.
	sed -e "s,gpuweb.github.io/gpuweb/</a>,gpuweb.github.io/gpuweb/</a><br><a href=\"$(GHC)/$(shell git rev-parse HEAD)/spec/index.bs\">$(GHC)/$(shell git rev-parse HEAD)/spec/index.bs</a>," <index.pre.html >index.html

index.pre.html: index.bs
	bikeshed --die-on=everything spec index.bs index.pre.html

webgpu.idl: index.bs extract-idl.py
	python3 extract-idl.py index.bs > webgpu.idl

online:
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F output=err
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F die-on=everything > index.html
	python3 extract-idl.py index.bs > webgpu.idl
