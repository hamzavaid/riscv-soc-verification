import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

from memory import SingleInstructionMemory


@cocotb.test()
async def reset_fetch_and_retire_addi(dut) -> None:
    """Reset, fetch ADDI x1,x0,42, then verify retirement and x1."""
    memory = SingleInstructionMemory(
        Path(os.environ["PROGRAM_DIR"]) / "addi_x1_42.hex"
    )
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    memory.idle(dut)

    for _ in range(2):
        await RisingEdge(dut.clk)
        await ReadOnly()
        assert int(dut.imem_req_o.value) == 0
        assert int(dut.retire_valid_o.value) == 0
        assert int(dut.debug_reg_x1_o.value) == 0

    await FallingEdge(dut.clk)
    dut.rst_n.value = 1
    await Timer(1, unit="ns")
    assert int(dut.imem_req_o.value) == 1
    assert int(dut.imem_addr_o.value) == 0
    memory.respond(dut)

    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.retire_valid_o.value) == 1
    assert int(dut.retire_pc_o.value) == 0
    assert int(dut.retire_insn_o.value) == memory.word
    assert int(dut.retire_rd_we_o.value) == 1
    assert int(dut.retire_rd_o.value) == 1
    assert int(dut.retire_rd_data_o.value) == 42
    assert int(dut.debug_reg_x1_o.value) == 42

    await FallingEdge(dut.clk)
    memory.idle(dut)
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.retire_valid_o.value) == 0
    assert int(dut.imem_req_o.value) == 0
