"Script for check quality operations."

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(command: List[str], description: str) -> Tuple[(bool, str)]:
    "Run Command operation."
    print(f"Running {description}...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"✅ {description} passed")
            return (True, result.stdout)
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return (False, result.stderr)
    except FileNotFoundError:
        print(f"⚠️  {description} skipped - command not found")
        return (True, "Command not found")


def check_formatting() -> bool:
    "Check Formatting operation."
    (success, _) = run_command(
        ["black", "--check", "app", "tests"], "Code formatting (black)"
    )
    return success


def check_imports() -> bool:
    "Check Imports operation."
    (success, _) = run_command(
        ["isort", "--check-only", "app", "tests"], "Import sorting (isort)"
    )
    return success


def check_linting() -> bool:
    "Check Linting operation."
    (success, _) = run_command(
        ["flake8", "app", "tests", "--max-line-length=88", "--extend-ignore=E203,W503"],
        "Code linting (flake8)",
    )
    return success


def check_types() -> bool:
    "Check Types operation."
    (success, _) = run_command(
        ["mypy", "app", "--ignore-missing-imports", "--no-strict-optional"],
        "Type checking (mypy)",
    )
    return success


def check_security() -> bool:
    "Check Security operation."
    (success, _) = run_command(
        ["bandit", "-r", "app", "-x", "tests"], "Security check (bandit)"
    )
    return success


def run_tests() -> bool:
    "Run Tests operation."
    (success, _) = run_command(
        ["pytest", "tests/", "-v", "--tb=short"], "Test suite (pytest)"
    )
    return success


def run_tests_with_coverage() -> bool:
    "Run Tests With Coverage operation."
    (success, _) = run_command(
        [
            "pytest",
            "tests/",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html",
        ],
        "Test coverage (pytest-cov)",
    )
    if success:
        print("📊 Coverage report generated in htmlcov/index.html")
    return success


def fix_formatting() -> bool:
    "Fix Formatting operation."
    print("🔧 Fixing code formatting...")
    (black_success, _) = run_command(["black", "app", "tests"], "Black formatting")
    (isort_success, _) = run_command(["isort", "app", "tests"], "Import sorting")
    return black_success and isort_success


def main():
    "Main entry point."
    parser = argparse.ArgumentParser(description="Run code quality checks")
    parser.add_argument(
        "--fix", action="store_true", help="Fix formatting issues automatically"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage report"
    )
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument(
        "--security-only", action="store_true", help="Run only security checks"
    )
    args = parser.parse_args()
    if not Path("app").exists():
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    print("🔍 Starting code quality checks for AI Chatbot Platform")
    print(("=" * 60))
    all_passed = True
    if args.fix:
        if not fix_formatting():
            all_passed = False
        print(("=" * 60))
    if args.security_only:
        if not check_security():
            all_passed = False
    else:
        checks = [
            check_formatting,
            check_imports,
            check_linting,
            check_types,
            check_security,
        ]
        if not args.skip_tests:
            if args.coverage:
                checks.append(run_tests_with_coverage)
            else:
                checks.append(run_tests)
        for check in checks:
            if not check():
                all_passed = False
            print(("-" * 40))
    print(("=" * 60))
    if all_passed:
        print("🎉 All checks passed! Code quality is excellent.")
        sys.exit(0)
    else:
        print("💥 Some checks failed. Please fix the issues above.")
        print("\nTips:")
        print("- Run with --fix to automatically fix formatting issues")
        print("- Run with --coverage to see detailed test coverage")
        print("- Check individual tool outputs for specific guidance")
        sys.exit(1)


if __name__ == "__main__":
    main()
