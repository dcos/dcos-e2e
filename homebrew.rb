class Homebrew < Formula
  include Language::Python::Virtualenv

  url "https://nofile.io/g/fE8wkd1eztIVUvciIUBy6FpmJNLTG7UT6kEJTWTHU1H7D2NXUHWrwHdE3zL359XL/dcos-e2e.tar/"
  #
  # resource "six" do
  #   url "https://pypi.python.org/packages/source/s/six/six-1.9.0.tar.gz"
  #   sha256 "e24052411fc4fbd1f672635537c3fc2330d9481b18c0317695b46259512c91d5"
  # end
  #
  # resource "parsedatetime" do
  #   url "https://pypi.python.org/packages/source/p/parsedatetime/parsedatetime-1.4.tar.gz"
  #   sha256 "09bfcd8f3c239c75e77b3ff05d782ab2c1aed0892f250ce2adf948d4308fe9dc"
  # end

  depends_on "python3"
  def install
    virtualenv_install_with_resources
    system "python", *Language::Python.setup_install_args(libexec/"dcos-e2e-master")
  end
end
