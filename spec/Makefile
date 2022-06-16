.PHONY: all clean

all: index.html webgpu.idl

clean:
	rm -f index.html index.pre.html webgpu.idl

index.pre.html: *.bs
	DIE_ON=everything bash ../tools/invoke-bikeshed.sh index.pre.html *.bs

index.html: index.pre.html
	bash ../tools/add-git-head-to-bikeshed-header.sh index.pre.html > index.html

webgpu.idl: index.html ../tools/extract-idl-index.py
	python3 ../tools/extract-idl-index.py index.html > webgpu.idl
