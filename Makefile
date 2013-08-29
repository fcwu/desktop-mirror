SUBDIRS = xrectsel
PWD = $(shell pwd)

.PHONY: subdirs $(SUBDIRS)

%:
	@echo make ${@} in $(SUBDIRS)
	@for dir in $(SUBDIRS); do \
		PREFIX=$(PWD) $(MAKE) -C $$dir ${@}; \
	done

subdirs: $(SUBDIRS)

$(SUBDIRS):
		PREFIX=$(PWD) $(MAKE) -C $@

