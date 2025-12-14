#!/usr/bin/env python3
"""
Test runner script for the Aurora Archive project.
"""
import subprocess
import sys
from pathlib import Path

def run_tests(test_path=None, verbose=True):
    """Run the test suite using pytest."""
    try:
        # Base command
        cmd = ["uv", "run", "pytest"]

        # Add verbosity
        if verbose:
            cmd.append("-v")

        # Add specific test path if provided
        if test_path:
            cmd.append(test_path)
        else:
            cmd.append("src/test")

        # Add current directory to PYTHONPATH
        import os
        env = {"PYTHONPATH": "src", **os.environ}

        # Run pytest
        result = subprocess.run(cmd, env=env)
        return result.returncode

    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run tests for Aurora Archive")
    parser.add_argument(
        "test_path",
        nargs="?",
        help="Specific test file or directory to run"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_false",
        dest="verbose",
        help="Run tests in quiet mode"
    )

    args = parser.parse_args()

    print("🧪 Running Aurora Archive Tests...")
    print(f"{'=' * 50}")

    exit_code = run_tests(args.test_path, args.verbose)

    if exit_code == 0:
        print(f"{'=' * 50}")
        print("✅ All tests passed!")
    else:
        print(f"{'=' * 50}")
        print("❌ Some tests failed!")

    sys.exit(exit_code)

if __name__ == "__main__":
    main()