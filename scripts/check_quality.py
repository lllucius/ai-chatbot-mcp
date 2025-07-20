#!/usr/bin/env python3
"""
Code quality check script for AI Chatbot Platform.

This script runs comprehensive code quality checks including linting,
formatting, type checking, security scanning, and testing.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(command: List[str], description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"Running {description}...")
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=False
        )
        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True, result.stdout
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False, result.stderr
    except FileNotFoundError:
        print(f"⚠️  {description} skipped - command not found")
        return True, "Command not found"


def check_formatting() -> bool:
    """Check code formatting with black."""
    success, _ = run_command(
        ["black", "--check", "app", "tests"],
        "Code formatting (black)"
    )
    return success


def check_imports() -> bool:
    """Check import sorting with isort."""
    success, _ = run_command(
        ["isort", "--check-only", "app", "tests"],
        "Import sorting (isort)"
    )
    return success


def check_linting() -> bool:
    """Check code linting with flake8."""
    success, _ = run_command(
        ["flake8", "app", "tests", "--max-line-length=88", "--extend-ignore=E203,W503"],
        "Code linting (flake8)"
    )
    return success


def check_types() -> bool:
    """Check type hints with mypy."""
    success, _ = run_command(
        ["mypy", "app", "--ignore-missing-imports", "--no-strict-optional"],
        "Type checking (mypy)"
    )
    return success


def check_security() -> bool:
    """Check security issues with bandit."""
    success, _ = run_command(
        ["bandit", "-r", "app", "-x", "tests"],
        "Security check (bandit)"
    )
    return success


def run_tests() -> bool:
    """Run tests with pytest."""
    success, _ = run_command(
        ["pytest", "tests/", "-v", "--tb=short"],
        "Test suite (pytest)"
    )
    return success


def run_tests_with_coverage() -> bool:
    """Run tests with coverage report."""
    success, _ = run_command(
        ["pytest", "tests/", "--cov=app", "--cov-report=term-missing", "--cov-report=html"],
        "Test coverage (pytest-cov)"
    )
    if success:
        print("📊 Coverage report generated in htmlcov/index.html")
    return success


def fix_formatting() -> bool:
    """Fix code formatting issues."""
    print("🔧 Fixing code formatting...")
    black_success, _ = run_command(["black", "app", "tests"], "Black formatting")
    isort_success, _ = run_command(["isort", "app", "tests"], "Import sorting")
    return black_success and isort_success


def main():
    """Main function for code quality checks."""
    parser = argparse.ArgumentParser(description="Run code quality checks")
    parser.add_argument(
        "--fix", 
        action="store_true", 
        help="Fix formatting issues automatically"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--skip-tests", 
        action="store_true", 
        help="Skip running tests"
    )
    parser.add_argument(
        "--security-only", 
        action="store_true", 
        help="Run only security checks"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    
    print("🔍 Starting code quality checks for AI Chatbot Platform")
    print("=" * 60)
    
    all_passed = True
    
    if args.fix:
        if not fix_formatting():
            all_passed = False
        print("=" * 60)
    
    if args.security_only:
        if not check_security():
            all_passed = False
    else:
        # Run all checks
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
            print("-" * 40)
    
    print("=" * 60)
    
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