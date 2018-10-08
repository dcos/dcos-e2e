"""
Tests for Sphinx version extensions.
"""

import subprocess
from pathlib import Path
from textwrap import dedent

import dcos_e2e

def test_version_prompt(tmpdir):
    """
    The ``version-prompt`` directive replaces the placemarker
    ``|release|`` in a source file with the current installable version in
    the output file.
    """
    version = dcos_e2e.__version__
    release = version.split('+')[0]
    source_directory = tmpdir.mkdir('source')
    source_file = source_directory.join('contents.rst')
    source_file.write(dedent('''
        .. version-prompt:: bash $

           $ PRE-|release|-POST
        '''))
    destination_directory = tmpdir.mkdir('destination')
    sphinx_build = subprocess.check_output([
        'sphinx-build', '-b', 'html',
        '-C',   # don't look for config file, use -D flags instead
        '-D', 'extensions=dcos_e2e._sphinx_extensions',
        # directory containing source/config files
        str(source_directory),
        # directory containing build files
        str(destination_directory),
        str(source_file),
    ])  # source file to process
    expected = 'PRE-{release}-POST'.format(release=release)
    content_html = Path(str(destination_directory)) / 'contents.html'
    assert expected in content_html.read_text()
