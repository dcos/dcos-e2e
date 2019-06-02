class {class_name} < Formula
  include Language::Python::Virtualenv

  url "{archive_url}"
  head "{head_url}"
  homepage "{homepage_url}"
  depends_on "python3"
  depends_on "pkg-config"

{resource_stanzas}

  def install
    # Without this we hit various issues including
    # https://github.com/takluyver/flit/issues/245.
    # All of these issues are caught by CI so it is safe to remove this
    # and then run CI.
    ENV["PIP_USE_PEP517"] = "false"
    virtualenv_install_with_resources
  end
end
