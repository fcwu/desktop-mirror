OUT        = xrectsel
VERSION    = $(shell git describe --tags)

SRC        = ${wildcard *.c}
OBJ        = ${SRC:.c=.o}
DISTFILES  = Makefile xrectsel.c

PREFIX    ?= /usr
MANPREFIX ?= ${PREFIX}/share/man

CPPFLAGS  := -DVERSION=\"${VERSION}\" ${CPPFLAGS}
CFLAGS    := --std=c99 -g -pedantic -Wall -Wextra -Wno-variadic-macros ${CFLAGS}
LDFLAGS   := -lX11 ${LDFLAGS}

all: ${OUT}

${OUT}: ${OBJ}
	${CC} -o $@ ${OBJ} ${LDFLAGS}

strip: ${OUT}
	strip --strip-all ${OUT}

install: xrectsel
	install -D -m755 xrectsel ${DESTDIR}${PREFIX}/bin/xrectsel

uninstall:
	@echo removing executable file from ${DESTDIR}${PREFIX}/bin
	rm -f ${DESTDIR}${PREFIX}/bin/xrectsel

dist: clean
	mkdir ffcast-${VERSION}
	cp ${DISTFILES} ffcast-${VERSION}
	sed "s/\(^VERSION *\)= .*/\1= ${VERSION}/" < Makefile > ffcast-${VERSION}/Makefile
	rm -rf ffcast-${VERSION}

clean:
	${RM} ${OUT} ${OBJ}

%:
	@echo

.PHONY: clean dist install uninstall
