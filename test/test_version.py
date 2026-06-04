import re

import powerguess


def test_version():
    assert re.match(r"^\d+\.\d+\.\d+(a\d+)?$", powerguess.__version__)
