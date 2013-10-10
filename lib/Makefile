PWD = $(shell pwd)
VERSION = $(shell git describe --tags)

build:
	sed -i "s/^VERSION = .*/VERSION = '${VERSION}'/" common.py

%:
	@echo $@
