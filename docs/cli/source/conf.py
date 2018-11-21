#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration for Sphinx.
"""

# pylint: disable=invalid-name

import os
import sys

import dcos_e2e

sys.path.insert(0, os.path.abspath('.'))

extensions = [
    'sphinx-prompt',
    'sphinx_substitution_extensions',
    'sphinx.ext.autodoc',
    'sphinx.ext.extlinks',
    'sphinx_click.ext',
    'sphinx_paramlinks',
    'sphinxcontrib.spelling',
    'sphinx.ext.autosectionlabel',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = 'miniDC/OS'
copyright = '2018, Adam Dangoor'  # pylint: disable=redefined-builtin
author = 'Adam Dangoor'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
version = dcos_e2e.__version__
release = version.split('+')[0]
autosectionlabel_prefix_document = True

substitutions = [
    ('|release|', release),
    ('|github-owner|', 'dcos'),
    ('|github-repository|', 'dcos-e2e'),
    ('|brewfile-stem|', 'minidcos'),
]

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
nitpicky = True
warning_is_error = True

html_show_copyright = False
html_show_sphinx = False
html_show_sourcelink = False

html_theme_options = {
    'show_powered_by': 'false',
}

html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'searchbox.html',
    ],
}

# Don't check anchors because many websites use #! for AJAX magic
# http://sphinx-doc.org/config.html#confval-linkcheck_anchors
linkcheck_anchors = False
# Retry link checking to avoid transient network errors.
linkcheck_retries = 5
linkcheck_ignore = [
    r'https://github.com/mesosphere/maws',
    # This is often down.
    r'https://www.virtualbox.org/wiki/Downloads',
]

spelling_word_list_filename = '../../../spelling_private_dict.txt'

autodoc_member_order = 'bysource'

extlinks = {
    'issue': ('https://jira.mesosphere.com/browse/%s', 'issue '),
}

rst_epilog = """
.. |project| replace:: {project}
.. |github-owner| replace:: dcos
.. |github-repository| replace:: dcos-e2e
""".format(project=project)
