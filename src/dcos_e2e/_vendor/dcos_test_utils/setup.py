from setuptools import setup

setup(
    name='dcos-test-utils',
    version='0.1',
    description='Backend for the dcos_api_session object used as a test harness in the DC/OS integration tests',
    url='https://dcos.io',
    author='Mesosphere, Inc.',
    author_email='help@dcos.io',
    license='apache2',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    packages=['dcos_test_utils'],
    install_requires=[
        'py',
        'pytest',
        'requests',
        'retrying'],
)
