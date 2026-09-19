import json
import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

from programs import PROGRAMS, ProgramSpec
from reference_model import Retirement
from scoreboard import RetirementScoreboard


def _retirement_from_dut(dut) -> Retirement:
    return Retirement(
        pc=int(dut.retire_pc_o.value),
        instruction=int(dut.retire_insn_o.value),
        rd_write=bool(dut.retire_rd_we_o.value),
        rd=int(dut.retire_rd_o.value),
        rd_value=int(dut.retire_rd_data_o.value),
        memory_valid=bool(dut.retire_mem_valid_o.value),
        memory_write=bool(dut.retire_mem_we_o.value),
        memory_address=int(dut.retire_mem_addr_o.value),
        memory_write_data=int(dut.retire_mem_wdata_o.value),
        trap=bool(dut.retire_trap_o.value),
    )


async def _run_program(dut, spec: ProgramSpec) -> None:
    program_dir = Path(os.environ["PROGRAM_DIR"])
    artifact_dir = Path(os.environ["ARTIFACT_DIR"])
    failure_path = artifact_dir / f"{spec.name}-mismatch.json"
    failure_path.unlink(missing_ok=True)
    program = spec.load(program_dir)
    scoreboard = RetirementScoreboard(program)
    dut_memory: dict[int, int] = {}

    try:
        cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
        dut.rst_n.value = 0
        dut.imem_rdata_i.value = 0
        dut.imem_valid_i.value = 0
        dut.dmem_rdata_i.value = 0
        dut.dmem_valid_i.value = 0

        for _ in range(2):
            await RisingEdge(dut.clk)
            await ReadOnly()
            assert not dut.imem_req_o.value
            assert not dut.dmem_req_o.value
            assert not dut.retire_valid_o.value

        await FallingEdge(dut.clk)
        dut.rst_n.value = 1
        retired = 0
        max_cycles = spec.retirement_count * 4 + 10

        for _ in range(max_cycles):
            await FallingEdge(dut.clk)
            dut.imem_valid_i.value = 0
            dut.dmem_valid_i.value = 0
            dut.imem_rdata_i.value = 0
            dut.dmem_rdata_i.value = 0

            if dut.imem_req_o.value:
                address = int(dut.imem_addr_o.value)
                assert address in program, f"fetch outside {spec.name}: 0x{address:08x}"
                dut.imem_rdata_i.value = program[address]
                dut.imem_valid_i.value = 1

            if dut.dmem_req_o.value:
                address = int(dut.dmem_addr_o.value)
                assert address & 0x3 == 0, f"unaligned DUT access: 0x{address:08x}"
                if dut.dmem_we_o.value:
                    write_strobe = int(dut.dmem_wstrb_o.value)
                    assert write_strobe == 0xF, f"unexpected write strobe 0x{write_strobe:x}"
                    dut_memory[address] = int(dut.dmem_wdata_o.value)
                else:
                    dut.dmem_rdata_i.value = dut_memory.get(address, 0)
                dut.dmem_valid_i.value = 1

            await RisingEdge(dut.clk)
            await ReadOnly()
            if dut.retire_valid_o.value:
                scoreboard.observe(_retirement_from_dut(dut))
                retired += 1
                if retired == spec.retirement_count:
                    for register, value in spec.final_registers.items():
                        assert scoreboard.model.registers[register] == value
                    assert scoreboard.model.data_memory == spec.final_memory
                    assert dut_memory == spec.final_memory
                    return

        raise AssertionError(
            f"timeout: {spec.name} retired {retired}/{spec.retirement_count} instructions"
        )
    except (AssertionError, AttributeError, ValueError) as error:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        failure_path.write_text(
            json.dumps(
                {
                    "program": spec.name,
                    "error": str(error),
                    "model_pc": scoreboard.model.pc,
                    "model_registers": scoreboard.model.registers,
                    "model_memory": scoreboard.model.data_memory,
                    "dut_memory": dut_memory,
                    "retirements": scoreboard.observations,
                },
                indent=2,
            )
            + "\n"
        )
        raise AssertionError(f"{error}; details: {failure_path}") from error


@cocotb.test()
async def directed_arithmetic(dut) -> None:
    await _run_program(dut, PROGRAMS["arithmetic"])


@cocotb.test()
async def directed_logic(dut) -> None:
    await _run_program(dut, PROGRAMS["logic"])


@cocotb.test()
async def directed_memory(dut) -> None:
    await _run_program(dut, PROGRAMS["memory"])


@cocotb.test()
async def directed_branches(dut) -> None:
    await _run_program(dut, PROGRAMS["branches"])


@cocotb.test()
async def directed_jumps(dut) -> None:
    await _run_program(dut, PROGRAMS["jumps"])
