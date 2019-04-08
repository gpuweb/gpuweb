all: index.html webgpu.idl

index.html: index.bs
	bikeshed -f spec index.bs

webgpu.idl: index.bs
	python extract-idl.py index.bs > webgpu.idl

online:
	curl https://api.csswg.org/bikeshed/ -F file=@index.bs -F force=1 > index.html
	python extract-idl.py index.bs > webgpu.idl
