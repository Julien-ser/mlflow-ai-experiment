#!/usr/bin/env python3
"""
Environment verification script for mlflow-ai-experiment project.
Checks that all core dependencies are installed and properly configured.
"""

import sys
import importlib
from packaging import version


def check_package(package_name, min_version=None):
    """Check if a package is installed and meets minimum version requirement."""
    try:
        module = importlib.import_module(package_name.replace("-", "_"))
        installed_version = getattr(module, "__version__", "unknown")
        if min_version and installed_version != "unknown":
            if version.parse(installed_version) < version.parse(min_version):
                print(
                    f"❌ {package_name}: {installed_version} (required: >={min_version})"
                )
                return False
        print(f"✓ {package_name}: {installed_version}")
        return True
    except ImportError as e:
        print(f"❌ {package_name}: Not installed - {e}")
        return False


def main():
    print("=" * 60)
    print("MLFlow AI Experiment - Environment Verification")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print("-" * 60)

    packages_to_check = [
        ("numpy", "1.24.0"),
        ("pandas", "2.0.0"),
        ("sklearn", "1.3.0"),
        ("mlflow", "2.8.0"),
        ("transformers", "4.35.0"),
        ("datasets", "2.14.0"),
        ("torch", "2.0.0"),
        ("xgboost", "1.7.0"),
        ("lightgbm", "4.0.0"),
        ("optuna", "3.3.0"),
    ]

    all_ok = True
    for package, min_ver in packages_to_check:
        if not check_package(package, min_ver):
            all_ok = False

    print("-" * 60)
    if all_ok:
        print("✓ All core dependencies are installed correctly!")
        print("\nNext steps:")
        print("  1. Run: mlflow ui")
        print("  2. Start with notebooks/01_data_exploration.ipynb")
        return 0
    else:
        print("❌ Some dependencies are missing or outdated.")
        print("\nPlease install missing packages:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
