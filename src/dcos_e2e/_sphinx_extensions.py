"""
Custom Sphinx extensions.
"""

import importlib
from sphinx.application import Sphinx
from typing import List

import dcos_e2e

# Due to the dash in the name, the sphinx-prompt module is unloadable
# using a normal import.
sphinx_prompt = __import__('sphinx-prompt')


class VersionPrompt(sphinx_prompt.PromptDirective):  # type: ignore
    """
    Similar to PromptDirective but replaces a placeholder with the
    latest release.

    Usage example:

    .. version-prompt:: bash $

       $ dcos-docker --version
       dcos-docker, version |release|
    """

    def run(self) -> List:
        """
        Replace the release placeholder with the release version.
        """
        placeholder = '|release|'
        version = dcos_e2e.__version__
        release = version.split('+')[0]
        self.content: List[str] = [
            item.replace(placeholder, release) for item in self.content
        ]
        return list(sphinx_prompt.PromptDirective.run(self))


def setup(app: Sphinx) -> None:
    """
    Add the custom directives to Sphinx.
    """
    app.add_directive('version-prompt', VersionPrompt)
