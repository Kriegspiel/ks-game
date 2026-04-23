#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner script for Kriegspiel test suite.

This script provides convenient ways to run different categories of tests:
- All tests (default)
- Unit tests only
- Integration tests only  
- Performance tests only
- Property-based tests only
- Fast tests (excluding slow tests)

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run unit tests only
    python run_tests.py --integration      # Run integration tests only
    python run_tests.py --performance      # Run performance tests only
    python run_tests.py --property         # Run property-based tests only
    python run_tests.py --fast             # Run fast tests (exclude slow ones)
    python run_tests.py --rules            # Run Kriegspiel rule tests only
"""

import argparse
import subprocess
import sys


def run_tests(test_args):
    """Run pytest with the given arguments."""
    cmd = [sys.executable, "-m", "pytest"] + test_args
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def main():
    parser = argparse.ArgumentParser(description="Run Kriegspiel tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--property", action="store_true", help="Run property-based tests only")
    parser.add_argument("--rules", action="store_true", help="Run Kriegspiel rule tests only")
    parser.add_argument("--fast", action="store_true", help="Run fast tests (exclude slow)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Retained for backwards compatibility. Coverage is enabled by default via pyproject.toml.",
    )
    parser.add_argument("--no-coverage", action="store_true", help="Disable the default coverage plugin options")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Extra arguments passed directly to pytest")
    
    args = parser.parse_args()
    
    # Build pytest arguments
    test_args = []
    
    if args.verbose:
        test_args.append("-v")

    if args.coverage and args.no_coverage:
        parser.error("--coverage and --no-coverage cannot be used together")

    if args.no_coverage:
        test_args.append("--no-cov")
    
    # Select test categories
    if args.unit:
        test_args.extend(["-m", "unit"])
    elif args.integration:
        test_args.extend(["-m", "integration"])
    elif args.performance:
        test_args.extend(["-m", "performance"])
    elif args.property:
        test_args.extend(["-m", "property"])
    elif args.rules:
        test_args.extend(["-m", "rules"])
    elif args.fast:
        test_args.extend(["-m", "not slow"])
    
    # Add test directory
    test_args.append("tests/")
    test_args.extend(args.pytest_args)
    
    return run_tests(test_args)


if __name__ == "__main__":
    sys.exit(main())
