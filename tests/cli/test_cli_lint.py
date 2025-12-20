import subprocess


def test_lint_help(mox_path):
    """Test lint command help output."""
    result = subprocess.run(
        [mox_path, "lint", "--help"], check=True, capture_output=True, text=True
    )
    assert "usage: natrix" in result.stdout
    assert result.returncode == 0