#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv

if python3 -c 'import sys; raise SystemExit(sys.version_info[:2] < (3, 14))'; then
    echo "warning: cocotb 2.0.1 does not officially support Python 3.14+; using its compatibility override"
    export COCOTB_IGNORE_PYTHON_REQUIRES=1
fi

.venv/bin/pip install --requirement requirements.txt
