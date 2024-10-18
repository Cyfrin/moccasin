import pytest


@pytest.mark.staging
def test_staging_test():
    assert 1 == 1


@pytest.mark.staging
@pytest.mark.local
def test_staging_local_test():
    assert 1 == 1


def test_staging_implicit_test():
    assert 1 == 1


@pytest.mark.local
def test_staging_explicit_test():
    assert 1 == 1
