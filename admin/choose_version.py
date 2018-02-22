"""
Switch to a release branch for the next version of DC/OS E2E.
"""

import datetime

from dulwich.porcelain import tag_list
from dulwich.repo import Repo


def get_version() -> str:
    """
    Returns the next version of DC/OS E2E.
    This is today’s date in the format ``YYYY.MM.DD.MICRO``.
    ``MICRO`` refers to the number of releases created on this date, starting
    from ``0``.
    """
    utc_now = datetime.datetime.utcnow()
    date_format = '%Y.%m.%d'
    date_str = utc_now.strftime(date_format)
    repo = Repo('.')
    tag_labels = tag_list(repo)
    tag_labels = [item.decode() for item in tag_labels]
    today_tag_labels = [
        item for item in tag_labels if item.startswith(date_str)
    ]
    micro = int(len(today_tag_labels))
    return '{date}.{micro}'.format(date=date_str, micro=micro)


def checkout_new_branch(name: str) - None:
    """
    Checks out a new branch given a branch name.
    """
    pass


def main():
    version_str = get_version()
    branch_name = 'release-' + version_str
    checkout_new_branch(name=branch_name)


if __name__ == '__main__':
    main()
