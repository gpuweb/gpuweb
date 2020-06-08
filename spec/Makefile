.PHONY: all online

all: index.html webgpu.idl

index.html: index.bs sections/*.bs
	bikeshed --die-on=everything spec index.bs

webgpu.idl: index.bs sections/*.bs extract-idl.py
	python extract-idl.py index.bs > webgpu.idl
