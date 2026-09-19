from pathlib import Path


PROGRAM = Path(__file__).parent / "programs" / "addi_x1_42.hex"


def test_m1_program_is_addi_x1_x0_42() -> None:
    words = [int(line, 16) for line in PROGRAM.read_text().splitlines() if line.strip()]

    assert words == [0x02A00093]
    instruction = words[0]
    assert instruction & 0x7F == 0b0010011
    assert (instruction >> 7) & 0x1F == 1
    assert (instruction >> 12) & 0x7 == 0
    assert (instruction >> 15) & 0x1F == 0
    assert instruction >> 20 == 42
