from pathlib import Path


class SingleInstructionMemory:
    """Deterministic, zero-wait-state instruction memory for the M1 smoke test."""

    def __init__(self, program_path: Path) -> None:
        words = [
            int(line, 16)
            for line in program_path.read_text().splitlines()
            if line.strip()
        ]
        if len(words) != 1:
            raise ValueError("M1 memory model requires exactly one instruction")
        self.word = words[0]

    def respond(self, dut) -> None:
        address = int(dut.imem_addr_o.value)
        if address != 0:
            raise AssertionError(f"unexpected instruction address 0x{address:08x}")
        dut.imem_rdata_i.value = self.word
        dut.imem_valid_i.value = 1

    @staticmethod
    def idle(dut) -> None:
        dut.imem_rdata_i.value = 0
        dut.imem_valid_i.value = 0
