class {class_name} < Formula
  include Language::Python::Virtualenv

  url "{archive_url}"
  head "{head_url}"
  homepage "{homepage_url}"
  depends_on "python3"
  depends_on "pkg-config"

{resource_stanzas}

  def install
    wanted = %w[python python@2 python2 python3 python@3 pypy pypy3].select {{ |py| needs_python?(py) }}
    raise FormulaAmbiguousPythonError, self if wanted.size > 1

    python = wanted.first || "python2.7"
    python = "python3" if python == "python"
    venv = virtualenv_create(libexec, python.delete("@"))
    venv.instance_variable_get(:@formula).system venv.instance_variable_get(:@venv_root)/"bin/pip", "install",
                    "-v", "--no-deps",
                    "--ignore-installed",
                    "--upgrade",
                    "--force-reinstall",
                    "pip<19"
    venv.pip_install resources
    venv.pip_install_and_link buildpath
    venv
  end
end
