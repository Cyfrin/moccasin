import subprocess


def test_explorer_fetch_alias_help(mox_path):
    result = subprocess.run(
        [mox_path, "explorer", "get", "-h"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "explorer fetch" in result.stdout
    assert result.returncode == 0


def test_explorer_list_runs(mox_path):
    result = subprocess.run(
        [mox_path, "explorer", "list"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Supported explorers" in result.stderr
    assert result.returncode == 0
