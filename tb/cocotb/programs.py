from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProgramSpec:
    name: str
    filename: str
    retirement_count: int
    final_registers: dict[int, int]
    final_memory: dict[int, int]

    def load(self, program_dir: Path) -> dict[int, int]:
        words = [
            int(line, 16)
            for line in (program_dir / self.filename).read_text().splitlines()
            if line.strip()
        ]
        return {index * 4: word for index, word in enumerate(words)}


PROGRAMS = {
    "arithmetic": ProgramSpec(
        "arithmetic",
        "m2_arithmetic.hex",
        5,
        {1: 7, 2: 5, 3: 12, 4: 2, 5: 0xFFFF_FFF9},
        {},
    ),
    "logic": ProgramSpec(
        "logic",
        "m2_logic.hex",
        8,
        {
            1: 0x5A,
            2: 0x0F,
            3: 0x0A,
            4: 0x5F,
            5: 0x55,
            6: 0x13,
            7: 0x2A,
            8: 0x5A,
        },
        {},
    ),
    "memory": ProgramSpec(
        "memory",
        "m2_memory.hex",
        4,
        {1: 64, 2: 42, 3: 42},
        {64: 42},
    ),
    "branches": ProgramSpec(
        "branches",
        "m2_branches.hex",
        7,
        {1: 1, 2: 2, 3: 7},
        {},
    ),
    "jumps": ProgramSpec(
        "jumps",
        "m2_jumps.hex",
        5,
        {1: 24, 2: 12, 5: 4, 6: 20, 7: 7},
        {},
    ),
}
