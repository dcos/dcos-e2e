#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration for Sphinx.
"""

# pylint: disable=invalid-name

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.spelling',
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

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ],
}

# Output file base name for HTML help builder.
htmlhelp_basename = 'DCOSE2Edoc'
autoclass_content = 'init'
intersphinx_mapping = {'python': ('https://docs.python.org/3.5', None)}
nitpicky = True
warning_is_error = True
nitpick_ignore = [
    ('py:class', 'dcos_e2e.backends._base_classes.ClusterBackend'),
    ('py:class', 'dcos_e2e.backends._base_classes.ClusterManager'),
    ('py:class', 'dcos_e2e.backends._docker.DockerCluster'),
    ('py:exc', 'RetryError'),
]

html_show_copyright = False
html_show_sphinx = False
html_show_sourcelink = False

html_theme_options = {
    'show_powered_by': 'false',
    'fixed_sidebar': True,
    'sidebar_includehidden': False,
}

html_sidebars = {
    '**': [
        'about.html',
        'globaltoc.html',
        'searchbox.html',
    ],
}

# Don't check anchors because many websites use #! for AJAX magic
# http://sphinx-doc.org/config.html#confval-linkcheck_anchors
linkcheck_anchors = False

spelling_word_list_filename = '../../spelling_private_dict.txt'
