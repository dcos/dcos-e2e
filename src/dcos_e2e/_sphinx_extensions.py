"""
Custom Sphinx extensions.
"""

import importlib

import dcos_e2e

# Due to the dash in the name, the sphinx-prompt module is unloadable
# using a normal import - use the importlib machinery instead.
sphinx_prompt = importlib.import_module('sphinx-prompt')


class VersionPrompt(sphinx_prompt.PromptDirective):
    """
    Similar to PromptDirective but replaces a placeholder with the
    latest release.

    Usage example:

    .. version-prompt:: bash $

       $ dcos-docker --version
       dcos-docker, version |release|
    """
    def run(self):
        placeholder = '|release|'
        version = dcos_e2e.__version__
        release = version.split('+')[0]
        self.content = [item.replace(placeholder, release) for
                        item in self.content]
        return sphinx_prompt.PromptDirective.run(self)


def setup(app):
    app.add_directive('version-prompt', VersionPrompt)
