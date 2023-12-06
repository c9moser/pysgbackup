# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build
SPHINXAPIDOC = sphinx-apidoc
SPHINXAPIDOC_OUTDIR = source/pysgbackup
SPHINXAPIDOC_PACKAGE = sgbackup
SPHINXAPIDOC_ARGS = --ext-autodoc -e -M

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

apidoc:
	#@$(SPHINXAPIDOC) $(SPHINXAPIDOC_ARGS) -o $(SPHINXAPIDOC_OUTDIR) $(SPHINXAPIDOC_PACKAGE)
	@echo sphinx-apidoc not running

install:
	@pip install .

.PHONY: help Makefile apidoc install
	
# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile apidoc
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
