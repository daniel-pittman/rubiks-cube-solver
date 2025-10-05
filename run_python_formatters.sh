#!/bin/bash
#
# Python Code Formatter and Linter Script
#
# Purpose: Runs all code quality tools (formatters and linters) on the project
# Usage: ./run_python_formatters.sh
#
# This script executes the following tools in order:
# 1. Black - Auto-formats code to PEP 8 style
# 2. Autoflake - Removes unused imports and variables
# 3. Isort - Organizes import statements
# 4. Pylint - Static analysis (must score ≥9.0/10.0)
#
# Exit codes:
# - 0: All checks passed
# - 1: Pylint score below threshold or other error
#
# Note: This script is also called by pre-commit hooks automatically

# Exit if any command fails, except pylint (we'll handle pylint separately)
set -e

# Turn on command echo for debugging (shows each command being executed)
set -x

# Define the list of directories to process (space-separated)
# Add more directories here as the project grows
directories="solver/"

# ============================================================
# FORMATTING PHASE: Auto-fix code style issues
# ============================================================

# Loop through each directory and apply the formatting tools
for dir in $directories; do
    echo "Processing directory: $dir"

    # Black: Opinionated Python formatter
    # Automatically reformats code to match PEP 8 style guide
    black "$dir"

    # Autoflake: Remove unused imports and variables
    # Cleans up dead code that accumulates during development
    autoflake --in-place --remove-unused-variables --remove-all-unused-imports --recursive "$dir"

    # Isort: Import statement organizer
    # Sorts imports alphabetically and groups them by type (stdlib, third-party, local)
    # Must use --profile=black to be compatible with Black's formatting
    isort --profile=black "$dir"

    echo "Finished processing directory: $dir"
done

# ============================================================
# LINTING PHASE: Static analysis and quality checks
# ============================================================

# Disable 'set -e' to handle pylint errors manually
# We want to collect results from all directories even if one fails
set +e

# Run pylint and capture the exit code
pylint_exit_code=0

set +x  # Disable command echo for cleaner output


for dir in $directories; do
    echo "Running pylint for directory: $dir"

    # Run pylint with custom message template for easier parsing
    # --msg-template: Custom format showing file:line,col: message
    # --fail-under=9: Exit with error if score is below 9.0/10.0
    pylint_output=$(pylint "$dir" --msg-template='{msg_id}:{path}:{line},{column}: {msg} ({symbol})' --fail-under=9)
    pylint_status=${PIPESTATUS[0]}  # Capture pylint's exit code (before piping)

    # Capture the last line which contains the pylint score
    pylint_score=$(echo "$pylint_output" | tail -n 1)

    # Custom sort: Organize output by file path, then severity, then line number
    # Severity order: Fatal > Error > Warning > Refactor > Convention
    # This makes it easier to see issues grouped by file and importance
    echo "$pylint_output" \
      | grep -E '^[CREFW]' \
      | sed -e 's/^C/1C/' -e 's/^R/2R/' -e 's/^W/3W/' -e 's/^E/4E/' -e 's/^F/5F/' \
      | sort -t':' -k2,2 -k1,1 -k1.2n -k3,3n \
      | sed -e 's/^1C/C/' -e 's/^2R/R/' -e 's/^3W/W/' -e 's/^4E/E/' -e 's/^5F/F/'

    # Print the pylint score (last line of the original output)
    # Example: "Your code has been rated at 9.07/10"
    echo "$pylint_score"

    # Track if any pylint run fails
    if [ "$pylint_status" -ne 0 ]; then
        pylint_exit_code=1
        echo "Pylint failed for directory: $dir"
    fi
done

set -x  # Re-enable command echo

# Re-enable 'set -e' to catch other errors
set -e

# Final exit status based on pylint results
if [ $pylint_exit_code -ne 0 ]; then
    echo "Some pylint checks failed"
    exit 1
else
    echo "All pylint checks passed"
    exit 0
fi
