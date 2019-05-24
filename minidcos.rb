class Minidcos < Formula
  include Language::Python::Virtualenv

  url "https://codeload.github.com/dcos/dcos-e2e/legacy.tar.gz/2019.05.24.1"
  head "https://github.com/dcos/dcos-e2e.git"
  homepage "http://minidcos.readthedocs.io/en/latest/"
  depends_on "python3"
  depends_on "pkg-config"

  resource "adal" do
    url "https://files.pythonhosted.org/packages/82/43/a1e4b7368eec9653660ee91f023af36056028cea97e3550f85866a0c3f2f/adal-1.2.1.tar.gz"
    sha256 "b6edd095be66561382bdaa59d40b04490e93149fb3b7fa44c1fa5504eed5b8b9"
  end

  resource "appnope" do
    url "https://files.pythonhosted.org/packages/26/34/0f3a5efac31f27fabce64645f8c609de9d925fe2915304d1a40f544cff0e/appnope-0.1.0.tar.gz"
    sha256 "8b995ffe925347a2138d7ac0fe77155e4311a0ea6d6da4f5128fe4b3cbe5ed71"
  end

  resource "asn1crypto" do
    url "https://files.pythonhosted.org/packages/fc/f1/8db7daa71f414ddabfa056c4ef792e1461ff655c2ae2928a2b675bfed6b4/asn1crypto-0.24.0.tar.gz"
    sha256 "9d5c20441baf0cb60a4ac34cc447c6c189024b6b4c6cd7877034f4965c464e49"
  end

  resource "atomicwrites" do
    url "https://files.pythonhosted.org/packages/ec/0f/cd484ac8820fed363b374af30049adc8fd13065720fd4f4c6be8a2309da7/atomicwrites-1.3.0.tar.gz"
    sha256 "75a9445bac02d8d058d5e1fe689654ba5a6556a1dfd8ce6ec55a0ed79866cfa6"
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

  resource "backcall" do
    url "https://files.pythonhosted.org/packages/84/71/c8ca4f5bb1e08401b916c68003acf0a0655df935d74d93bf3f3364b310e0/backcall-0.1.0.tar.gz"
    sha256 "38ecd85be2c1e78f77fd91700c76e14667dc21e2713b63876c0eb901196e01e4"
  end

  resource "bcrypt" do
    url "https://files.pythonhosted.org/packages/ce/3a/3d540b9f5ee8d92ce757eebacf167b9deedb8e30aedec69a2a072b2399bb/bcrypt-3.1.6.tar.gz"
    sha256 "44636759d222baa62806bbceb20e96f75a015a6381690d1bc2eda91c01ec02ea"
  end

  resource "boto3" do
    url "https://files.pythonhosted.org/packages/6f/5a/0cfdef6f69a32287f11d92fa6054c49b2c98e0e4412a0a9181544d0fd7ef/boto3-1.9.123.tar.gz"
    sha256 "2e527686a72ff5fed8275e897df63fadbdca6d4d47f651d898dee89ba9b9eb4d"
  end

  resource "botocore" do
    url "https://files.pythonhosted.org/packages/c1/88/8811cf71a9a45c1ba4c54e8bccb5c863b905e6765af40354b441b62fb2f6/botocore-1.12.123.tar.gz"
    sha256 "7982ab3b3da1f7f2f23f0a12fbd34fe8efc514b53bbe61b536a61884a51db25c"
  end

  resource "cachetools" do
    url "https://files.pythonhosted.org/packages/ae/37/7fd45996b19200e0cb2027a0b6bef4636951c4ea111bfad36c71287247f6/cachetools-3.1.1.tar.gz"
    sha256 "8ea2d3ce97850f31e4a08b0e2b5e6c34997d7216a9d2c98e0f3978630d4da69a"
  end

  resource "Cerberus" do
    url "https://files.pythonhosted.org/packages/90/31/e30784a1f9a4b46875cfed1c9f806c188e2181e7ba3b568e81e7b0bc5718/Cerberus-1.2.tar.gz"
    sha256 "f5c2e048fb15ecb3c088d192164316093fcfa602a74b3386eefb2983aa7e800a"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/06/b8/d1ea38513c22e8c906275d135818fee16ad8495985956a9b7e2bb21942a1/certifi-2019.3.9.tar.gz"
    sha256 "b26104d6835d1f5e49452a26eb2ff87fe7090b89dfcaee5ea2212697e1e1d7ae"
  end

  resource "cffi" do
    url "https://files.pythonhosted.org/packages/93/1a/ab8c62b5838722f29f3daffcc8d4bd61844aa9b5f437341cc890ceee483b/cffi-1.12.3.tar.gz"
    sha256 "041c81822e9f84b1d9c401182e174996f0bae9991f33725d059b771744290774"
  end

  resource "chardet" do
    url "https://files.pythonhosted.org/packages/fc/bb/a5768c230f9ddb03acc9ef3f0d4a3cf93462473795d18e9535498c8f929d/chardet-3.0.4.tar.gz"
    sha256 "84ab92ed1c4d4f16916e05906b6b75a6c0fb5db821cc65e70cbd64a3e2a5eaae"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/f8/5c/f60e9d8a1e77005f664b76ff8aeaee5bc05d0a91798afd7f53fc998dbc47/Click-7.0.tar.gz"
    sha256 "5b94b49521f6456670fdb30cd82a4eca9412788a93fa6dd6df72c94d5a8ff2d7"
  end

  resource "click-pathlib" do
    url "https://files.pythonhosted.org/packages/c8/8c/cafb4eef88aee325a9e12f9f51be3a203629cc907ab27ac283a52f9eab44/click-pathlib-2019.4.30.2.tar.gz"
    sha256 "a7e82cee61d103f46f588fc9c0421617fe760dc081c2a62f6f8822b1e4a9d8b9"
  end

  resource "colorama" do
    url "https://files.pythonhosted.org/packages/e6/76/257b53926889e2835355d74fec73d82662100135293e17d382e2b74d1669/colorama-0.3.9.tar.gz"
    sha256 "48eb22f4f8461b1df5734a074b57042430fb06e1d61bd1e11b078c0fe6d7a1f1"
  end

  resource "cryptography" do
    url "https://files.pythonhosted.org/packages/07/ca/bc827c5e55918ad223d59d299fff92f3563476c3b00d0a9157d9c0217449/cryptography-2.6.1.tar.gz"
    sha256 "26c821cbeb683facb966045e2064303029d572a87ee69ca5a1bf54bf55f93ca6"
  end

  resource "cursor" do
    url "https://files.pythonhosted.org/packages/23/0d/bec47260080d5e4b1d88a08b31c6c44b476a9c7509e41b1d84967027d32d/cursor-1.2.0.tar.gz"
    sha256 "8ee9fe5b925e1001f6ae6c017e93682583d2b4d1ef7130a26cfcdf1651c0032c"
  end

  resource "decorator" do
    url "https://files.pythonhosted.org/packages/ba/19/1119fe7b1e49b9c8a9f154c930060f37074ea2e8f9f6558efc2eeaa417a2/decorator-4.4.0.tar.gz"
    sha256 "86156361c50488b84a3f148056ea716ca587df2f0de1d34750d35c21312725de"
  end

  resource "docker" do
    url "https://files.pythonhosted.org/packages/4b/79/4206ea568bd0d134cd7cb6022dd60bea06ffdb8b5564288ca428fd3aeb0d/docker-3.7.2.tar.gz"
    sha256 "c456ded5420af5860441219ff8e51cdec531d65f4a9e948ccd4133e063b72f50"
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
    url "https://files.pythonhosted.org/packages/27/e8/607697e6ab8a961fc0b141a97ea4ce72cd9c9e264adeb0669f6d194aa626/entrypoints-0.2.3.tar.gz"
    sha256 "d2d587dde06f99545fb13a383d2cd336a8ff1f359c5839ce3a64c917d10c029f"
  end

  resource "google-api-python-client" do
    url "https://files.pythonhosted.org/packages/7a/84/ffde3c95d4162cdc8bae710fecc6873cccb05ac33afc3b2c925c74cc0150/google-api-python-client-1.7.8.tar.gz"
    sha256 "06907006ed5ce831018f03af3852d739c0b2489cdacfda6971bcc2075c762858"
  end

  resource "google-auth" do
    url "https://files.pythonhosted.org/packages/ef/77/eb1d3288dbe2ba6f4fe50b9bb41770bac514cd2eb91466b56d44a99e2f8d/google-auth-1.6.3.tar.gz"
    sha256 "0f7c6a64927d34c1a474da92cfc59e552a5d3b940d3266606c6a28b72888b9e4"
  end

  resource "google-auth-httplib2" do
    url "https://files.pythonhosted.org/packages/e7/32/ac7f30b742276b4911a1439c5291abab1b797ccfd30bc923c5ad67892b13/google-auth-httplib2-0.0.3.tar.gz"
    sha256 "098fade613c25b4527b2c08fa42d11f3c2037dda8995d86de0745228e965d445"
  end

  resource "httplib2" do
    url "https://files.pythonhosted.org/packages/67/33/29779c5aaeac796679a37bf798b3c2adbfaae7dbf13e966b0ab9c3aa06c0/httplib2-0.12.3.tar.gz"
    sha256 "a18121c7c72a56689efbf1aef990139ad940fee1e64c6f2458831736cd593600"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/ad/13/eb56951b6f7950cadb579ca166e448ba77f9d24efc03edd7e55fa57d04b7/idna-2.8.tar.gz"
    sha256 "c357b3f628cf53ae2c4c05627ecc484553142ca23264e593d327bcde5e9c3407"
  end

  resource "ipython" do
    url "https://files.pythonhosted.org/packages/75/74/9b0ef91c8e356c907bb12297000951acb804583b54eeaddc342c5bad4d96/ipython-7.5.0.tar.gz"
    sha256 "e840810029224b56cd0d9e7719dc3b39cf84d577f8ac686547c8ba7a06eeab26"
  end

  resource "ipython_genutils" do
    url "https://files.pythonhosted.org/packages/e8/69/fbeffffc05236398ebfcfb512b6d2511c622871dca1746361006da310399/ipython_genutils-0.2.0.tar.gz"
    sha256 "eb2e116e75ecef9d4d228fdc66af54269afa26ab4463042e33785b887c628ba8"
  end

  resource "isodate" do
    url "https://files.pythonhosted.org/packages/b1/80/fb8c13a4cd38eb5021dc3741a9e588e4d1de88d895c1910c6fc8a08b7a70/isodate-0.6.0.tar.gz"
    sha256 "2e364a3d5759479cdb2d37cce6b9376ea504db2ff90252a2e5b7cc89cc9ff2d8"
  end

  resource "jedi" do
    url "https://files.pythonhosted.org/packages/96/fb/e99fc0442f8a0fa4bf5d34162c2d98131489017f661bf8a331857844b145/jedi-0.13.3.tar.gz"
    sha256 "2bb0603e3506f708e792c7f4ad8fc2a7a9d9c2d292a358fbbd58da531695595b"
  end

  resource "jeepney" do
    url "https://files.pythonhosted.org/packages/18/17/7dbc70bc13dc9c8ba8c9b25fbc8b75dffb6bc7e56c3d7cecd87e6b563e5f/jeepney-0.3.1.tar.gz"
    sha256 "a6f2aa72e61660248d4d524dfccb6405f17c693b69af5d60dd7f2bab807d907e"
  end

  resource "jmespath" do
    url "https://files.pythonhosted.org/packages/2c/30/f0162d3d83e398c7a3b70c91eef61d409dea205fb4dc2b47d335f429de32/jmespath-0.9.4.tar.gz"
    sha256 "bde2aef6f44302dfb30320115b17d030798de8c4110e28d5cf6cf91a7a31074c"
  end

  resource "keyring" do
    url "https://files.pythonhosted.org/packages/ee/79/744da3470d832b776a37ccf2b277339f165ff75827606b073dd653b26bba/keyring-16.0.2.tar.gz"
    sha256 "95e4f1d0342d0bf5d137d1d2352d59f7abbebb1507bec1ac26831c411ac23150"
  end

  resource "more-itertools" do
    url "https://files.pythonhosted.org/packages/29/ed/3a85eb4afdce6dc33e78dad885e17c678db8055bf65353e0de4944c72a40/more-itertools-7.0.0.tar.gz"
    sha256 "c3e4748ba1aad8dba30a4886b0b1a2004f9a863837b8654e7059eebf727afa5a"
  end

  resource "msrest" do
    url "https://files.pythonhosted.org/packages/0b/ec/437da5296f540830eb7fe0d0d06e4f3f4d97b82ef369b637dec76bf20f3e/msrest-0.6.6.tar.gz"
    sha256 "947e9155fb55bda98340e99c15e4115a268ff69aee0007aaa54b7bf05018029b"
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
    url "https://files.pythonhosted.org/packages/ec/90/882f43232719f2ebfbdbe8b7c57fc9642a25b3df30cb70a3701ea22622de/oauthlib-3.0.1.tar.gz"
    sha256 "0ce32c5d989a1827e3f1148f98b9085ed2370fc939bf524c9c851d8714797298"
  end

  resource "paramiko" do
    url "https://files.pythonhosted.org/packages/a4/57/86681372e7a8d642718cadeef38ead1c24c4a1af21ae852642bf974e37c7/paramiko-2.4.2.tar.gz"
    sha256 "a8975a7df3560c9f1e2b43dc54ebd40fd00a7017392ca5445ce7df409f900fcb"
  end

  resource "parso" do
    url "https://files.pythonhosted.org/packages/79/52/70d0bb8a1f4b1475a603b4b1484bb351edda30846996fc93fe1976948fef/parso-0.4.0.tar.gz"
    sha256 "2e9574cb12e7112a87253e14e2c380ce312060269d04bd018478a3c92ea9a376"
  end

  resource "passlib" do
    url "https://files.pythonhosted.org/packages/25/4b/6fbfc66aabb3017cd8c3bd97b37f769d7503ead2899bf76e570eb91270de/passlib-1.7.1.tar.gz"
    sha256 "3d948f64138c25633613f303bcc471126eae67c04d5e3f6b7b8ce6242f8653e0"
  end

  resource "pexpect" do
    url "https://files.pythonhosted.org/packages/1c/b1/362a0d4235496cb42c33d1d8732b5e2c607b0129ad5fdd76f5a583b9fcb3/pexpect-4.7.0.tar.gz"
    sha256 "9e2c1fd0e6ee3a49b28f95d4b33bc389c89b20af6a1255906e90ff1262ce62eb"
  end

  resource "pickleshare" do
    url "https://files.pythonhosted.org/packages/d8/b6/df3c1c9b616e9c0edbc4fbab6ddd09df9535849c64ba51fcb6531c32d4d8/pickleshare-0.7.5.tar.gz"
    sha256 "87683d47965c1da65cdacaf31c8441d12b8044cdec9aca500cd78fc2c683afca"
  end

  resource "pluggy" do
    url "https://files.pythonhosted.org/packages/0d/a1/862ab336e8128fde20981d2c1aa8506693412daf5083b1911d539412676b/pluggy-0.11.0.tar.gz"
    sha256 "25a1bc1d148c9a640211872b4ff859878d422bccb59c9965e04eed468a0aa180"
  end

  resource "prompt_toolkit" do
    url "https://files.pythonhosted.org/packages/94/a0/57dc47115621d9b3fcc589848cdbcbb6c4c130186e8fc4c4704766a7a699/prompt_toolkit-2.0.9.tar.gz"
    sha256 "2519ad1d8038fd5fc8e770362237ad0364d16a7650fb5724af6997ed5515e3c1"
  end

  resource "ptyprocess" do
    url "https://files.pythonhosted.org/packages/51/83/5d07dc35534640b06f9d9f1a1d2bc2513fb9cc7595a1b0e28ae5477056ce/ptyprocess-0.5.2.tar.gz"
    sha256 "e64193f0047ad603b71f202332ab5527c5e52aa7c8b609704fc28c0dc20c4365"
  end

  resource "py" do
    url "https://files.pythonhosted.org/packages/f1/5a/87ca5909f400a2de1561f1648883af74345fe96349f34f737cdfc94eba8c/py-1.8.0.tar.gz"
    sha256 "dc639b046a6e2cff5bbe40194ad65936d6ba360b52b3c3fe1d08a82dd50b5e53"
  end

  resource "pyasn1" do
    url "https://files.pythonhosted.org/packages/46/60/b7e32f6ff481b8a1f6c8f02b0fd9b693d1c92ddd2efb038ec050d99a7245/pyasn1-0.4.5.tar.gz"
    sha256 "da2420fe13a9452d8ae97a0e478adde1dee153b11ba832a95b223a2ba01c10f7"
  end

  resource "pyasn1-modules" do
    url "https://files.pythonhosted.org/packages/ec/0b/69620cb04a016e4a1e8e352e8a42717862129b574b3479adb2358a1f12f7/pyasn1-modules-0.2.5.tar.gz"
    sha256 "ef721f68f7951fab9b0404d42590f479e30d9005daccb1699b0a51bb4177db96"
  end

  resource "pycparser" do
    url "https://files.pythonhosted.org/packages/68/9e/49196946aee219aead1290e00d1e7fdeab8567783e83e1b9ab5585e6206a/pycparser-2.19.tar.gz"
    sha256 "a988718abfad80b6b157acce7bf130a30876d27603738ac39f140993246b25b3"
  end

  resource "Pygments" do
    url "https://files.pythonhosted.org/packages/1d/55/55cd82a72af652d71eb14f318e2d12d2fd14ded43d6fd105e50ed395198c/Pygments-2.4.0.tar.gz"
    sha256 "31cba6ffb739f099a85e243eff8cb717089fdd3c7300767d9fc34cb8e1b065f5"
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
    url "https://files.pythonhosted.org/packages/e2/1d/5aaae6a77d9699ebcc5cbed574c28272371b8915073a126a9ead961c8f6c/pytest-4.1.1.tar.gz"
    sha256 "c3c573a29d7c9547fb90217ece8a8843aa0c1328a797e200290dc3d0b4b823be"
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
    url "https://files.pythonhosted.org/packages/9f/2c/9417b5c774792634834e730932745bc09a7d36754ca00acf1ccd1ac2594d/PyYAML-5.1.tar.gz"
    sha256 "436bc774ecf7c103814098159fbb84c2715d25980175292c648f2da143909f95"
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
    url "https://files.pythonhosted.org/packages/43/22/37b9aaf3969628a25b3b921612139ebc5b8dc26cabb9873c356e1ad2ce2e/s3transfer-0.2.0.tar.gz"
    sha256 "f23d5cb7d862b104401d9021fc82e5fa0e0cf57b7660a1331425aab0c691d021"
  end

  resource "sarge" do
    url "https://files.pythonhosted.org/packages/c4/2b/deaaacf4af3f9c45c48be04a6a48fec60515fb34dafda9fe61ecd2c5e4cc/sarge-0.1.5.post0.tar.gz"
    sha256 "da8cc90883f8e5ab4af0d746438f608662f5f2a35da2e858517927edefa134b0"
  end

  resource "SecretStorage" do
    url "https://files.pythonhosted.org/packages/17/7a/683ce8d41b0b392199f1f6273a5cc81a0583b886e799786b7add5750817f/SecretStorage-3.1.0.tar.gz"
    sha256 "29aa3cbd36dd5e54ac17d69161f9a150548f4ffba21fa8b5fdd5add854fe7d8b"
  end

  resource "semver" do
    url "https://files.pythonhosted.org/packages/47/13/8ae74584d6dd33a1d640ea27cd656a9f718132e75d759c09377d10d64595/semver-2.8.1.tar.gz"
    sha256 "5b09010a66d9a3837211bb7ae5a20d10ba88f8cb49e92cb139a69ef90d5060d8"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/dd/bf/4138e7bfb757de47d1f4b6994648ec67a51efe58fa907c1e11e350cddfca/six-1.12.0.tar.gz"
    sha256 "d16a0141ec1a18405cd4ce8b4613101da75da0e9a7aec5bdd4fa804d0e0eba73"
  end

  resource "spinners" do
    url "https://files.pythonhosted.org/packages/01/3f/156b7faa2cbadd35a504c9ee852db32e07ff5f106bbf288d49b22b061135/spinners-0.0.23.tar.gz"
    sha256 "f396fea1ee00c0622988d7d2bf2895d26dd6f70850ca2ce94eaca52ca4873560"
  end

  resource "termcolor" do
    url "https://files.pythonhosted.org/packages/8a/48/a76be51647d0eb9f10e2a4511bf3ffb8cc1e6b14e9e4fab46173aa79f981/termcolor-1.1.0.tar.gz"
    sha256 "1d6d69ce66211143803fbc56652b41d73b4a400a2891d7bf7a1cdf4c02de613b"
  end

  resource "timeout-decorator" do
    url "https://files.pythonhosted.org/packages/07/1c/0d9adcb848f1690f3253dcb1c1557b6cf229a93e724977cb83f266cbd0ae/timeout-decorator-0.4.1.tar.gz"
    sha256 "1a5e276e75c1c5acbf3cdbd9b5e45d77e1f8626f93e39bd5115d68119171d3c6"
  end

  resource "tqdm" do
    url "https://files.pythonhosted.org/packages/80/9b/f3036a9a11c250eb51d38acf94d1d7c33a0d4da8a8931bfdf15e12d505b1/tqdm-4.31.1.tar.gz"
    sha256 "e22977e3ebe961f72362f6ddfb9197cc531c9737aaf5f607ef09740c849ecd05"
  end

  resource "traitlets" do
    url "https://files.pythonhosted.org/packages/a5/98/7f5ef2fe9e9e071813aaf9cb91d1a732e0a68b6c44a32b38cb8e14c3f069/traitlets-4.3.2.tar.gz"
    sha256 "9c4bd2d267b7153df9152698efb1050a5d84982d3384a37b2c1f7723ba3e7835"
  end

  resource "uritemplate" do
    url "https://files.pythonhosted.org/packages/cd/db/f7b98cdc3f81513fb25d3cbe2501d621882ee81150b745cdd1363278c10a/uritemplate-3.0.0.tar.gz"
    sha256 "c02643cebe23fc8adb5e6becffe201185bf06c40bda5c0b4028a93f1527d011d"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/fd/fa/b21f4f03176463a6cccdb612a5ff71b927e5224e83483012747c12fc5d62/urllib3-1.24.2.tar.gz"
    sha256 "9a247273df709c4fedb38c711e44292304f73f39ab01beda9f6b9fc375669ac3"
  end

  resource "wcwidth" do
    url "https://files.pythonhosted.org/packages/55/11/e4a2bb08bb450fdbd42cc709dd40de4ed2c472cf0ccb9e64af22279c5495/wcwidth-0.1.7.tar.gz"
    sha256 "3df37372226d6e63e1b1e1eda15c594bca98a22d33a23832a90998faa96bc65e"
  end

  resource "websocket_client" do
    url "https://files.pythonhosted.org/packages/c5/01/8c9c7de6c46f88e70b5a3276c791a2be82ae83d8e0d0cc030525ee2866fd/websocket_client-0.56.0.tar.gz"
    sha256 "1fd5520878b68b84b5748bb30e592b10d0a91529d5383f74f4964e72b297fd3a"
  end


  def install
    # Without this we hit various issues including
    # https://github.com/takluyver/flit/issues/245.
    # All of these issues are caught by CI so it is safe to remove this
    # and then run CI.
    ENV["PIP_USE_PEP517"] = "false"
    virtualenv_install_with_resources
  end

  test do
      system "#{bin}/dcos_docker", "--help"
  end
end
