#!/usr/bin/env bash
set -uo pipefail

status=0

check_command() {
    local command_name="$1"
    if command -v "${command_name}" >/dev/null 2>&1; then
        printf 'ok      %-14s %s\n' "${command_name}" "$(command -v "${command_name}")"
    else
        printf 'missing %-14s required\n' "${command_name}"
        status=1
    fi
}

check_command python3
check_command make
check_command iverilog
check_command verilator

if [[ -x .venv/bin/python ]]; then
    printf 'ok      %-14s %s\n' '.venv' "$(.venv/bin/python --version 2>&1)"
    if .venv/bin/python -c 'import sys; raise SystemExit(sys.version_info[:2] < (3, 14))'; then
        printf 'warning %-14s cocotb support ends at Python 3.13\n' 'Python version'
    fi
    if .venv/bin/python -c 'import cocotb, pytest' >/dev/null 2>&1; then
        printf 'ok      %-14s cocotb and pytest import successfully\n' 'Python deps'
    else
        printf 'missing %-14s run make setup\n' 'Python deps'
        status=1
    fi
else
    printf 'missing %-14s run make setup\n' '.venv'
    status=1
fi

exit "${status}"
