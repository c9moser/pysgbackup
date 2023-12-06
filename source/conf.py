# vim: syn=python ts=4 sts=4 smartindent expandtab
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os

PROJECT_ROOT=os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0,PROJECT_ROOT)
import sgbackup
from sgbackup.config import settings

project = 'pysgbackup'
copyright = '2023, Christian Moser'
author = 'Christian Moser'

release = '.'.join((str(i) for i in settings.VERSION_NUMBER))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
]

templates_path = ['_templates']
exclude_patterns = []

source_suffix = {
    '.rst':'restructuredtext',
    '.txt':'restructuredtext',
    #'.md':'markdown',
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
