class Dcose2e < Formula
  include Language::Python::Virtualenv

  url "https://github.com/dcos/dcos-e2e/archive/2018.07.03.3.tar.gz"
  head "https://github.com/dcos/dcos-e2e.git"
  homepage "http://dcos-e2e.readthedocs.io/en/latest/cli.html"
  depends_on "python3"
  depends_on "pkg-config"


resource "PyYAML" do
  url "https://github.com/yaml/pyyaml/archive/4.2b2.zip"
  sha256 "851e17742830a79dacba60b06ad1cc52b67b0a4e78433d442c74756ceebe23b8"
end


  def install
    virtualenv_install_with_resources
  end

  test do
      ENV["LC_ALL"] = "en_US.utf-8"
      ENV["LANG"] = "en_US.utf-8"
      system "#{bin}/dcos_docker", "--help"
  end
end
