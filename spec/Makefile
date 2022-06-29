.PHONY: all clean

all: index.html webgpu.idl

clean:
	rm -f index.html index.pre.html webgpu.idl

index.pre.html: *.bs
	DIE_ON=everything bash ../tools/invoke-bikeshed.sh index.pre.html *.bs

GHC=https://github.com/gpuweb/gpuweb/blob
index.html: index.pre.html
	@echo 'Inserting source permalink: index.pre.html -> index.html'
	@sed -e "s,gpuweb.github.io/gpuweb/</a>,gpuweb.github.io/gpuweb/</a><br><a href=\"$(GHC)/$(shell git rev-parse HEAD)/spec/index.bs\">$(GHC)/$(shell git rev-parse HEAD)/spec/index.bs</a>," <index.pre.html >index.html

webgpu.idl: index.html ../tools/extract-idl-index.py
	python3 ../tools/extract-idl-index.py index.html > webgpu.idl
