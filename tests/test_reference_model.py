from dataclasses import replace
from pathlib import Path

import pytest

from tb.cocotb.programs import PROGRAMS
from tb.cocotb.reference_model import RV32IReferenceModel, UnsupportedInstruction
from tb.cocotb.scoreboard import RetirementMismatch, RetirementScoreboard


PROGRAM_DIR = Path(__file__).parent / "programs"


@pytest.mark.parametrize("program_name", PROGRAMS)
def test_reference_model_known_answer_programs(program_name: str) -> None:
    spec = PROGRAMS[program_name]
    program = spec.load(PROGRAM_DIR)
    model = RV32IReferenceModel()

    for _ in range(spec.retirement_count):
        model.step(program[model.pc])

    for register, expected in spec.final_registers.items():
        assert model.registers[register] == expected
    assert model.registers[0] == 0
    assert model.data_memory == spec.final_memory


def test_reference_model_rejects_unsupported_instruction() -> None:
    model = RV32IReferenceModel()

    with pytest.raises(UnsupportedInstruction, match="unsupported instruction"):
        model.step(0xFFFF_FFFF)

    assert model.pc == 0
    assert model.registers == [0] * 32


def test_scoreboard_reports_field_level_mismatch() -> None:
    instruction = 0x00700093  # ADDI x1, x0, 7
    scoreboard = RetirementScoreboard({0: instruction})
    expected = RV32IReferenceModel().step(instruction)

    with pytest.raises(RetirementMismatch, match="rd_value") as mismatch:
        scoreboard.observe(replace(expected, rd_value=8))

    assert "expected 0x00000007, got 0x00000008" in str(mismatch.value)
