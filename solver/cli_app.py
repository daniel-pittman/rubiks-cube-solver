#!/usr/bin/env python3
"""
Compatibility module for the old CLI app location.

The actual CLI implementation has been moved to solver/cli/cli_app.py
This file provides backward compatibility.
"""

from solver.cli.cli_app import main

if __name__ == "__main__":
    print("Note: CLI has been moved to solver.cli module")
    print("Use 'python -m solver.cli' or run_app.sh for the best experience")
    print()
    main()
