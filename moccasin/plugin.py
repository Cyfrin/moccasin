import pytest

from moccasin.config import get_or_initialize_config


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "staging: mark test to run on a live or staging environment, and all other tests to be skipped",
    )
    config.addinivalue_line(
        "markers",
        "local: mark test to run in a local or forked environment, all tests are implicitly marked as this",
    )
    config.addinivalue_line("markers", "local: all tests are implicitly marked as ")


def pytest_collection_modifyitems(config, items):
    moccasin_config = get_or_initialize_config()
    active_network = moccasin_config.get_active_network()
    if active_network.live_or_staging:
        skip_non_staging = pytest.mark.skip(reason="Not a staging test")
        for item in items:
            if "staging" not in item.keywords:
                item.add_marker(skip_non_staging)
    else:
        skip_staging = pytest.mark.skip(reason="Not running on a live network")
        for item in items:
            if "staging" in item.keywords and "local" not in item.keywords:
                item.add_marker(skip_staging)
