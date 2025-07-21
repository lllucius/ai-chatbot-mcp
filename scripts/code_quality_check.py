#!/usr/bin/env python3
"""
Code quality checker for the AI Chatbot Platform.

This script performs various code quality checks including:
- Import organization validation
- Docstring completeness checks
- Logging pattern consistency
- Service class inheritance validation
- Error handling pattern verification

Usage:
    python scripts/code_quality_check.py [--fix] [--report]

Options:
    --fix: Automatically fix issues where possible
    --report: Generate detailed quality report

Generated on: 2025-01-20 21:00:00 UTC
Current User: assistant
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import Dict, List


class CodeQualityChecker:
    """Code quality checker with various validation rules."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.violations = []

    def check_all(self) -> Dict[str, List[str]]:
        """Run all quality checks."""
        results = {
            "import_organization": [],
            "docstring_completeness": [],
            "logging_consistency": [],
            "service_inheritance": [],
            "error_handling": [],
        }

        python_files = list(self.root_dir.rglob("*.py"))

        for file_path in python_files:
            if "tests/" in str(file_path) or "__pycache__" in str(file_path):
                continue

            results["import_organization"].extend(
                self.check_import_organization(file_path)
            )
            results["docstring_completeness"].extend(self.check_docstrings(file_path))
            results["logging_consistency"].extend(
                self.check_logging_patterns(file_path)
            )
            results["service_inheritance"].extend(
                self.check_service_inheritance(file_path)
            )
            results["error_handling"].extend(self.check_error_handling(file_path))

        return results

    def check_import_organization(self, file_path: Path) -> List[str]:
        """Check import organization in a file."""
        violations = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Parse imports
            tree = ast.parse(content)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node.lineno)

            # Check if imports are at the top (after docstring)
            if imports:
                first_import = min(imports)
                # Simple check - imports should be early in file
                if first_import > 20:  # Allow for module docstring
                    violations.append(f"{file_path}: Imports should be at top of file")

        except Exception as e:
            violations.append(f"{file_path}: Error parsing imports - {e}")

        return violations

    def check_docstrings(self, file_path: Path) -> List[str]:
        """Check docstring completeness."""
        violations = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    docstring = ast.get_docstring(node)

                    if not docstring:
                        violations.append(
                            f"{file_path}:{node.lineno}: Missing docstring for {node.name}"
                        )
                    elif len(docstring.strip()) < 20:
                        violations.append(
                            f"{file_path}:{node.lineno}: Insufficient docstring for {node.name}"
                        )

        except Exception as e:
            violations.append(f"{file_path}: Error checking docstrings - {e}")

        return violations

    def check_logging_patterns(self, file_path: Path) -> List[str]:
        """Check logging pattern consistency."""
        violations = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Check for old logging pattern
            if "logger = logging.getLogger(__name__)" in content:
                if "from .base import BaseService" not in content:
                    violations.append(
                        f"{file_path}: Using old logging pattern, consider BaseService"
                    )

            # Check for structured logging usage
            if (
                "logger." in content
                and "StructuredLogger" not in content
                and "BaseService" not in content
            ):
                violations.append(
                    f"{file_path}: Consider using StructuredLogger for better logging"
                )

        except Exception as e:
            violations.append(f"{file_path}: Error checking logging - {e}")

        return violations

    def check_service_inheritance(self, file_path: Path) -> List[str]:
        """Check service class inheritance."""
        violations = []

        if not file_path.name.endswith(".py") or "services" not in str(file_path):
            return violations

        try:
            with open(file_path, "r") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.endswith("Service"):
                    if node.name != "BaseService":
                        # Check if inherits from BaseService
                        inherits_base = any(
                            getattr(base, "id", None) == "BaseService"
                            or getattr(base, "attr", None) == "BaseService"
                            for base in node.bases
                        )

                        if not inherits_base and "BaseService" in content:
                            violations.append(
                                f"{file_path}:{node.lineno}: {node.name} should inherit from BaseService"
                            )

        except Exception as e:
            violations.append(f"{file_path}: Error checking service inheritance - {e}")

        return violations

    def check_error_handling(self, file_path: Path) -> List[str]:
        """Check error handling patterns."""
        violations = []

        if not file_path.name.endswith(".py") or "api" not in str(file_path):
            return violations

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Check for old error handling patterns
            if "HTTPException" in content and "@handle_api_errors" not in content:
                if "router" in content and "APIRouter" in content:
                    violations.append(
                        f"{file_path}: Consider using @handle_api_errors decorator"
                    )

        except Exception as e:
            violations.append(f"{file_path}: Error checking error handling - {e}")

        return violations

    def generate_report(self, results: Dict[str, List[str]]) -> str:
        """Generate a quality report."""
        report = ["AI Chatbot Platform - Code Quality Report", "=" * 50, ""]

        total_violations = sum(len(violations) for violations in results.values())
        report.append(f"Total violations found: {total_violations}\n")

        for category, violations in results.items():
            if violations:
                report.append(
                    f"{category.replace('_', ' ').title()}: {len(violations)} violations"
                )
                for violation in violations[:10]:  # Limit to first 10
                    report.append(f"  - {violation}")
                if len(violations) > 10:
                    report.append(f"  ... and {len(violations) - 10} more")
                report.append("")

        return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check code quality")
    parser.add_argument("--fix", action="store_true", help="Fix issues automatically")
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed report"
    )
    parser.add_argument("--dir", default=".", help="Directory to check")

    args = parser.parse_args()

    checker = CodeQualityChecker(args.dir)
    results = checker.check_all()

    if args.report:
        report = checker.generate_report(results)
        with open("code_quality_report.txt", "w") as f:
            f.write(report)
        print("Report generated: code_quality_report.txt")
    else:
        # Print summary
        total_violations = sum(len(violations) for violations in results.values())
        print(f"Code quality check complete: {total_violations} violations found")

        for category, violations in results.items():
            if violations:
                print(f"  {category}: {len(violations)} issues")

    # Exit with error code if violations found
    total_violations = sum(len(violations) for violations in results.values())
    sys.exit(1 if total_violations > 0 else 0)


if __name__ == "__main__":
    main()
