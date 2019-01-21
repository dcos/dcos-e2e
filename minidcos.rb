class Minidcos < Formula
  include Language::Python::Virtualenv

  url "https://codeload.github.com/dcos/dcos-e2e/legacy.tar.gz/2019.01.21.0"
  head "https://github.com/dcos/dcos-e2e.git"
  homepage "http://minidcos.readthedocs.io/en/latest/"
  depends_on "python3"
  depends_on "pkg-config"

  resource "adal" do
    url "https://files.pythonhosted.org/packages/0f/ba/07dbea5f63937c4a9a10946107d72b03354f65a51f9e0602314193fc2bae/adal-1.2.0.tar.gz"
    sha256 "ba52913c38d76b4a4d88eaab41a5763d056ab6d073f106e0605b051ab930f5c1"
  end

  resource "asn1crypto" do
    url "https://files.pythonhosted.org/packages/fc/f1/8db7daa71f414ddabfa056c4ef792e1461ff655c2ae2928a2b675bfed6b4/asn1crypto-0.24.0.tar.gz"
    sha256 "9d5c20441baf0cb60a4ac34cc447c6c189024b6b4c6cd7877034f4965c464e49"
  end

  resource "atomicwrites" do
    url "https://files.pythonhosted.org/packages/ac/ed/a311712ef6b4355035489f665e63e1a73f9eb371929e3c98e5efd451069e/atomicwrites-1.2.1.tar.gz"
    sha256 "ec9ae8adaae229e4f8446952d204a3e4b5fdd2d099f9be3aaf556120135fb3ee"
  end

  resource "attrs" do
    url "https://files.pythonhosted.org/packages/0f/9e/26b1d194aab960063b266170e53c39f73ea0d0d3f5ce23313e0ec8ee9bdf/attrs-18.2.0.tar.gz"
    sha256 "10cbf6e27dbce8c30807caf056c8eb50917e0eaafe86347671b57254006c3e69"
  end

  resource "azure-common" do
    url "https://files.pythonhosted.org/packages/39/ca/2bdd67243ae7a45281acbbfc139db273868e99fc219e46724dac68094e69/azure-common-1.1.16.zip"
    sha256 "2606ae77ff81c0036965b92ec2efe03eaec02a66714140ca0f7aa401b8b9bbb0"
  end

  resource "azure-datalake-store" do
    url "https://files.pythonhosted.org/packages/ef/a5/e81e99ebc25eae9bfabcd5ceff28c4f0ca136c0c3d914a53a8012441d3b8/azure-datalake-store-0.0.40.tar.gz"
    sha256 "c43f291ab17fc57b68c44adfb597f73255854c2fc57c2c808d146cb175db9519"
  end

  resource "azure-mgmt-network" do
    url "https://files.pythonhosted.org/packages/eb/4b/bae36713bb209ac647f030e19b0b81147c18290cc42405655c0e9582a52b/azure-mgmt-network-2.2.1.zip"
    sha256 "a4327bccc435ca4f829ac18f82f17923b490958c202af7a86044ccabeaaa5401"
  end

  resource "azure-mgmt-nspkg" do
    url "https://files.pythonhosted.org/packages/c4/d4/a9a140ee15abd8b0a542c0d31b7212acf173582c10323b09380c79a1178b/azure-mgmt-nspkg-3.0.2.zip"
    sha256 "8b2287f671529505b296005e6de9150b074344c2c7d1c805b3f053d081d58c52"
  end

  resource "azure-mgmt-resource" do
    url "https://files.pythonhosted.org/packages/48/31/5996d2af3e32cf6ccc3f44da401ae397e6302b08d7ef7d8736191a8bfe61/azure-mgmt-resource-2.0.0.zip"
    sha256 "2e83289369be88d0f06792118db5a7d4ed7150f956aaae64c528808da5518d7f"
  end

  resource "azure-monitor" do
    url "https://files.pythonhosted.org/packages/f5/b1/cd88adb77b15f99d549857827bd3cce59cbf95dc7b46cfad02290ec713db/azure-monitor-0.3.1.zip"
    sha256 "1935f4caf3e58df865121139747f4069490ccbb6acb5ea9b6f4d4b98e7355c56"
  end

  resource "azure-nspkg" do
    url "https://files.pythonhosted.org/packages/39/31/b24f494eca22e0389ac2e81b1b734453f187b69c95f039aa202f6f798b84/azure-nspkg-3.0.2.zip"
    sha256 "e7d3cea6af63e667d87ba1ca4f8cd7cb4dfca678e4c55fc1cedb320760e39dd0"
  end

  resource "bcrypt" do
    url "https://files.pythonhosted.org/packages/ce/3a/3d540b9f5ee8d92ce757eebacf167b9deedb8e30aedec69a2a072b2399bb/bcrypt-3.1.6.tar.gz"
    sha256 "44636759d222baa62806bbceb20e96f75a015a6381690d1bc2eda91c01ec02ea"
  end

  resource "boto3" do
    url "https://files.pythonhosted.org/packages/ce/fd/10e1e6b10f688ab7bb583dd2adf532e8de0332ba98728d95eb956d2bdaaa/boto3-1.9.76.tar.gz"
    sha256 "9d2e79eb36486c8ea1979b966c1993a948765466237bf8b8035e1a191d2fbdc4"
  end

  resource "botocore" do
    url "https://files.pythonhosted.org/packages/a4/3c/7024ae28a82007c30a0390c98614fd2de3da61824b284edd8ee74a4f5311/botocore-1.12.76.tar.gz"
    sha256 "3dea3109b7b9c6aaed1f0c6dcb718f41e8b95c1137fbf01644c789fedcfd19cb"
  end

  resource "cachetools" do
    url "https://files.pythonhosted.org/packages/e6/28/7cde8e73835ff48b4f35b2d93a509575f7bc02b7d614ada71b820c8d9233/cachetools-3.0.0.tar.gz"
    sha256 "4621965b0d9d4c82a79a29edbad19946f5e7702df4afae7d1ed2df951559a8cc"
  end

  resource "Cerberus" do
    url "https://files.pythonhosted.org/packages/90/31/e30784a1f9a4b46875cfed1c9f806c188e2181e7ba3b568e81e7b0bc5718/Cerberus-1.2.tar.gz"
    sha256 "f5c2e048fb15ecb3c088d192164316093fcfa602a74b3386eefb2983aa7e800a"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/55/54/3ce77783acba5979ce16674fc98b1920d00b01d337cfaaf5db22543505ed/certifi-2018.11.29.tar.gz"
    sha256 "47f9c83ef4c0c621eaef743f133f09fa8a74a9b75f037e8624f83bd1b6626cb7"
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
    url "https://files.pythonhosted.org/packages/f8/5c/f60e9d8a1e77005f664b76ff8aeaee5bc05d0a91798afd7f53fc998dbc47/Click-7.0.tar.gz"
    sha256 "5b94b49521f6456670fdb30cd82a4eca9412788a93fa6dd6df72c94d5a8ff2d7"
  end

  resource "click-spinner" do
    url "https://files.pythonhosted.org/packages/4d/c4/e4cc6595266021b549f774a20329188e68b63f06896eba94c1c952027c6e/click-spinner-0.1.8.tar.gz"
    sha256 "67b5af5e825faf82a4fc6cda77c58359abe716fb1c9bc12cc7bea9a0cae1fc8e"
  end

  resource "cryptography" do
    url "https://files.pythonhosted.org/packages/f3/39/d3904df7c56f8654691c4ae1bdb270c1c9220d6da79bd3b1fbad91afd0e1/cryptography-2.4.2.tar.gz"
    sha256 "05a6052c6a9f17ff78ba78f8e6eb1d777d25db3b763343a1ae89a7a8670386dd"
  end

  resource "decorator" do
    url "https://files.pythonhosted.org/packages/6f/24/15a229626c775aae5806312f6bf1e2a73785be3402c0acdec5dbddd8c11e/decorator-4.3.0.tar.gz"
    sha256 "c39efa13fbdeb4506c476c9b3babf6a718da943dab7811c206005a4a956c080c"
  end

  resource "docker" do
    url "https://files.pythonhosted.org/packages/cc/9c/50ec68951d10fc341b650a2f5a6ed3925f7e4adc245113acfe64eb61f46a/docker-3.6.0.tar.gz"
    sha256 "145c673f531df772a957bd1ebc49fc5a366bcd55efa0e64bbd029f5cc7a1fd8e"
  end

  resource "docker-pycreds" do
    url "https://files.pythonhosted.org/packages/c5/e6/d1f6c00b7221e2d7c4b470132c931325c8b22c51ca62417e300f5ce16009/docker-pycreds-0.4.0.tar.gz"
    sha256 "6ce3270bcaf404cc4c3e27e4b6c70d3521deae82fb508767870fdbf772d584d4"
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
    url "https://files.pythonhosted.org/packages/b4/ef/063484f1f9ba3081e920ec9972c96664e2edb9fdc3d8669b0e3b8fc0ad7c/entrypoints-0.3.tar.gz"
    sha256 "c70dd71abe5a8c85e55e12c19bd91ccfeec11a6e99044204511f9ed547d48451"
  end

  resource "google-api-python-client" do
    url "https://files.pythonhosted.org/packages/e0/91/0e6a42ea3e0898a75d819a9690c8c8d0eecd31275d8a85503c8fc33949f2/google-api-python-client-1.7.7.tar.gz"
    sha256 "9106e7d09d80f59a9472a91edd85c2d6ad420aef28c9440ce1691b4a19ba9ada"
  end

  resource "google-auth" do
    url "https://files.pythonhosted.org/packages/5f/8a/b75ec006bf703c96920ce9ba3e97ac9c6eb48772af689576808fc68ac04f/google-auth-1.6.2.tar.gz"
    sha256 "e8d64e9bc8cb6f0fc5360c693f86dc9ee6964081ee702e3b5ddc937f99efc950"
  end

  resource "google-auth-httplib2" do
    url "https://files.pythonhosted.org/packages/e7/32/ac7f30b742276b4911a1439c5291abab1b797ccfd30bc923c5ad67892b13/google-auth-httplib2-0.0.3.tar.gz"
    sha256 "098fade613c25b4527b2c08fa42d11f3c2037dda8995d86de0745228e965d445"
  end

  resource "httplib2" do
    url "https://files.pythonhosted.org/packages/ce/ed/803905d670b52fa0edfdd135337e545b4496c2ab3a222f1449b7256eb99f/httplib2-0.12.0.tar.gz"
    sha256 "f61fb838a94ce3b349aa32c92fd8430f7e3511afdb18bf9640d647e30c90a6d6"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/ad/13/eb56951b6f7950cadb579ca166e448ba77f9d24efc03edd7e55fa57d04b7/idna-2.8.tar.gz"
    sha256 "c357b3f628cf53ae2c4c05627ecc484553142ca23264e593d327bcde5e9c3407"
  end

  resource "isodate" do
    url "https://files.pythonhosted.org/packages/b1/80/fb8c13a4cd38eb5021dc3741a9e588e4d1de88d895c1910c6fc8a08b7a70/isodate-0.6.0.tar.gz"
    sha256 "2e364a3d5759479cdb2d37cce6b9376ea504db2ff90252a2e5b7cc89cc9ff2d8"
  end

  resource "jeepney" do
    url "https://files.pythonhosted.org/packages/16/1d/74adf3b164a8d19a60d0fcf706a751ffa2a1eaa8e5bbb1b6705c92a05263/jeepney-0.4.tar.gz"
    sha256 "6089412a5de162c04747f0220f6b2223b8ba660acd041e52a76426ca550e3c70"
  end

  resource "jmespath" do
    url "https://files.pythonhosted.org/packages/e5/21/795b7549397735e911b032f255cff5fb0de58f96da794274660bca4f58ef/jmespath-0.9.3.tar.gz"
    sha256 "6a81d4c9aa62caf061cb517b4d9ad1dd300374cd4706997aff9cd6aedd61fc64"
  end

  resource "keyring" do
    url "https://files.pythonhosted.org/packages/ee/79/744da3470d832b776a37ccf2b277339f165ff75827606b073dd653b26bba/keyring-16.0.2.tar.gz"
    sha256 "95e4f1d0342d0bf5d137d1d2352d59f7abbebb1507bec1ac26831c411ac23150"
  end

  resource "more-itertools" do
    url "https://files.pythonhosted.org/packages/dd/26/30fc0d541d9fdf55faf5ba4b0fd68f81d5bd2447579224820ad525934178/more-itertools-5.0.0.tar.gz"
    sha256 "38a936c0a6d98a38bcc2d03fdaaedaba9f412879461dd2ceff8d37564d6522e4"
  end

  resource "msrest" do
    url "https://files.pythonhosted.org/packages/71/4f/408da7e619c348782762d88f96d664086a97f6f2f70804367f3ca5e7d589/msrest-0.6.4.tar.gz"
    sha256 "5dadd54bec98d52cd9f43fb095015c346135b8cafaa35f24c7309cc25d3ad266"
  end

  resource "msrestazure" do
    url "https://files.pythonhosted.org/packages/cd/ce/1381822930cb2e90e889e43831428982577acb9caec5244bcce1c9c542f9/msrestazure-0.4.34.tar.gz"
    sha256 "4fc94a03ecd5b094ab904d929cc5be7a6a80262eab93948260cfe9081a9e6de4"
  end

  resource "oauth2client" do
    url "https://files.pythonhosted.org/packages/a6/7b/17244b1083e8e604bf154cf9b716aecd6388acd656dd01893d0d244c94d9/oauth2client-4.1.3.tar.gz"
    sha256 "d486741e451287f69568a4d26d70d9acd73a2bbfa275746c535b4209891cccc6"
  end

  resource "oauthlib" do
    url "https://files.pythonhosted.org/packages/a2/c8/fcb769d478397c92fbd922369a58b9356fa7c4e8ab024d133090bdb9e025/oauthlib-3.0.0.tar.gz"
    sha256 "0a8b2e0daa7afb62bd1b0b387b7a3723fa9a35d1183694ca5a5c8e3d6df59913"
  end

  resource "paramiko" do
    url "https://files.pythonhosted.org/packages/a4/57/86681372e7a8d642718cadeef38ead1c24c4a1af21ae852642bf974e37c7/paramiko-2.4.2.tar.gz"
    sha256 "a8975a7df3560c9f1e2b43dc54ebd40fd00a7017392ca5445ce7df409f900fcb"
  end

  resource "passlib" do
    url "https://files.pythonhosted.org/packages/25/4b/6fbfc66aabb3017cd8c3bd97b37f769d7503ead2899bf76e570eb91270de/passlib-1.7.1.tar.gz"
    sha256 "3d948f64138c25633613f303bcc471126eae67c04d5e3f6b7b8ce6242f8653e0"
  end

  resource "pluggy" do
    url "https://files.pythonhosted.org/packages/38/e1/83b10c17688af7b2998fa5342fec58ecbd2a5a7499f31e606ae6640b71ac/pluggy-0.8.1.tar.gz"
    sha256 "8ddc32f03971bfdf900a81961a48ccf2fb677cf7715108f85295c67405798616"
  end

  resource "py" do
    url "https://files.pythonhosted.org/packages/c7/fa/eb6dd513d9eb13436e110aaeef9a1703437a8efa466ce6bb2ff1d9217ac7/py-1.7.0.tar.gz"
    sha256 "bf92637198836372b520efcba9e020c330123be8ce527e535d185ed4b6f45694"
  end

  resource "pyasn1" do
    url "https://files.pythonhosted.org/packages/46/60/b7e32f6ff481b8a1f6c8f02b0fd9b693d1c92ddd2efb038ec050d99a7245/pyasn1-0.4.5.tar.gz"
    sha256 "da2420fe13a9452d8ae97a0e478adde1dee153b11ba832a95b223a2ba01c10f7"
  end

  resource "pyasn1-modules" do
    url "https://files.pythonhosted.org/packages/c8/0e/3fe59edc782faf8b429f4a1db734418d0f68a7e50f43095747c08330e952/pyasn1-modules-0.2.3.tar.gz"
    sha256 "d14fcb29dabecba3d7b360bf72327c26c385248a5d603cf6be5f566ce999b261"
  end

  resource "pycparser" do
    url "https://files.pythonhosted.org/packages/68/9e/49196946aee219aead1290e00d1e7fdeab8567783e83e1b9ab5585e6206a/pycparser-2.19.tar.gz"
    sha256 "a988718abfad80b6b157acce7bf130a30876d27603738ac39f140993246b25b3"
  end

  resource "PyJWT" do
    url "https://files.pythonhosted.org/packages/2f/38/ff37a24c0243c5f45f5798bd120c0f873eeed073994133c084e1cf13b95c/PyJWT-1.7.1.tar.gz"
    sha256 "8d59a976fb773f3e6a39c85636357c4f0e242707394cadadd9814f5cbaa20e96"
  end

  resource "PyNaCl" do
    url "https://files.pythonhosted.org/packages/61/ab/2ac6dea8489fa713e2b4c6c5b549cc962dd4a842b5998d9e80cf8440b7cd/PyNaCl-1.3.0.tar.gz"
    sha256 "0c6100edd16fefd1557da078c7a31e7b7d7a52ce39fdca2bec29d4f7b6e7600c"
  end

  resource "pytest" do
    url "https://files.pythonhosted.org/packages/77/ae/06047559c82066b16eb57094da60f5e0c6c7a09e2e951c9fc44761e1d9e5/pytest-4.1.0.tar.gz"
    sha256 "5924060b374f62608a078494b909d341720a050b5224ff87e17e12377486a71d"
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/0e/01/68747933e8d12263d41ce08119620d9a7e5eb72c876a3442257f74490da0/python-dateutil-2.7.5.tar.gz"
    sha256 "88f9287c0174266bb0d8cedd395cfba9c58e87e5ad86b2ce58859bc11be3cf02"
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
    url "https://files.pythonhosted.org/packages/52/2c/514e4ac25da2b08ca5a464c50463682126385c4272c18193876e91f4bc38/requests-2.21.0.tar.gz"
    sha256 "502a824f31acdacb3a35b6690b5fbf0bc41d63a24a45c4004352b0242707598e"
  end

  resource "requests-oauthlib" do
    url "https://files.pythonhosted.org/packages/de/a2/f55312dfe2f7a344d0d4044fdfae12ac8a24169dc668bd55f72b27090c32/requests-oauthlib-1.2.0.tar.gz"
    sha256 "bd6533330e8748e94bf0b214775fed487d309b8b8fe823dc45641ebcd9a32f57"
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
    url "https://files.pythonhosted.org/packages/cb/d0/8f99b91432a60ca4b1cd478fd0bdf28c1901c58e3a9f14f4ba3dba86b57f/rsa-4.0.tar.gz"
    sha256 "1a836406405730121ae9823e19c6e806c62bbad73f890574fff50efa4122c487"
  end

  resource "s3transfer" do
    url "https://files.pythonhosted.org/packages/9a/66/c6a5ae4dbbaf253bd662921b805e4972451a6d214d0dc9fb3300cb642320/s3transfer-0.1.13.tar.gz"
    sha256 "90dc18e028989c609146e241ea153250be451e05ecc0c2832565231dacdf59c1"
  end

  resource "SecretStorage" do
    url "https://files.pythonhosted.org/packages/17/7a/683ce8d41b0b392199f1f6273a5cc81a0583b886e799786b7add5750817f/SecretStorage-3.1.0.tar.gz"
    sha256 "29aa3cbd36dd5e54ac17d69161f9a150548f4ffba21fa8b5fdd5add854fe7d8b"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/dd/bf/4138e7bfb757de47d1f4b6994648ec67a51efe58fa907c1e11e350cddfca/six-1.12.0.tar.gz"
    sha256 "d16a0141ec1a18405cd4ce8b4613101da75da0e9a7aec5bdd4fa804d0e0eba73"
  end

  resource "timeout-decorator" do
    url "https://files.pythonhosted.org/packages/07/1c/0d9adcb848f1690f3253dcb1c1557b6cf229a93e724977cb83f266cbd0ae/timeout-decorator-0.4.1.tar.gz"
    sha256 "1a5e276e75c1c5acbf3cdbd9b5e45d77e1f8626f93e39bd5115d68119171d3c6"
  end

  resource "tqdm" do
    url "https://files.pythonhosted.org/packages/f3/75/1072640a8ef9eb6cd338215800f0f3c6eb8150c0733aec47b57363d356d1/tqdm-4.29.0.tar.gz"
    sha256 "79420109a762f82e20e8ecdc3b3bc1bc6c6536884a8de5fa86a50eb99386376a"
  end

  resource "uritemplate" do
    url "https://files.pythonhosted.org/packages/cd/db/f7b98cdc3f81513fb25d3cbe2501d621882ee81150b745cdd1363278c10a/uritemplate-3.0.0.tar.gz"
    sha256 "c02643cebe23fc8adb5e6becffe201185bf06c40bda5c0b4028a93f1527d011d"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/b1/53/37d82ab391393565f2f831b8eedbffd57db5a718216f82f1a8b4d381a1c1/urllib3-1.24.1.tar.gz"
    sha256 "de9529817c93f27c8ccbfead6985011db27bd0ddfcdb2d86f3f663385c6a9c22"
  end

  resource "websocket-client" do
    url "https://files.pythonhosted.org/packages/35/d4/14e446a82bc9172d088ebd81c0b02c5ca8481bfeecb13c9ef07998f9249b/websocket_client-0.54.0.tar.gz"
    sha256 "e51562c91ddb8148e791f0155fdb01325d99bb52c4cdbb291aee7a3563fd0849"
  end


  def install
    virtualenv_install_with_resources
  end

  test do
      system "#{bin}/dcos_docker", "--help"
  end
end
