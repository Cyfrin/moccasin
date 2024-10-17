import pytest


# TODO: Add a new pytest mark for staging tests, they should:
# 1. Run when you're running on a live network (not forked or local)
# 2. Any test that doesn't have this mark is skipped
@pytest.mark.staging
def test_staging_test():
    pass
