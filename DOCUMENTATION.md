# Documentation

## About

The documentation roughly attempts to follow [Diátaxis](https://diataxis.fr/).

## View

As of today, you can [view the moccasin documentation here.](https://cyfrin.github.io/moccasin/)

## Build

To build the documentation, you can do the following.

1. Follow the `Installing for local development` instructions in the [CONTRIBUTING.md](./CONTRIBUTING.md) file.

2. Add dependencies

```bash
uv sync --all-extras
```

3. Build the documentation
   
```bash
just docs
```

4. Open the documentation in your browser of choice.

If using something like VSCode's live server, open:

```bash
http://127.0.0.1:5500/built_docs/html/index.html
```

Or:

```bash
/path/to/your/file/built_docs/html/index.html
```