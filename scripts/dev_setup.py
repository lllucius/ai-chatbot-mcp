"Script for dev setup operations."

import argparse
import os
import subprocess
import sys
from pathlib import Path
from shutil import which


def check_command_exists(command: str) -> bool:
    "Check Command Exists operation."
    return which(command) is not None


def run_command(command: str, description: str, check: bool = True) -> bool:
    "Run Command operation."
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=check)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed with return code {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False


def check_prerequisites() -> bool:
    "Check Prerequisites operation."
    print("🔍 Checking prerequisites...")
    required_commands = {
        "python": "Python 3.11+",
        "pip": "pip package manager",
        "git": "Git version control",
    }
    optional_commands = {"psql": "PostgreSQL client"}
    missing_required = []
    missing_optional = []
    for cmd, desc in required_commands.items():
        if not check_command_exists(cmd):
            missing_required.append(f"  - {cmd}: {desc}")
    for cmd, desc in optional_commands.items():
        if not check_command_exists(cmd):
            missing_optional.append(f"  - {cmd}: {desc}")
    if missing_required:
        print("❌ Missing required prerequisites:")
        for item in missing_required:
            print(item)
        return False
    if missing_optional:
        print("⚠️  Missing optional prerequisites:")
        for item in missing_optional:
            print(item)
        print("You can still develop without these, but some features may be limited.")
    print("✅ All required prerequisites are available")
    return True


def setup_virtual_environment() -> bool:
    "Setup Virtual Environment operation."
    print("🐍 Setting up Python virtual environment...")
    if Path("venv").exists():
        print("Virtual environment already exists")
        return True
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    activate_cmd = (
        "source venv/bin/activate" if (os.name != "nt") else "venv\\Scripts\\activate"
    )
    pip_upgrade = f"{activate_cmd} && pip install --upgrade pip"
    return run_command(pip_upgrade, "Upgrading pip in virtual environment")


def install_dependencies() -> bool:
    "Install Dependencies operation."
    print("📦 Installing Python dependencies...")
    activate_cmd = (
        "source venv/bin/activate" if (os.name != "nt") else "venv\\Scripts\\activate"
    )
    install_cmd = f"{activate_cmd} && pip install -r requirements.txt"
    if not run_command(install_cmd, "Installing main dependencies"):
        return False
    dev_deps = [
        "pytest-asyncio",
        "pytest-cov",
        "black",
        "isort",
        "mypy",
        "flake8",
        "pre-commit",
        "types-all",
    ]
    dev_install_cmd = f"{activate_cmd} && pip install {' '.join(dev_deps)}"
    return run_command(dev_install_cmd, "Installing development dependencies")


def setup_environment_file() -> bool:
    "Setup Environment File operation."
    print("⚙️  Setting up environment configuration...")
    env_file = Path(".env")
    env_example = Path(".env.example")
    if env_file.exists():
        print("Environment file already exists")
        return True
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    try:
        env_file.write_text(env_example.read_text())
        print("✅ Created .env file from .env.example")
        print("⚠️  Please edit .env file with your configuration:")
        print("  - Add your OpenAI API key")
        print("  - Configure database connection")
        print("  - Set a secure SECRET_KEY")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def setup_pre_commit_hooks() -> bool:
    "Setup Pre Commit Hooks operation."
    print("🪝 Setting up pre-commit hooks...")
    activate_cmd = (
        "source venv/bin/activate" if (os.name != "nt") else "venv\\Scripts\\activate"
    )
    hook_cmd = f"{activate_cmd} && pre-commit install"
    return run_command(hook_cmd, "Installing pre-commit hooks")


def create_database_setup_script() -> bool:
    "Create new database setup script."
    print("🗄️  Creating database setup helper...")
    db_script = '#!/bin/bash\n# Database setup script for AI Chatbot Platform\n\necho "Setting up PostgreSQL database..."\n\n# Check if PostgreSQL is running\nif ! pg_isready &> /dev/null; then\n    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."\n    exit 1\nfi\n\n# Create database and user\npsql -U postgres -c "CREATE DATABASE ai_chatbot_dev;" 2>/dev/null || echo "Database may already exist"\npsql -U postgres -c "CREATE USER chatbot_user WITH PASSWORD \'dev_password\';" 2>/dev/null || echo "User may already exist"\npsql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ai_chatbot_dev TO chatbot_user;" 2>/dev/null\npsql -U postgres -d ai_chatbot_dev -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null\n\necho "✅ Database setup completed"\necho "Database URL: postgresql+asyncpg://chatbot_user:dev_password@localhost:5432/ai_chatbot_dev"\n'
    try:
        script_path = Path("scripts/setup_database.sh")
        script_path.parent.mkdir(exist_ok=True)
        script_path.write_text(db_script)
        script_path.chmod(493)
        print("✅ Created database setup script at scripts/setup_database.sh")
        return True
    except Exception as e:
        print(f"❌ Failed to create database setup script: {e}")
        return False


def print_next_steps():
    "Print Next Steps operation."
    print(("\n" + ("=" * 60)))
    print("🎉 Development environment setup completed!")
    print(("=" * 60))
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Set up PostgreSQL database:")
    print("   - Install PostgreSQL with pgvector extension")
    print("   - Run: bash scripts/setup_database.sh")
    print("3. Initialize the database:")
    print("   - source venv/bin/activate")
    print("   - python scripts/startup.py")
    print("4. Start the development server:")
    print("   - uvicorn app.main:app --reload")
    print("5. Visit http://localhost:8000/docs for API documentation")
    print("\nOptional:")
    print("- Run code quality checks: python scripts/check_quality.py")
    print("- Set up your IDE/editor with Python environment at ./venv")


def main():
    "Main entry point."
    parser = argparse.ArgumentParser(description="Set up development environment")
    parser.add_argument(
        "--skip-venv", action="store_true", help="Skip virtual environment setup"
    )
    parser.add_argument(
        "--skip-hooks", action="store_true", help="Skip pre-commit hooks setup"
    )
    args = parser.parse_args()
    print("🚀 AI Chatbot Platform - Development Environment Setup")
    print(("=" * 60))
    if (not Path("app").exists()) or (not Path("requirements.txt").exists()):
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    if not check_prerequisites():
        print("Please install missing prerequisites and run again.")
        sys.exit(1)
    success = True
    if not args.skip_venv:
        if not setup_virtual_environment():
            success = False
    if success and (not install_dependencies()):
        success = False
    if success and (not setup_environment_file()):
        success = False
    if success and (not args.skip_hooks):
        if not setup_pre_commit_hooks():
            success = False
    if success and (not create_database_setup_script()):
        success = False
    if success:
        print_next_steps()
    else:
        print("\n❌ Setup encountered some issues. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
