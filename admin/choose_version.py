"""
Print a version string for the next version of DC/OS E2E.
"""

import datetime

from dulwich.repo import Repo
from dulwich.porcelain import tag_list

def get_version():
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

if __name__ == '__main__':
    print(get_version())
