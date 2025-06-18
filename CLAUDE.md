# Notes

- If you want to run a python command like `python -c "from eth_typing import Address; help(Address)"` use `uv run` instead of `python`, ie:

```bash
uv run python -c "from eth_typing import Address; help(Address)"
```