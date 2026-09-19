# RISC-V SoC Verification Lab

This repository is an incremental verification lab for a deliberately scoped
RV32I processor. The current M1 baseline demonstrates one deterministic,
end-to-end path: reset a small SystemVerilog DUT, serve one `ADDI` instruction
from a cocotb memory model, observe retirement, and check the architectural
register result.

This is not an ISA-compliant processor and does not claim RISC-V compliance.

## Prerequisites

- Linux or WSL2
- Python 3.10-3.13 with `venv` (Python 3.14 uses cocotb's unsupported
  compatibility override and is checked locally on a best-effort basis)
- GNU Make
- Icarus Verilog and/or Verilator

On Ubuntu/WSL2, install system tools with your normal package manager, then
create the repository-local Python environment:

```sh
make setup
make doctor
```

Open the repository from WSL with `code .`; VS Code will select
`.venv/bin/python`. The included tasks expose setup, doctor, lint, and smoke
commands through **Terminal > Run Task**.

## Commands

```sh
make doctor             # report required tool and Python dependency status
make lint               # lint Python and compile-check SystemVerilog
make smoke              # run the M1 cocotb test with Icarus
make smoke SIM=verilator
make test               # run Python tests, lint, and both available simulators
make clean              # remove generated output, keeping .venv
```

Generated build products live under `build/`; test reports live under
`artifacts/`. Hand-authored RTL, testbench code, and program images remain in
their source directories.

## Current scope

M0 freezes the first increment to RV32I `ADDI` only. M1 provides clock/reset,
a minimal instruction-memory request/valid interface, a single-instruction
memory model, and observable retirement data. Broader directed instruction
testing, a reference-model scoreboard, random testing, coverage, assertions,
and formal verification are later milestones.
