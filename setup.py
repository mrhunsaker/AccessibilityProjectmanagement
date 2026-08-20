#!/usr/bin/env python3
"""
Accessibility Project Management - Terminal Setup Assistant

This script guides first-time users through the setup process, including:
- Detecting the operating system
- Creating the .secrets file with required configuration
- Setting up tools.ini from the example
- Validating the setup
- Providing next steps
"""

import os
import sys
import platform
import secrets
import hashlib
import base64
import getpass
import shutil
from pathlib import Path
from typing import Dict, Any


class SetupAssistant:
    """Terminal-based setup assistant for Accessibility Project Management."""

    def __init__(self):
        self.repo_root = Path(__file__).parent.resolve()
        self.secrets_file = self.repo_root / ".secrets"
        self.tools_example = self.repo_root / "tools.ini.example"
        self.tools_file = self.repo_root / "tools.ini"
        self.is_windows = platform.system() == "Windows"
        self.is_macos = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"

    def print_header(self, text: str) -> None:
        """Print a formatted header."""
        print("\n" + "=" * 70)
        print(f"  {text}")
        print("=" * 70)

    def print_section(self, text: str) -> None:
        """Print a formatted section."""
        print(f"\n  {text}")
        print("  " + "-" * 66)

    def print_success(self, text: str) -> None:
        """Print a success message."""
        print(f"  ✓ {text}")

    def print_warning(self, text: str) -> None:
        """Print a warning message."""
        print(f"  ⚠ {text}")

    def print_error(self, text: str) -> None:
        """Print an error message."""
        print(f"  ✗ {text}")

    def print_info(self, text: str) -> None:
        """Print an info message."""
        print(f"  ℹ {text}")

    def detect_os(self) -> str:
        """Detect and return the operating system."""
        if self.is_windows:
            return "Windows"
        elif self.is_macos:
            return "macOS"
        elif self.is_linux:
            return "Linux"
        else:
            return platform.system()

    def check_prerequisites(self) -> Dict[str, Any]:
        """Check for required prerequisites."""
        results = {
            "python_version": None,
            "uv_installed": False,
            "python_ok": False,
            "all_ok": False,
        }

        # Check Python version
        try:
            python_version = sys.version_info
            results["python_version"] = (
                f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            )
            results["python_ok"] = python_version >= (3, 12)
        except Exception:
            results["python_ok"] = False

        # Check for uv
        try:
            import subprocess

            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            results["uv_installed"] = result.returncode == 0
        except Exception:
            results["uv_installed"] = False

        results["all_ok"] = results.get("python_ok", False) and results["uv_installed"]
        return results

    def generate_storage_secret(self) -> str:
        """Generate a secure STORAGE_SECRET."""
        return secrets.token_urlsafe(32)

    def generate_password_hash(self, password: str) -> str:
        """Generate PBKDF2 password hash."""
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260000)
        return base64.b64encode(salt + dk).decode()

    def create_secrets_file(self) -> bool:
        """Interactively create the .secrets file."""
        self.print_section("Creating .secrets file")

        # Generate STORAGE_SECRET automatically
        storage_secret = self.generate_storage_secret()
        self.print_info("Generated STORAGE_SECRET")

        # Get password from user
        while True:
            password = getpass.getpass("  Enter admin password: ")
            if password:
                confirm = getpass.getpass("  Confirm admin password: ")
                if password == confirm:
                    break
                else:
                    self.print_error("Passwords do not match. Please try again.")
            else:
                self.print_error("Password cannot be empty.")

        password_hash = self.generate_password_hash(password)
        self.print_info("Generated password hash")

        # Ask about optional settings
        print("\n  Optional Settings:")

        api_auth = self.ask_yes_no("  Enable API authentication?", default=True)
        api_key = ""
        if api_auth:
            api_key = secrets.token_urlsafe(32)
            self.print_info(f"  Generated API key: {api_key}")

        db_path = self.ask_input("  Database path (leave blank for default):", default="")
        backup_dir = self.ask_input("  Backup directory (leave blank for default):", default="")
        backup_retention = self.ask_input(
            "  Backup retention days (leave blank for 30):", default="30"
        )
        log_level = self.ask_input(
            "  Log level (INFO/DEBUG/WARNING, leave blank for INFO):", default="INFO"
        )

        # Build secrets content
        secrets_content = f"""# Accessibility Project Management - Secrets Configuration
# Generated by setup.py - DO NOT COMMIT THIS FILE
# This file must be in the repository root directory

# Required Secrets
STORAGE_SECRET={storage_secret}
ACCESSMAN_PASSWORD_HASH={password_hash}

# Optional Secrets
ACCESSMAN_API_AUTH_REQUIRED={"1" if api_auth else "0"}
ACCESSMAN_API_KEY={api_key}
"""

        if db_path:
            secrets_content += f"ACCESSMAN_DB_PATH={db_path}\n"
        if backup_dir:
            secrets_content += f"ACCESSMAN_BACKUP_DIR={backup_dir}\n"
        secrets_content += f"ACCESSMAN_BACKUP_RETENTION={backup_retention}\n"
        secrets_content += f"ACCESSMAN_LOG_LEVEL={log_level}\n"

        # Write the file
        try:
            with open(self.secrets_file, "w") as f:
                f.write(secrets_content)

            # Set permissions (600 on Unix-like systems)
            if not self.is_windows:
                os.chmod(self.secrets_file, 0o600)

            self.print_success(f"Created .secrets file at {self.secrets_file}")
            self.print_warning("  ⚠ NEVER COMMIT THIS FILE TO VERSION CONTROL!")
            return True

        except Exception as e:
            self.print_error(f"Failed to create .secrets file: {e}")
            return False

    def setup_tools_config(self) -> bool:
        """Set up tools.ini from the example."""
        self.print_section("Setting up tools.ini")

        if not self.tools_example.exists():
            self.print_warning("tools.ini.example not found. Creating a basic tools.ini.")
            tools_content = self.get_default_tools_config()
        else:
            self.print_info("Found tools.ini.example")

            # Check if tools.ini already exists
            if self.tools_file.exists():
                overwrite = self.ask_yes_no(
                    "  tools.ini already exists. Overwrite?", default=False
                )
                if not overwrite:
                    self.print_info("Skipping tools.ini setup")
                    return True

            # Copy from example
            try:
                shutil.copy2(self.tools_example, self.tools_file)
                self.print_success(f"Created tools.ini from {self.tools_example}")

                # Offer to configure paths
                if self.ask_yes_no("  Configure external tool paths now?", default=True):
                    self.configure_tool_paths()
                return True

            except Exception as e:
                self.print_error(f"Failed to copy tools.ini: {e}")
                return False

        # Create basic tools.ini
        try:
            with open(self.tools_file, "w") as f:
                f.write(tools_content)
            self.print_success("Created basic tools.ini")
            return True
        except Exception as e:
            self.print_error(f"Failed to create tools.ini: {e}")
            return False

    def get_default_tools_config(self) -> str:
        """Get default tools.ini content based on OS."""
        if self.is_windows:
            return """[tools]
# Configure paths to external accessibility tools
# Update these paths to match your system
ace =
epubcheck =
pipeline =
liblouis =

[paths]
# Additional PATH directories
extra =
"""
        elif self.is_macos:
            return """[tools]
# Configure paths to external accessibility tools
# Common macOS paths (using Homebrew):
ace = /opt/homebrew/bin/ace
epubcheck = /opt/homebrew/bin/epubcheck
pipeline = /opt/homebrew/bin/pipeline2
liblouis = /opt/homebrew/bin/lou_translate

[paths]
# Additional PATH directories
extra =
    /opt/homebrew/bin
    /usr/local/bin
"""
        else:
            return """[tools]
# Configure paths to external accessibility tools
# Common Linux paths:
ace = /usr/local/bin/ace
epubcheck = /usr/local/bin/epubcheck
pipeline = /opt/daisy-pipeline/bin/pipeline2
liblouis = /usr/bin/lou_translate

[paths]
# Additional PATH directories
extra =
    /opt/daisy-pipeline/bin
    /usr/local/share/npm/bin
    /usr/local/bin
"""

    def configure_tool_paths(self) -> None:
        """Interactively configure tool paths."""
        self.print_section("Configuring External Tool Paths")

        tools = {
            "ace": "DAISY Ace validator",
            "epubcheck": "EPUB validator",
            "pipeline": "DAISY Pipeline 2",
            "liblouis": "Liblouis braille translator",
        }

        print("\n  Configure paths for external accessibility tools:")
        print("  (Leave blank to use default/empty)")

        # Read current tools.ini
        config = {}
        if self.tools_file.exists():
            try:
                import configparser

                parser = configparser.ConfigParser()
                parser.read(self.tools_file)
                if "tools" in parser:
                    config = dict(parser["tools"])
            except Exception:
                pass

        # Ask for each tool
        for tool_name, description in tools.items():
            current = config.get(tool_name, "")
            if current:
                prompt = f"  {tool_name} ({description}) [{current}]: "
            else:
                prompt = f"  {tool_name} ({description}): "

            path = input(prompt).strip()
            if path:
                config[tool_name] = path
            elif tool_name not in config:
                config[tool_name] = ""

        # Save back to file
        try:
            import configparser

            parser = configparser.ConfigParser()
            parser["tools"] = config

            # Preserve extra paths if they exist
            if self.tools_file.exists():
                parser2 = configparser.ConfigParser()
                parser2.read(self.tools_file)
                if "paths" in parser2:
                    parser["paths"] = dict(parser2["paths"])
                else:
                    parser["paths"] = {"extra": ""}
            else:
                parser["paths"] = {"extra": ""}

            with open(self.tools_file, "w") as f:
                parser.write(f)

            self.print_success("Updated tools.ini with configured paths")

        except Exception as e:
            self.print_error(f"Failed to update tools.ini: {e}")

    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask a yes/no question."""
        default_str = "Y/n" if default else "y/N"
        while True:
            response = input(f"{question} ({default_str}): ").strip().lower()
            if not response:
                return default
            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False
            print("  Please enter 'y' or 'n'")

    def ask_input(self, question: str, default: str = "") -> str:
        """Ask for input with a default."""
        if default:
            prompt = f"{question} [{default}]: "
        else:
            prompt = f"{question}: "

        response = input(prompt).strip()
        return response if response else default

    def validate_setup(self) -> Dict[str, Any]:
        """Validate the current setup."""
        self.print_section("Validating Setup")

        results = {
            "secrets_exists": False,
            "secrets_valid": False,
            "tools_exists": False,
            "all_ok": False,
        }

        # Check .secrets file
        if self.secrets_file.exists():
            results["secrets_exists"] = True
            try:
                with open(self.secrets_file, "r") as f:
                    content = f.read()

                required_keys = ["STORAGE_SECRET", "ACCESSMAN_PASSWORD_HASH"]
                for key in required_keys:
                    if f"{key}=" not in content:
                        self.print_error(f"  Missing required key: {key}")
                        break
                else:
                    results["secrets_valid"] = True
                    self.print_success("  .secrets file is valid")
            except Exception as e:
                self.print_error(f"  Error reading .secrets: {e}")
        else:
            self.print_error("  .secrets file does not exist")

        # Check tools.ini
        if self.tools_file.exists():
            results["tools_exists"] = True
            self.print_success("  tools.ini exists")
        else:
            self.print_warning("  tools.ini does not exist (optional)")
            results["tools_exists"] = True

        results["all_ok"] = (
            results["secrets_exists"] and results["secrets_valid"] and results["tools_exists"]
        )
        return results

    def show_next_steps(self) -> None:
        """Display next steps after setup."""
        self.print_section("Next Steps")

        print("""
  Your setup is complete! Here's what to do next:

  1. Install dependencies (if not already done):
     $ uv sync

  2. Start the application:
     $ uv run AccessMan

  3. Open your browser to:
     http://localhost:8765

  4. Log in with the password you configured

  Optional:
  - Review and customize tools.ini for your external tools
  - Configure backup settings in .secrets
  - Set up API authentication if needed
        """)

        # OS-specific notes
        if self.is_windows:
            print("\n  Windows Notes:")
            print("  - Make sure Python is in your PATH")
            print("  - Use 'uv sync' in PowerShell or CMD")
        elif self.is_macos or self.is_linux:
            print("\n  Unix-like Systems Notes:")
            print("  - The .secrets file has been set to 600 permissions")
            print("  - Consider using tmux or screen for long-running sessions")

    def run(self) -> None:
        """Run the setup assistant."""
        # Clear screen for better visibility
        if not self.is_windows:
            os.system("clear")
        else:
            os.system("cls")

        # Header
        self.print_header("Accessibility Project Management - Setup Assistant")

        # OS Detection
        os_name = self.detect_os()
        self.print_success(f"Detected Operating System: {os_name}")

        # Check prerequisites
        self.print_section("Checking Prerequisites")
        prereq = self.check_prerequisites()

        if prereq["python_version"]:
            self.print_info(f"Python Version: {prereq['python_version']}")
            if prereq["python_ok"]:
                self.print_success("Python version is sufficient (≥ 3.12)")
            else:
                self.print_error("Python version is too old! Requires Python 3.12+")
        else:
            self.print_error("Python not found!")

        if prereq["uv_installed"]:
            self.print_success("uv package manager is installed")
        else:
            self.print_warning("uv package manager not found")
            print("  Install uv from: https://github.com/astral-sh/uv")

        if not prereq["all_ok"]:
            self.print_warning("\n  ⚠ Some prerequisites are missing!")
            if not self.ask_yes_no("  Continue with setup anyway?", default=True):
                print("\n  Please install the required prerequisites and run setup again.")
                sys.exit(1)

        # Check if already set up
        if self.secrets_file.exists():
            self.print_warning("  .secrets file already exists!")
            if not self.ask_yes_no("  Overwrite existing .secrets file?", default=False):
                self.print_info("Skipping .secrets creation")
            else:
                self.create_secrets_file()
        else:
            self.create_secrets_file()

        # Setup tools.ini
        self.setup_tools_config()

        # Validate
        validation = self.validate_setup()

        if validation["all_ok"]:
            self.print_success("\n  ✓ Setup completed successfully!")
        else:
            self.print_error("\n  ✗ Setup has issues that need to be resolved")

        # Show next steps
        self.show_next_steps()

        print("\n" + "=" * 70)


def main():
    """Main entry point."""
    try:
        assistant = SetupAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during setup: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
