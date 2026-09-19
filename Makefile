SHELL := /bin/bash

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff
COCOTB_CONFIG := $(abspath .venv/bin/cocotb-config)
SIM ?= icarus
WAVES ?= 0
COCOTB_MODULE ?= test_m1_smoke
RESULTS_FILE ?= results.xml

ifeq ($(SIM),verilator)
WAVE_ARTIFACT := artifacts/verilator/rv32i_core.fst
else
WAVE_ARTIFACT := artifacts/$(SIM)/rv32i_core.vcd
endif

.PHONY: setup doctor lint smoke directed wave test clean

setup:
	@./scripts/setup.sh

doctor:
	@./scripts/doctor.sh

lint:
	@test -x $(RUFF) || { echo "error: run 'make setup' first"; exit 1; }
	$(RUFF) check scripts tb tests
	verilator --lint-only --timing -Wall --Wno-fatal rtl/rv32i_core.sv
	iverilog -g2012 -s rv32i_core -t null rtl/rv32i_core.sv

smoke:
	@test -x $(COCOTB_CONFIG) || { echo "error: run 'make setup' first"; exit 1; }
	PATH="$(abspath .venv/bin):$$PATH" $(MAKE) --directory tb/cocotb \
		SIM=$(SIM) \
		PYTHON_BIN=$(abspath $(PYTHON)) \
		COCOTB_CONFIG=$(COCOTB_CONFIG) \
		MODULE=$(COCOTB_MODULE) \
		RESULTS_FILE=$(RESULTS_FILE) \
		TRACE=$(WAVES) \
		RTL_DIR=$(abspath rtl) \
		PROGRAM_DIR=$(abspath tests/programs) \
		BUILD_DIR=$(abspath build/sim/$(SIM)$(if $(filter 1,$(WAVES)),-waves,)) \
		ARTIFACT_DIR=$(abspath artifacts/$(SIM))
	$(PYTHON) scripts/check_results.py artifacts/$(SIM)/$(RESULTS_FILE)

directed:
	$(MAKE) smoke SIM=$(SIM) \
		COCOTB_MODULE=test_m2_directed \
		RESULTS_FILE=directed-results.xml

wave:
	$(RM) $(WAVE_ARTIFACT)
	$(MAKE) smoke SIM=$(SIM) WAVES=1
	@test -s $(WAVE_ARTIFACT) || { echo "error: waveform was not generated: $(WAVE_ARTIFACT)"; exit 1; }
	@echo "waveform: $(WAVE_ARTIFACT)"

test:
	@test -x $(PYTHON) || { echo "error: run 'make setup' first"; exit 1; }
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m pytest -q -p no:cacheprovider
	$(MAKE) lint
	$(MAKE) smoke SIM=icarus
	$(MAKE) directed SIM=icarus
	@if command -v verilator >/dev/null 2>&1; then \
		$(MAKE) smoke SIM=verilator && $(MAKE) directed SIM=verilator; \
	else \
		echo "note: verilator not found; skipping optional second simulator"; \
	fi

clean:
	rm -rf build artifacts .pytest_cache .ruff_cache
	find scripts tb tests -type d -name __pycache__ -prune -exec rm -rf {} +
