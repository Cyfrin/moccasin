import sys

from moccasin import __main__


def main():
    __main__.main(sys.argv[1:])


def version() -> str:
    return __main__.get_version()


if __name__ == "__main__":
    main()
