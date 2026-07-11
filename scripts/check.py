import os
import subprocess
import sys

CHECK_PATHS = ["src", "tests", "scripts", "etl", "dags", "migrations"]


def main() -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = _append_pythonpath(env.get("PYTHONPATH", ""), "src")

    checks = [
        ("compile", [sys.executable, "-m", "compileall", *CHECK_PATHS]),
        ("lint", [sys.executable, "-m", "ruff", "check", *CHECK_PATHS]),
        ("tests", [sys.executable, "-m", "unittest", "discover"]),
    ]

    for name, command in checks:
        print(f"\n==> Running {name}", flush=True)
        result = subprocess.run(command, env=env, check=False)
        if result.returncode != 0:
            print(f"\n{name} failed with exit code {result.returncode}.", flush=True)
            return result.returncode

    print("\nAll checks passed.", flush=True)
    return 0


def _append_pythonpath(existing: str, path: str) -> str:
    if not existing:
        return path
    return os.pathsep.join([path, existing])


if __name__ == "__main__":
    raise SystemExit(main())
