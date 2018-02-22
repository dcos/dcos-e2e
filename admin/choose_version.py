"""
Print a version string for the next version of DC/OS E2E.
"""

import datetime

def get_version():
    utc_now = datetime.datetime.utcnow()
    date_format = '%Y.%m.%d'
    date_str = utc_now.strftime(date_format)
    micro = 1
    return '{date}.{micro}'.format(date=date_str, micro=micro)

if __name__ == '__main__':
    print(get_version())
