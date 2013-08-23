SUBDIRS = xrectsel

.PHONY: subdirs $(SUBDIRS)

%:
	@echo make ${@} in $(SUBDIRS)
	@for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir ${@}; \
	done

subdirs: $(SUBDIRS)

$(SUBDIRS):
		$(MAKE) -C $@

