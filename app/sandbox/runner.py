"""What runs inside the sealed box."""

import sys


def main() -> int:
    code = sys.stdin.read()
    scope = {"__name__": "__main__", "__file__": "<generated>"}
    exec(compile(code, "<generated>", "exec"), scope)
    return 0


if __name__ == "__main__":
    sys.exit(main())
