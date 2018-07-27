class Dcose2e < Formula
  include Language::Python::Virtualenv

  url "https://github.com/dcos/dcos-e2e/archive/2018.07.27.0.tar.gz"
  head "https://github.com/dcos/dcos-e2e.git"
  homepage "http://dcos-e2e.readthedocs.io/en/latest/cli.html"
  depends_on "python3"
  depends_on "pkg-config"

  resource "adal" do
    url "https://files.pythonhosted.org/packages/80/65/d62a4b43eca475cf865ffc2acc18be08fe3430f374b0a0d931d7063b5d72/adal-1.0.2.tar.gz"
    sha256 "4c020807b3f3cfd90f59203077dd5e1f59671833f8c3c5028ec029ed5072f9ce"
  end

  resource "asn1crypto" do
    url "https://files.pythonhosted.org/packages/fc/f1/8db7daa71f414ddabfa056c4ef792e1461ff655c2ae2928a2b675bfed6b4/asn1crypto-0.24.0.tar.gz"
    sha256 "9d5c20441baf0cb60a4ac34cc447c6c189024b6b4c6cd7877034f4965c464e49"
  end

  resource "atomicwrites" do
    url "https://files.pythonhosted.org/packages/a1/e1/2d9bc76838e6e6667fde5814aa25d7feb93d6fa471bf6816daac2596e8b2/atomicwrites-1.1.5.tar.gz"
    sha256 "240831ea22da9ab882b551b31d4225591e5e447a68c5e188db5b89ca1d487585"
  end

  resource "attrs" do
    url "https://files.pythonhosted.org/packages/e4/ac/a04671e118b57bee87dabca1e0f2d3bda816b7a551036012d0ca24190e71/attrs-18.1.0.tar.gz"
    sha256 "e0d0eb91441a3b53dab4d9b743eafc1ac44476296a2053b6ca3af0b139faf87b"
  end

  resource "azure-common" do
    url "https://files.pythonhosted.org/packages/e0/c8/49ccf6e2f0edf3add1f915afa21d9a75947fb57c028d6792b5ed09b79159/azure-common-1.1.13.zip"
    sha256 "b087e80e8f0adc858f0a2b9ba596bb791383f74834b4acc4b47b64ddfa1362e3"
  end

  resource "azure-mgmt-network" do
    url "https://files.pythonhosted.org/packages/94/a9/bf8ae648f37561c3195a7c2fc8d7eecea4b22e90460465b73b45fad5eec9/azure-mgmt-network-2.0.0rc2.zip"
    sha256 "56922cd31a80bd2568aeed7839a0207d9550feb54897bbb9a2a967fed9390abd"
  end

  resource "azure-mgmt-nspkg" do
    url "https://files.pythonhosted.org/packages/fe/66/66eb0d5ead69b7371649466fa160a166de0d1ddafc4a1d7a172858a8abc9/azure-mgmt-nspkg-2.0.0.zip"
    sha256 "e36488d4f5d7d668ef5cc3e6e86f081448fd60c9bf4e051d06ff7cfc5a653e6f"
  end

  resource "azure-mgmt-resource" do
    url "https://files.pythonhosted.org/packages/27/f0/ab10f7851e9437da02b981d79545cd7290380d396d822bf71f99d457637b/azure-mgmt-resource-1.2.2.zip"
    sha256 "fe65dc43c8643a8c3e731783e98334258bf5dc57cf4ae063401e2b05b9d71d71"
  end

  resource "azure-monitor" do
    url "https://files.pythonhosted.org/packages/f5/b1/cd88adb77b15f99d549857827bd3cce59cbf95dc7b46cfad02290ec713db/azure-monitor-0.3.1.zip"
    sha256 "1935f4caf3e58df865121139747f4069490ccbb6acb5ea9b6f4d4b98e7355c56"
  end

  resource "azure-nspkg" do
    url "https://files.pythonhosted.org/packages/06/a2/77820fa07ec4657d6456b67edfa78856b4789ada42d1bb8e8485df19824e/azure-nspkg-2.0.0.zip"
    sha256 "fe19ee5d8c66ee8ef62557fc7310f59cffb7230f0a94701eef79f6e3191fdc7b"
  end

  resource "bcrypt" do
    url "https://files.pythonhosted.org/packages/f3/ec/bb6b384b5134fd881b91b6aa3a88ccddaad0103857760711a5ab8c799358/bcrypt-3.1.4.tar.gz"
    sha256 "67ed1a374c9155ec0840214ce804616de49c3df9c5bc66740687c1c9b1cd9e8d"
  end

  resource "boto3" do
    url "https://files.pythonhosted.org/packages/4f/28/1642a25573c8ffbdcec0ceb09cf5d941f5bc2a0be71179a5d2220e1df3e0/boto3-1.7.58.tar.gz"
    sha256 "ce462e7505c03c3e6708ce6f264ac43d478886082af703ff69c502592df5d4f3"
  end

  resource "botocore" do
    url "https://files.pythonhosted.org/packages/e5/7b/4f0d1613f33b32a8ad8f65c7973a389244e0aecd209db761f5d51291ebc4/botocore-1.10.58.tar.gz"
    sha256 "e0e6b6d1fdbce81c28151136ee919d2cdeee13041559710cd5c93d7e4035a455"
  end

  resource "cachetools" do
    url "https://files.pythonhosted.org/packages/87/41/b3e00059f3c34b57a653d2120d213715abb4327b36fee22e59c1da977d25/cachetools-2.1.0.tar.gz"
    sha256 "90f1d559512fc073483fe573ef5ceb39bf6ad3d39edc98dc55178a2b2b176fa3"
  end

  resource "Cerberus" do
    url "https://files.pythonhosted.org/packages/90/31/e30784a1f9a4b46875cfed1c9f806c188e2181e7ba3b568e81e7b0bc5718/Cerberus-1.2.tar.gz"
    sha256 "f5c2e048fb15ecb3c088d192164316093fcfa602a74b3386eefb2983aa7e800a"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/4d/9c/46e950a6f4d6b4be571ddcae21e7bc846fcbb88f1de3eff0f6dd0a6be55d/certifi-2018.4.16.tar.gz"
    sha256 "13e698f54293db9f89122b0581843a782ad0934a4fe0172d2a980ba77fc61bb7"
  end

  resource "cffi" do
    url "https://files.pythonhosted.org/packages/e7/a7/4cd50e57cc6f436f1cc3a7e8fa700ff9b8b4d471620629074913e3735fb2/cffi-1.11.5.tar.gz"
    sha256 "e90f17980e6ab0f3c2f3730e56d1fe9bcba1891eeea58966e89d352492cc74f4"
  end

  resource "chardet" do
    url "https://files.pythonhosted.org/packages/fc/bb/a5768c230f9ddb03acc9ef3f0d4a3cf93462473795d18e9535498c8f929d/chardet-3.0.4.tar.gz"
    sha256 "84ab92ed1c4d4f16916e05906b6b75a6c0fb5db821cc65e70cbd64a3e2a5eaae"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/95/d9/c3336b6b5711c3ab9d1d3a80f1a3e2afeb9d8c02a7166462f6cc96570897/click-6.7.tar.gz"
    sha256 "f15516df478d5a56180fbf80e68f206010e6d160fc39fa508b65e035fd75130b"
  end

  resource "click-spinner" do
    url "https://files.pythonhosted.org/packages/4d/c4/e4cc6595266021b549f774a20329188e68b63f06896eba94c1c952027c6e/click-spinner-0.1.8.tar.gz"
    sha256 "67b5af5e825faf82a4fc6cda77c58359abe716fb1c9bc12cc7bea9a0cae1fc8e"
  end

  resource "cryptography" do
    url "https://files.pythonhosted.org/packages/ec/b2/faa78c1ab928d2b2c634c8b41ff1181f0abdd9adf9193211bd606ffa57e2/cryptography-2.2.2.tar.gz"
    sha256 "9fc295bf69130a342e7a19a39d7bbeb15c0bcaabc7382ec33ef3b2b7d18d2f63"
  end

  resource "decorator" do
    url "https://files.pythonhosted.org/packages/6f/24/15a229626c775aae5806312f6bf1e2a73785be3402c0acdec5dbddd8c11e/decorator-4.3.0.tar.gz"
    sha256 "c39efa13fbdeb4506c476c9b3babf6a718da943dab7811c206005a4a956c080c"
  end

  resource "docker" do
    url "https://files.pythonhosted.org/packages/f4/cb/5e15c50ec90daa926777f79e7e5cbc00fe2539e677a14c0a491d01f45479/docker-3.4.1.tar.gz"
    sha256 "ad077b49660b711d20f50f344f70cfae014d635ef094bf21b0d7df5f0aeedf99"
  end

  resource "docker-pycreds" do
    url "https://files.pythonhosted.org/packages/9e/7a/109e0a3cc3c19534edd843c16e792c67911b5b4072fdd34ddce90d49f355/docker-pycreds-0.3.0.tar.gz"
    sha256 "8b0e956c8d206f832b06aa93a710ba2c3bcbacb5a314449c040b0b814355bbff"
  end

  resource "docopt" do
    url "https://files.pythonhosted.org/packages/a2/55/8f8cab2afd404cf578136ef2cc5dfb50baa1761b68c9da1fb1e4eed343c9/docopt-0.6.2.tar.gz"
    sha256 "49b3a825280bd66b3aa83585ef59c4a8c82f2c8a522dbe754a8bc8d08c85c491"
  end

  resource "docutils" do
    url "https://files.pythonhosted.org/packages/84/f4/5771e41fdf52aabebbadecc9381d11dea0fa34e4759b4071244fa094804c/docutils-0.14.tar.gz"
    sha256 "51e64ef2ebfb29cae1faa133b3710143496eca21c530f3f71424d77687764274"
  end

  resource "entrypoints" do
    url "https://files.pythonhosted.org/packages/27/e8/607697e6ab8a961fc0b141a97ea4ce72cd9c9e264adeb0669f6d194aa626/entrypoints-0.2.3.tar.gz"
    sha256 "d2d587dde06f99545fb13a383d2cd336a8ff1f359c5839ce3a64c917d10c029f"
  end

  resource "google-api-python-client" do
    url "https://files.pythonhosted.org/packages/4e/92/e4746e646585c8c359781c19984fe8b6b8794a6cfe382cd481329d5252ac/google-api-python-client-1.7.4.tar.gz"
    sha256 "5d5cb02c6f3112c68eed51b74891a49c0e35263380672d662f8bfe85b8114d7c"
  end

  resource "google-auth" do
    url "https://files.pythonhosted.org/packages/a2/39/0c3d41aa96c1bdb9dcc4f646909b82e4c0ed9a1a398e869627a21a0563c4/google-auth-1.5.0.tar.gz"
    sha256 "1745c9066f698eac3da99cef082914495fb71bc09597ba7626efbbb64c4acc57"
  end

  resource "google-auth-httplib2" do
    url "https://files.pythonhosted.org/packages/e7/32/ac7f30b742276b4911a1439c5291abab1b797ccfd30bc923c5ad67892b13/google-auth-httplib2-0.0.3.tar.gz"
    sha256 "098fade613c25b4527b2c08fa42d11f3c2037dda8995d86de0745228e965d445"
  end

  resource "httplib2" do
    url "https://files.pythonhosted.org/packages/fd/ce/aa4a385e3e9fd351737fd2b07edaa56e7a730448465aceda6b35086a0d9b/httplib2-0.11.3.tar.gz"
    sha256 "e71daed9a0e6373642db61166fa70beecc9bf04383477f84671348c02a04cbdf"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/65/c4/80f97e9c9628f3cac9b98bfca0402ede54e0563b56482e3e6e45c43c4935/idna-2.7.tar.gz"
    sha256 "684a38a6f903c1d71d6d5fac066b58d7768af4de2b832e426ec79c30daa94a16"
  end

  resource "isodate" do
    url "https://files.pythonhosted.org/packages/b1/80/fb8c13a4cd38eb5021dc3741a9e588e4d1de88d895c1910c6fc8a08b7a70/isodate-0.6.0.tar.gz"
    sha256 "2e364a3d5759479cdb2d37cce6b9376ea504db2ff90252a2e5b7cc89cc9ff2d8"
  end

  resource "jeepney" do
    url "https://files.pythonhosted.org/packages/18/17/7dbc70bc13dc9c8ba8c9b25fbc8b75dffb6bc7e56c3d7cecd87e6b563e5f/jeepney-0.3.1.tar.gz"
    sha256 "a6f2aa72e61660248d4d524dfccb6405f17c693b69af5d60dd7f2bab807d907e"
  end

  resource "jmespath" do
    url "https://files.pythonhosted.org/packages/e5/21/795b7549397735e911b032f255cff5fb0de58f96da794274660bca4f58ef/jmespath-0.9.3.tar.gz"
    sha256 "6a81d4c9aa62caf061cb517b4d9ad1dd300374cd4706997aff9cd6aedd61fc64"
  end

  resource "keyring" do
    url "https://files.pythonhosted.org/packages/a0/c9/c08bf10bd057293ff385abaef38e7e548549bbe81e95333157684e75ebc6/keyring-13.2.1.tar.gz"
    sha256 "6364bb8c233f28538df4928576f4e051229e0451651073ab20b315488da16a58"
  end

  resource "more-itertools" do
    url "https://files.pythonhosted.org/packages/c0/2f/6773347277d76c5ade4414a6c3f785ef27e7f5c4b0870ec7e888e66a8d83/more-itertools-4.2.0.tar.gz"
    sha256 "2b6b9893337bfd9166bee6a62c2b0c9fe7735dcf85948b387ec8cba30e85d8e8"
  end

  resource "msrest" do
    url "https://files.pythonhosted.org/packages/d9/48/e636320da2f5ebf2a0786af61f9656ede1448f57b5b8d1a232e313fc5081/msrest-0.5.4.tar.gz"
    sha256 "d609c2997ab66aa8985a6ced972e895cd7aa0a415d715af042a554c5c791934a"
  end

  resource "msrestazure" do
    url "https://files.pythonhosted.org/packages/cd/ce/1381822930cb2e90e889e43831428982577acb9caec5244bcce1c9c542f9/msrestazure-0.4.34.tar.gz"
    sha256 "4fc94a03ecd5b094ab904d929cc5be7a6a80262eab93948260cfe9081a9e6de4"
  end

  resource "oauth2client" do
    url "https://files.pythonhosted.org/packages/50/30/f89a4fc014a03e180840d432e73ffb96da422f2a8094ff3539f0f0c46661/oauth2client-4.1.2.tar.gz"
    sha256 "bd3062c06f8b10c6ef7a890b22c2740e5f87d61b6e1f4b1c90d069cdfc9dadb5"
  end

  resource "oauthlib" do
    url "https://files.pythonhosted.org/packages/df/5f/3f4aae7b28db87ddef18afed3b71921e531ca288dc604eb981e9ec9f8853/oauthlib-2.1.0.tar.gz"
    sha256 "ac35665a61c1685c56336bda97d5eefa246f1202618a1d6f34fccb1bdd404162"
  end

  resource "paramiko" do
    url "https://files.pythonhosted.org/packages/29/65/83181630befb17cd1370a6abb9a87957947a43c2332216e5975353f61d64/paramiko-2.4.1.tar.gz"
    sha256 "33e36775a6c71790ba7692a73f948b329cf9295a72b0102144b031114bd2a4f3"
  end

  resource "passlib" do
    url "https://files.pythonhosted.org/packages/25/4b/6fbfc66aabb3017cd8c3bd97b37f769d7503ead2899bf76e570eb91270de/passlib-1.7.1.tar.gz"
    sha256 "3d948f64138c25633613f303bcc471126eae67c04d5e3f6b7b8ce6242f8653e0"
  end

  resource "pluggy" do
    url "https://files.pythonhosted.org/packages/11/bf/cbeb8cdfaffa9f2ea154a30ae31a9d04a1209312e2919138b4171a1f8199/pluggy-0.6.0.tar.gz"
    sha256 "7f8ae7f5bdf75671a718d2daf0a64b7885f74510bcd98b1a0bb420eb9a9d0cff"
  end

  resource "py" do
    url "https://files.pythonhosted.org/packages/35/77/a0a2a4126cf454e6ac772942898379e2fe78f2b7885df0461a5b8f8a8040/py-1.5.4.tar.gz"
    sha256 "3fd59af7435864e1a243790d322d763925431213b6b8529c6ca71081ace3bbf7"
  end

  resource "pyasn1" do
    url "https://files.pythonhosted.org/packages/10/46/059775dc8e50f722d205452bced4b3cc965d27e8c3389156acd3b1123ae3/pyasn1-0.4.4.tar.gz"
    sha256 "f58f2a3d12fd754aa123e9fa74fb7345333000a035f3921dbdaa08597aa53137"
  end

  resource "pyasn1-modules" do
    url "https://files.pythonhosted.org/packages/37/33/74ebdc52be534e683dc91faf263931bc00ae05c6073909fde53999088541/pyasn1-modules-0.2.2.tar.gz"
    sha256 "a0cf3e1842e7c60fde97cb22d275eb6f9524f5c5250489e292529de841417547"
  end

  resource "pycparser" do
    url "https://files.pythonhosted.org/packages/8c/2d/aad7f16146f4197a11f8e91fb81df177adcc2073d36a17b1491fd09df6ed/pycparser-2.18.tar.gz"
    sha256 "99a8ca03e29851d96616ad0404b4aad7d9ee16f25c9f9708a11faf2810f7b226"
  end

  resource "PyJWT" do
    url "https://files.pythonhosted.org/packages/00/5e/b358c9bb24421e6155799d995b4aa3aa3307ffc7ecae4ad9d29fd7e07a73/PyJWT-1.6.4.tar.gz"
    sha256 "4ee413b357d53fd3fb44704577afac88e72e878716116270d722723d65b42176"
  end

  resource "PyNaCl" do
    url "https://files.pythonhosted.org/packages/08/19/cf56e60efd122fa6d2228118a9b345455b13ffe16a14be81d025b03b261f/PyNaCl-1.2.1.tar.gz"
    sha256 "e0d38fa0a75f65f556fb912f2c6790d1fa29b7dd27a1d9cc5591b281321eaaa9"
  end

  resource "pytest" do
    url "https://files.pythonhosted.org/packages/55/50/399419c03c39bf41faa7cbd5a8976c076037b2d76adf2535610919806d67/pytest-3.6.3.tar.gz"
    sha256 "0453c8676c2bee6feb0434748b068d5510273a916295fd61d306c4f22fbfd752"
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/a0/b0/a4e3241d2dee665fea11baec21389aec6886655cd4db7647ddf96c3fad15/python-dateutil-2.7.3.tar.gz"
    sha256 "e27001de32f627c22380a688bcc43ce83504a7bc5da472209b4c70f02829f0b8"
  end

  resource "python-vagrant" do
    url "https://files.pythonhosted.org/packages/bb/c6/0a6d22ae1782f261fc4274ea9385b85bf792129d7126575ec2a71d8aea18/python-vagrant-0.5.15.tar.gz"
    sha256 "af9a8a9802d382d45dbea96aa3cfbe77c6e6ad65b3fe7b7c799d41ab988179c6"
  end

  resource "PyYAML" do
    url "https://files.pythonhosted.org/packages/a8/c6/a8d1555e795dbd0375c3c93b576ca13bbf139db51ea604afa19a2c35fc03/PyYAML-4.2b4.tar.gz"
    sha256 "3c17fb92c8ba2f525e4b5f7941d850e7a48c3a59b32d331e2502a3cdc6648e76"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/54/1f/782a5734931ddf2e1494e4cd615a51ff98e1879cbe9eecbdfeaf09aa75e9/requests-2.19.1.tar.gz"
    sha256 "ec22d826a36ed72a7358ff3fe56cbd4ba69dd7a6718ffd450ff0e9df7a47ce6a"
  end

  resource "requests-oauthlib" do
    url "https://files.pythonhosted.org/packages/95/be/072464f05b70e4142cb37151e215a2037b08b1400f8a56f2538b76ca6205/requests-oauthlib-1.0.0.tar.gz"
    sha256 "8886bfec5ad7afb391ed5443b1f697c6f4ae98d0e5620839d8b4499c032ada3f"
  end

  resource "retry" do
    url "https://files.pythonhosted.org/packages/9d/72/75d0b85443fbc8d9f38d08d2b1b67cc184ce35280e4a3813cda2f445f3a4/retry-0.9.2.tar.gz"
    sha256 "f8bfa8b99b69c4506d6f5bd3b0aabf77f98cdb17f3c9fc3f5ca820033336fba4"
  end

  resource "retrying" do
    url "https://files.pythonhosted.org/packages/44/ef/beae4b4ef80902f22e3af073397f079c96969c69b2c7d52a57ea9ae61c9d/retrying-1.3.3.tar.gz"
    sha256 "08c039560a6da2fe4f2c426d0766e284d3b736e355f8dd24b37367b0bb41973b"
  end

  resource "rsa" do
    url "https://files.pythonhosted.org/packages/14/89/adf8b72371e37f3ca69c6cb8ab6319d009c4a24b04a31399e5bd77d9bb57/rsa-3.4.2.tar.gz"
    sha256 "25df4e10c263fb88b5ace923dd84bf9aa7f5019687b5e55382ffcdb8bede9db5"
  end

  resource "s3transfer" do
    url "https://files.pythonhosted.org/packages/9a/66/c6a5ae4dbbaf253bd662921b805e4972451a6d214d0dc9fb3300cb642320/s3transfer-0.1.13.tar.gz"
    sha256 "90dc18e028989c609146e241ea153250be451e05ecc0c2832565231dacdf59c1"
  end

  resource "SecretStorage" do
    url "https://files.pythonhosted.org/packages/65/02/1f0d2a7b1221bc9a15f8b8d4de2c8ad8272c4d0af76cbdc72e2cf51d42e0/SecretStorage-3.0.1.tar.gz"
    sha256 "819087ca89c0d6c5711692f41fb26f786af9dcc5bb89d567722a66edfbb2a689"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/16/d8/bc6316cf98419719bd59c91742194c111b6f2e85abac88e496adefaf7afe/six-1.11.0.tar.gz"
    sha256 "70e8a77beed4562e7f14fe23a786b54f6296e34344c23bc42f07b15018ff98e9"
  end

  resource "uritemplate" do
    url "https://files.pythonhosted.org/packages/cd/db/f7b98cdc3f81513fb25d3cbe2501d621882ee81150b745cdd1363278c10a/uritemplate-3.0.0.tar.gz"
    sha256 "c02643cebe23fc8adb5e6becffe201185bf06c40bda5c0b4028a93f1527d011d"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/3c/d2/dc5471622bd200db1cd9319e02e71bc655e9ea27b8e0ce65fc69de0dac15/urllib3-1.23.tar.gz"
    sha256 "a68ac5e15e76e7e5dd2b8f94007233e01effe3e50e8daddf69acfd81cb686baf"
  end

  resource "websocket-client" do
    url "https://files.pythonhosted.org/packages/28/85/df04ec21c622728316b591c2852fd20a0e74324eeb6ca26f351844ba815f/websocket_client-0.48.0.tar.gz"
    sha256 "18f1170e6a1b5463986739d9fd45c4308b0d025c1b2f9b88788d8f69e8a5eb4a"
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
