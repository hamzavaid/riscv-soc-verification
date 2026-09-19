# RISC-V SoC Verification Lab

This repository is an incremental verification lab for a deliberately scoped
RV32I processor. The current M2 baseline checks deterministic arithmetic,
logic, memory, branch, and jump programs against an independent Python
architectural reference model at every retired instruction.

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
make directed           # run the M2 directed scoreboard suite with Icarus
make directed SIM=verilator
make wave               # run Icarus and write artifacts/icarus/rv32i_core.vcd
make wave SIM=verilator # write artifacts/verilator/rv32i_core.fst
make directed-wave      # run the M2 suite and preserve an Icarus VCD
make test               # run Python tests, lint, and both available simulators
make clean              # remove generated output, keeping .venv
```

Waveforms are opt-in, so normal smoke tests and regressions do not create trace
files. `make smoke WAVES=1` is equivalent to `make wave` for the selected
simulator. Use `make directed-wave SIM=verilator` for an M2 FST. On a scoreboard
failure, a field-level diagnostic is printed and a JSON trace is retained under
`artifacts/<simulator>/`. Open a generated trace with GTKWave:

```sh
gtkwave artifacts/icarus/rv32i_core.vcd
gtkwave artifacts/verilator/rv32i_core.fst
```

GTKWave requires a working desktop display; under WSL, use WSLg or another X
server.

Generated build products live under `build/`; test reports live under
`artifacts/`. Hand-authored RTL, testbench code, and program images remain in
their source directories.

## Current scope

M1 established clock/reset, the instruction-memory handshake, and an observable
retirement record. M2 adds the data-memory handshake and supports `ADDI`,
`ANDI`, `ORI`, `XORI`, `ADD`, `SUB`, `AND`, `OR`, `XOR`, word-aligned `LW`/`SW`,
`BEQ`/`BNE`, `JAL`, and `JALR`. The scoreboard compares retired PC,
instruction, destination writeback, memory transaction, and trap status against
the Python model.

This remains a teaching core with a deliberately incomplete RV32I subset.
Random testing, coverage, assertions, formal verification, and ISA compliance
testing are not part of the current milestone.
