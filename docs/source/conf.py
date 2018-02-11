#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pylint: disable=invalid-name

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_napoleon_typehints',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = 'DC/OS E2E'
copyright = '2018, Adam Dangoor'  # pylint: disable=redefined-builtin
author = 'Adam Dangoor'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
version = '2018.01.25.0'
release = '2018.01.25.0'

language = None

# The name of the syntax highlighting style to use.
pygments_style = 'sphinx'
html_theme = 'alabaster'
html_static_path = []

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}


# Output file base name for HTML help builder.
htmlhelp_basename = 'DCOSE2Edoc'
autoclass_content = 'init'
