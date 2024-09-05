> Docs are a work in process.

1. Install the docs dependencies

```bash
rye sync --features docs
```

2. Run the build

```bash
rye run sphinx-build -M html docs/source built_docs
```