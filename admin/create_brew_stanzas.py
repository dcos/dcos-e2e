import subprocess

requirements = [
    'click',
    'click-spinner',
    'cryptography',
    'docker',
    'paramiko',
    'passlib',
    'PyYAML',
    'pytest',
    'retry',
    'retrying',
    'requests',
    'scp',
    'urllib3',
]

first = requirements[0]
others = requirements[1:]
command = 'poet ' + first
for requirement in others:
    command += ' --also ' + requirement

print(command)
