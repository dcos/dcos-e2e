"""
Custom Sphinx extensions.
"""

from typing import List

from sphinx.application import Sphinx

import dcos_e2e

# Due to the dash in the name, we cannot import sphinx-prompt using a normal
# import.
_SPHINX_PROMPT = __import__('sphinx-prompt')


class VersionPrompt(_SPHINX_PROMPT.PromptDirective):  # type: ignore
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
        self.content = [  # pylint: disable=attribute-defined-outside-init
            item.replace(placeholder, release) for item in self.content
        ]  # type: List[str]
        return list(_SPHINX_PROMPT.PromptDirective.run(self))


def setup(app: Sphinx) -> None:
    """
    Add the custom directives to Sphinx.
    """
    app.add_directive('version-prompt', VersionPrompt)
