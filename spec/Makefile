.PHONY: all online

all: index.html webgpu.idl

index.html: index.bs sections/*.bs
	bikeshed --die-on=everything spec index.bs

webgpu.idl: index.bs sections/*.bs extract-idl.py
	python extract-idl.py index.bs > webgpu.idl

online: index.bs sections/*.bs webgpu.idl
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F output=err
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F force=1 > index.html
