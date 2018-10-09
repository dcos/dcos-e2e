"""
Custom Sphinx extensions.
"""

from typing import List

from sphinx.application import Sphinx

import dcos_e2e

# Due to the dash in the name, we cannot import sphinx-prompt using a normal
# import.
_SPHINX_PROMPT = __import__('sphinx-prompt')


class SmartPrompt(_SPHINX_PROMPT.PromptDirective):  # type: ignore
    """
    Similar to PromptDirective but replaces a placeholder with the
    latest release and other variables.

    Usage example:

    .. smart-prompt:: bash $

       $ dcos-docker --version
       dcos-docker, version |release|
    """

    def run(self) -> List:
        """
        Replace the release placeholder with the release version.
        """
        version = dcos_e2e.__version__
        release = version.split('+')[0]
        placeholder_replace_pairs = (
            ('|release|', release),
            ('|github-owner|', 'dcos'),
            ('|github-repository|', 'dcos-e2e'),
        )
        new_content = []
        self.content = (  # pylint: disable=attribute-defined-outside-init
            self.content
        )  # type: List[str]
        existing_content = self.content
        for item in existing_content:
            for pair in placeholder_replace_pairs:
                original, replacement = pair
                item = item.replace(original, replacement)
            new_content.append(item)

        self.content = (  # pylint: disable=attribute-defined-outside-init
            new_content
        )
        return list(_SPHINX_PROMPT.PromptDirective.run(self))


def setup(app: Sphinx) -> None:
    """
    Add the custom directives to Sphinx.
    """
    app.add_directive('smart-prompt', SmartPrompt)
