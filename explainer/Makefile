.PHONY: all clean

all: index.html

clean:
	rm -f index.html webgpu.idl

index.html: *.bs
	DIE_ON=everything ../tools/invoke-bikeshed.sh index.html *.bs
