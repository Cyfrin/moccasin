from moccasin.commands.install import (
    DependencyType,
    classify_dependency,
    extract_org_and_package,
)


def test_classify_dependency_pip():
    dep = "snekmate"
    assert classify_dependency(dep) == DependencyType.PIP


def test_classify_dependency_pip_version():
    dep = "snekmate==0.1.0"
    assert classify_dependency(dep) == DependencyType.PIP


def test_classify_dependency_git():
    dep = "pcaversaccio/snekmate"
    assert classify_dependency(dep) == DependencyType.GITHUB


def test_classify_dependency_git_version():
    dep = "pcaversaccio/snekmate@0.1.0"
    assert classify_dependency(dep) == DependencyType.GITHUB


def test_classify_dependency_git_long():
    dep = '"git+https://github.com/pcaversaccio/snekmate.git"'
    assert classify_dependency(dep) == DependencyType.GITHUB


def test_classify_dependency_git_no_git():
    dep = "https://github.com/pcaversaccio/snekmate"
    assert classify_dependency(dep) == DependencyType.GITHUB


def test_extra_from_github():
    dep = '"git+https://github.com/pcaversaccio/snekmate.git"'
    org, package = extract_org_and_package(dep)
    assert org == "pcaversaccio"
    assert package == "snekmate"


def test_extra_from_github_shorthand():
    dep = "pcaversaccio/snekmate"
    org, package = extract_org_and_package(dep)
    assert org == "pcaversaccio"
    assert package == "snekmate"


def test_extra_from_github_version():
    dep = "pcaversaccio/snekmate@0.1.0"
    org, package = extract_org_and_package(dep)
    assert org == "pcaversaccio"
    assert package == "snekmate"


def test_extra_from_github_no_git():
    dep = "https://github.com/pcaversaccio/snekmate"
    org, package = extract_org_and_package(dep)
    assert org == "pcaversaccio"
    assert package == "snekmate"
