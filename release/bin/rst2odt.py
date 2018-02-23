#!/private/var/folders/3l/ffdytd9n2cnbgch4rwt6k7jm0000gn/T/tmp.DSZjtJOH/dcos-e2e/release/bin/python3.6

# $Id: rst2odt.py 5839 2009-01-07 19:09:28Z dkuhlman $
# Author: Dave Kuhlman <dkuhlman@rexx.com>
# Copyright: This module has been placed in the public domain.

"""
A front end to the Docutils Publisher, producing OpenOffice documents.
"""

import sys
try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline_to_binary, default_description
from docutils.writers.odf_odt import Writer, Reader


description = ('Generates OpenDocument/OpenOffice/ODF documents from '
               'standalone reStructuredText sources.  ' + default_description)


writer = Writer()
reader = Reader()
output = publish_cmdline_to_binary(reader=reader, writer=writer,
    description=description)

