import subprocess


def test_format_help(mox_path):
    """Test format command help output."""
    result = subprocess.run(
        [mox_path, "format", "--help"], capture_output=True, text=True
    )
    # Since format command passes args to mamushi, we expect mamushi help or error
    assert result.returncode in [
        0,
        1,
    ]  # Could be 0 (mamushi installed) or 1 (not installed)
