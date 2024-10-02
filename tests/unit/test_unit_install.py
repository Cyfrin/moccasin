from moccasin._dependency_utils import (
    DependencyType,
    classify_dependency,
    preprocess_requirement,
)


def test_classify_dependency_pip():
    dep = "snekmate"
    assert classify_dependency(dep) == DependencyType.PIP


def test_classify_dependency_pip_version():
    dep = "snekmate==0.1.0"
    assert classify_dependency(dep) == DependencyType.PIP


def test_classify_dependency_pip_long():
    dep = '"git+https://github.com/pcaversaccio/snekmate.git"'
    assert classify_dependency(dep) == DependencyType.PIP


def test_classify_dependency_git():
    dep = "pcaversaccio/snekmate"
    assert classify_dependency(dep) == DependencyType.GITHUB


def test_classify_dependency_git_version():
    dep = "pcaversaccio/snekmate@0.1.0"
    assert classify_dependency(dep) == DependencyType.GITHUB


def test_classify_dependency_git_no_git():
    dep = "https://github.com/pcaversaccio/snekmate"
    assert classify_dependency(dep) == DependencyType.GITHUB


def test_preprocess_requirement():
    req = '"git+https://github.com/pcaversaccio/snekmate.git"'
    assert preprocess_requirement(req) == "snekmate"
