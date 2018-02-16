import subprocess
from pathlib import Path
from typing import List


def get_requirements(requirements_file: Path) -> List[str]:
    requirements_file = requirements_file.read_text().strip().split('\n')
    return [line for line in requirements_file if not line.startswith('#')]

def get_resource_stanzas(requirements: List[str]):
    first = requirements[0]

    args = ['poet', first]
    for requirement in requirements[1:]:
        args.append('--also')
        args.append(requirement)

    result = subprocess.run(args=args, stdout=subprocess.PIPE)
    return result.stdout


def  get_formula(resource_stanzas: str):
    import pdb; pdb.set_trace()
    return (
        ''
        '{resource_stanzas}'
        ''
    ).format(resource_stanzas=resource_stanzas)

if __name__ == '__main__':
    requirements_file = Path(__file__).parent.parent / 'requirements.txt'
    requirements = get_requirements(requirements_file=requirements_file)
    resource_stanzas = get_resource_stanzas(requirements=requirements)
    formula = get_formula(resource_stanzas=resource_stanzas)
    print(formula)
