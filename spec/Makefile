.PHONY: all clean

all: index.html webgpu.idl

clean:
	rm -f index.html index.pre.html webgpu.idl

index.pre.html: *.bs
	DIE_ON=everything ../tools/invoke-bikeshed.sh index.pre.html *.bs

index.html: index.pre.html
	../tools/add-git-head-to-bikeshed-header.sh index.pre.html > index.html

webgpu.idl: index.html ../tools/extract-idl-index.py
	../tools/extract-idl-index.py index.html > webgpu.idl
