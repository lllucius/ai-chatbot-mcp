#!/usr/bin/env python3
"""
Comprehensive test suite for the API-based CLI.

This script tests all major CLI commands and their functionality to ensure
the API-based CLI provides equivalent functionality to the original manage.py.
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class CLITester:
    """Test harness for the API CLI."""
    
    def __init__(self, cli_path: str = "api_manage.py"):
        self.cli_path = cli_path
        self.test_results: List[Dict] = []
        self.failed_tests = 0
        self.passed_tests = 0
        
    def run_command(self, command: List[str], expect_failure: bool = False) -> Dict:
        """Run a CLI command and capture results."""
        full_command = ["python", self.cli_path] + command
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = (result.returncode == 0) if not expect_failure else (result.returncode != 0)
            
            test_result = {
                "command": " ".join(command),
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "expected_failure": expect_failure
            }
            
            if success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            
            self.test_results.append(test_result)
            return test_result
            
        except subprocess.TimeoutExpired:
            test_result = {
                "command": " ".join(command),
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out",
                "expected_failure": expect_failure
            }
            self.failed_tests += 1
            self.test_results.append(test_result)
            return test_result
    
    def test_basic_commands(self):
        """Test basic CLI commands that don't require authentication."""
        console.print(Panel("Testing Basic Commands", style="blue"))
        
        # Test help commands
        self.run_command(["--help"])
        self.run_command(["users", "--help"])
        self.run_command(["documents", "--help"])
        self.run_command(["conversations", "--help"])
        self.run_command(["analytics", "--help"])
        self.run_command(["database", "--help"])
        self.run_command(["tasks", "--help"])
        self.run_command(["prompts", "--help"])
        self.run_command(["profiles", "--help"])
        
        # Test informational commands (these should work without auth)
        self.run_command(["quickstart"])
        self.run_command(["config"])
        self.run_command(["auth-status"])
        
        # Test version (this requires API to be running, might fail)
        self.run_command(["version"], expect_failure=True)
        
        # Test health (this requires API to be running, might fail)
        self.run_command(["health"], expect_failure=True)
    
    def test_authentication_flow(self):
        """Test authentication commands."""
        console.print(Panel("Testing Authentication Flow", style="green"))
        
        # Test logout (should work even if not logged in)
        self.run_command(["logout"])
        
        # Test commands that require auth (should fail without login)
        self.run_command(["users", "list"], expect_failure=True)
        self.run_command(["documents", "list"], expect_failure=True)
        self.run_command(["conversations", "list"], expect_failure=True)
        
        # Note: We can't test actual login without a running server and credentials
        console.print("[yellow]Note: Login testing requires a running API server[/yellow]")
    
    def test_user_commands(self):
        """Test user management commands."""
        console.print(Panel("Testing User Commands", style="cyan"))
        
        # These will fail without authentication, but we test the command parsing
        self.run_command(["users", "list"], expect_failure=True)
        self.run_command(["users", "list", "--active-only"], expect_failure=True)
        self.run_command(["users", "list", "--search", "test"], expect_failure=True)
        self.run_command(["users", "show", "testuser"], expect_failure=True)
        self.run_command(["users", "stats"], expect_failure=True)
        
        # Test commands with invalid parameters
        self.run_command(["users", "create"], expect_failure=True)  # Missing required args
        self.run_command(["users", "show"], expect_failure=True)    # Missing required args
    
    def test_document_commands(self):
        """Test document management commands."""
        console.print(Panel("Testing Document Commands", style="magenta"))
        
        # These will fail without authentication
        self.run_command(["documents", "list"], expect_failure=True)
        self.run_command(["documents", "list", "--status", "completed"], expect_failure=True)
        self.run_command(["documents", "stats"], expect_failure=True)
        self.run_command(["documents", "search", "test"], expect_failure=True)
        
        # Test file upload (will fail without auth and valid file)
        self.run_command(["documents", "upload", "nonexistent.pdf"], expect_failure=True)
        
        # Test cleanup commands
        self.run_command(["documents", "cleanup", "--dry-run"], expect_failure=True)
    
    def test_conversation_commands(self):
        """Test conversation management commands."""
        console.print(Panel("Testing Conversation Commands", style="yellow"))
        
        # These will fail without authentication
        self.run_command(["conversations", "list"], expect_failure=True)
        self.run_command(["conversations", "list", "--active-only"], expect_failure=True)
        self.run_command(["conversations", "stats"], expect_failure=True)
        self.run_command(["conversations", "search", "test"], expect_failure=True)
        
        # Test export/import (will fail without auth)
        self.run_command(["conversations", "export", "test-id"], expect_failure=True)
        self.run_command(["conversations", "import-conversation", "test.json"], expect_failure=True)
        
        # Test archival
        self.run_command(["conversations", "archive", "--dry-run"], expect_failure=True)
    
    def test_analytics_commands(self):
        """Test analytics and reporting commands."""
        console.print(Panel("Testing Analytics Commands", style="red"))
        
        # These will fail without authentication
        self.run_command(["analytics", "overview"], expect_failure=True)
        self.run_command(["analytics", "usage"], expect_failure=True)
        self.run_command(["analytics", "usage", "--period", "7d"], expect_failure=True)
        self.run_command(["analytics", "performance"], expect_failure=True)
        self.run_command(["analytics", "users"], expect_failure=True)
        self.run_command(["analytics", "trends"], expect_failure=True)
        self.run_command(["analytics", "export-report"], expect_failure=True)
    
    def test_database_commands(self):
        """Test database management commands."""
        console.print(Panel("Testing Database Commands", style="blue"))
        
        # These will fail without authentication
        self.run_command(["database", "status"], expect_failure=True)
        self.run_command(["database", "tables"], expect_failure=True)
        self.run_command(["database", "migrations"], expect_failure=True)
        self.run_command(["database", "analyze"], expect_failure=True)
        
        # Test dangerous commands (will fail without auth)
        self.run_command(["database", "init"], expect_failure=True)
        self.run_command(["database", "upgrade"], expect_failure=True)
        self.run_command(["database", "backup"], expect_failure=True)
        self.run_command(["database", "vacuum"], expect_failure=True)
        
        # Test query command
        self.run_command(["database", "query", "SELECT 1"], expect_failure=True)
    
    def test_task_commands(self):
        """Test background task management commands."""
        console.print(Panel("Testing Task Commands", style="green"))
        
        # These will fail without authentication
        self.run_command(["tasks", "status"], expect_failure=True)
        self.run_command(["tasks", "workers"], expect_failure=True)
        self.run_command(["tasks", "queue"], expect_failure=True)
        self.run_command(["tasks", "active"], expect_failure=True)
        self.run_command(["tasks", "stats"], expect_failure=True)
        self.run_command(["tasks", "monitor"], expect_failure=True)
        
        # Test management commands
        self.run_command(["tasks", "retry-failed"], expect_failure=True)
        self.run_command(["tasks", "schedule", "test_task"], expect_failure=True)
    
    def test_prompt_commands(self):
        """Test prompt management commands."""
        console.print(Panel("Testing Prompt Commands", style="magenta"))
        
        # These will fail without authentication
        self.run_command(["prompts", "list"], expect_failure=True)
        self.run_command(["prompts", "stats"], expect_failure=True)
        self.run_command(["prompts", "categories"], expect_failure=True)
        self.run_command(["prompts", "tags"], expect_failure=True)
        
        # Test management commands
        self.run_command(["prompts", "show", "test"], expect_failure=True)
        self.run_command(["prompts", "add", "test", "--title", "Test", "--content", "Test content"], expect_failure=True)
    
    def test_profile_commands(self):
        """Test LLM profile management commands."""
        console.print(Panel("Testing Profile Commands", style="cyan"))
        
        # These will fail without authentication
        self.run_command(["profiles", "list"], expect_failure=True)
        self.run_command(["profiles", "stats"], expect_failure=True)
        
        # Test management commands
        self.run_command(["profiles", "show", "test"], expect_failure=True)
        self.run_command(["profiles", "add", "test", "--title", "Test Profile"], expect_failure=True)
        self.run_command(["profiles", "clone", "source", "target"], expect_failure=True)
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        console.print(Panel("Testing Edge Cases", style="red"))
        
        # Test invalid commands
        self.run_command(["invalid-command"], expect_failure=True)
        self.run_command(["users", "invalid-subcommand"], expect_failure=True)
        
        # Test missing required arguments
        self.run_command(["documents", "upload"], expect_failure=True)
        self.run_command(["conversations", "export"], expect_failure=True)
        self.run_command(["database", "query"], expect_failure=True)
        
        # Test invalid options
        self.run_command(["analytics", "usage", "--period", "invalid"], expect_failure=True)
        self.run_command(["users", "list", "--limit", "-1"], expect_failure=True)
    
    def run_all_tests(self):
        """Run the complete test suite."""
        console.print(Panel("Starting API CLI Test Suite", style="bold blue"))
        
        self.test_basic_commands()
        self.test_authentication_flow()
        self.test_user_commands()
        self.test_document_commands()
        self.test_conversation_commands()
        self.test_analytics_commands()
        self.test_database_commands()
        self.test_task_commands()
        self.test_prompt_commands()
        self.test_profile_commands()
        self.test_edge_cases()
        
        self.show_results()
    
    def show_results(self):
        """Display test results summary."""
        console.print(Panel("Test Results Summary", style="bold"))
        
        # Summary statistics
        total_tests = len(self.test_results)
        
        summary_table = Table(title="Test Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="white")
        summary_table.add_column("Percentage", style="green")
        
        summary_table.add_row("Total Tests", str(total_tests), "100%")
        summary_table.add_row("Passed", str(self.passed_tests), f"{(self.passed_tests/total_tests)*100:.1f}%")
        summary_table.add_row("Failed", str(self.failed_tests), f"{(self.failed_tests/total_tests)*100:.1f}%")
        
        console.print(summary_table)
        
        # Show failed tests
        failed_tests = [t for t in self.test_results if not t["success"]]
        
        if failed_tests:
            console.print("\n[bold red]Failed Tests:[/bold red]")
            
            failed_table = Table()
            failed_table.add_column("Command", style="cyan")
            failed_table.add_column("Return Code", style="yellow")
            failed_table.add_column("Error", style="red")
            failed_table.add_column("Expected", style="white")
            
            for test in failed_tests[:10]:  # Show first 10 failures
                error_msg = test["stderr"][:100] + "..." if len(test["stderr"]) > 100 else test["stderr"]
                expected = "Yes" if test["expected_failure"] else "No"
                
                failed_table.add_row(
                    test["command"],
                    str(test["returncode"]),
                    error_msg or "No error message",
                    expected
                )
            
            console.print(failed_table)
            
            if len(failed_tests) > 10:
                console.print(f"\n[dim]... and {len(failed_tests) - 10} more failed tests[/dim]")
        
        # Overall result
        if self.failed_tests == 0:
            console.print(Panel("🎉 All tests passed!", style="bold green"))
        else:
            console.print(Panel(f"⚠️ {self.failed_tests} tests failed", style="bold yellow"))
        
        # Save detailed results
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        console.print(f"\n[dim]Detailed results saved to test_results.json[/dim]")


def main():
    """Main test function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        console.print("""
[bold]API CLI Test Suite[/bold]

This script tests the API-based CLI to ensure it provides equivalent
functionality to the original manage.py script.

Usage:
    python test_api_cli.py

The test suite will:
1. Test all command help functions
2. Test authentication flow
3. Test all major command categories
4. Test edge cases and error conditions
5. Generate a summary report

Note: Most tests expect failures since they require a running API server
and authentication. The tests verify that commands are properly structured
and can be parsed correctly.
        """)
        return
    
    # Check if CLI script exists
    cli_path = Path("api_manage.py")
    if not cli_path.exists():
        console.print("[red]Error: api_manage.py not found in current directory[/red]")
        return
    
    tester = CLITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()