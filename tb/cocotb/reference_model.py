from dataclasses import dataclass


MASK32 = 0xFFFF_FFFF


class UnsupportedInstruction(ValueError):
    """Raised when a program leaves the deliberately scoped M2 subset."""


def _u32(value: int) -> int:
    return value & MASK32


def _sign_extend(value: int, width: int) -> int:
    sign_bit = 1 << (width - 1)
    return (value ^ sign_bit) - sign_bit


@dataclass(frozen=True)
class Retirement:
    pc: int
    instruction: int
    rd_write: bool
    rd: int
    rd_value: int
    memory_valid: bool = False
    memory_write: bool = False
    memory_address: int = 0
    memory_write_data: int = 0
    trap: bool = False


class RV32IReferenceModel:
    """Behavioral RV32I model for the deterministic M2 instruction subset."""

    def __init__(self, data_memory: dict[int, int] | None = None) -> None:
        self.pc = 0
        self.registers = [0] * 32
        self.data_memory = {
            _u32(address): _u32(value)
            for address, value in (data_memory or {}).items()
        }

    def _read_word(self, address: int) -> int:
        if address & 0x3:
            raise ValueError(f"unaligned word read at 0x{address:08x}")
        return self.data_memory.get(address, 0)

    def _write_word(self, address: int, value: int) -> None:
        if address & 0x3:
            raise ValueError(f"unaligned word write at 0x{address:08x}")
        self.data_memory[address] = _u32(value)

    def step(self, instruction: int) -> Retirement:
        instruction = _u32(instruction)
        opcode = instruction & 0x7F
        rd = (instruction >> 7) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rs1 = (instruction >> 15) & 0x1F
        rs2 = (instruction >> 20) & 0x1F
        funct7 = (instruction >> 25) & 0x7F
        current_pc = self.pc
        next_pc = _u32(current_pc + 4)
        rd_write = False
        rd_value = 0
        memory_valid = False
        memory_write = False
        memory_address = 0
        memory_write_data = 0

        if opcode == 0x13 and funct3 in (0x0, 0x4, 0x6, 0x7):
            immediate = _sign_extend(instruction >> 20, 12)
            lhs = self.registers[rs1]
            operations = {
                0x0: lambda: lhs + immediate,
                0x4: lambda: lhs ^ immediate,
                0x6: lambda: lhs | immediate,
                0x7: lambda: lhs & immediate,
            }
            rd_value = _u32(operations[funct3]())
            rd_write = rd != 0
        elif opcode == 0x33 and funct3 in (0x0, 0x4, 0x6, 0x7):
            lhs = self.registers[rs1]
            rhs = self.registers[rs2]
            if funct3 == 0x0 and funct7 == 0x00:
                rd_value = _u32(lhs + rhs)
            elif funct3 == 0x0 and funct7 == 0x20:
                rd_value = _u32(lhs - rhs)
            elif funct3 == 0x4 and funct7 == 0x00:
                rd_value = lhs ^ rhs
            elif funct3 == 0x6 and funct7 == 0x00:
                rd_value = lhs | rhs
            elif funct3 == 0x7 and funct7 == 0x00:
                rd_value = lhs & rhs
            else:
                raise UnsupportedInstruction(f"unsupported OP 0x{instruction:08x}")
            rd_write = rd != 0
        elif opcode == 0x03 and funct3 == 0x2:
            immediate = _sign_extend(instruction >> 20, 12)
            memory_address = _u32(self.registers[rs1] + immediate)
            rd_value = self._read_word(memory_address)
            rd_write = rd != 0
            memory_valid = True
        elif opcode == 0x23 and funct3 == 0x2:
            immediate_bits = ((instruction >> 25) << 5) | ((instruction >> 7) & 0x1F)
            immediate = _sign_extend(immediate_bits, 12)
            memory_address = _u32(self.registers[rs1] + immediate)
            memory_write_data = self.registers[rs2]
            self._write_word(memory_address, memory_write_data)
            memory_valid = True
            memory_write = True
        elif opcode == 0x63 and funct3 in (0x0, 0x1):
            immediate_bits = (
                ((instruction >> 31) & 0x1) << 12
                | ((instruction >> 7) & 0x1) << 11
                | ((instruction >> 25) & 0x3F) << 5
                | ((instruction >> 8) & 0xF) << 1
            )
            immediate = _sign_extend(immediate_bits, 13)
            equal = self.registers[rs1] == self.registers[rs2]
            taken = equal if funct3 == 0x0 else not equal
            if taken:
                next_pc = _u32(current_pc + immediate)
        elif opcode == 0x6F:
            immediate_bits = (
                ((instruction >> 31) & 0x1) << 20
                | ((instruction >> 12) & 0xFF) << 12
                | ((instruction >> 20) & 0x1) << 11
                | ((instruction >> 21) & 0x3FF) << 1
            )
            immediate = _sign_extend(immediate_bits, 21)
            rd_value = next_pc
            rd_write = rd != 0
            next_pc = _u32(current_pc + immediate)
        elif opcode == 0x67 and funct3 == 0x0:
            immediate = _sign_extend(instruction >> 20, 12)
            rd_value = next_pc
            rd_write = rd != 0
            next_pc = _u32(self.registers[rs1] + immediate) & ~0x1
        else:
            raise UnsupportedInstruction(f"unsupported instruction 0x{instruction:08x}")

        if rd_write:
            self.registers[rd] = _u32(rd_value)
        self.registers[0] = 0
        self.pc = next_pc

        return Retirement(
            pc=current_pc,
            instruction=instruction,
            rd_write=rd_write,
            rd=rd,
            rd_value=_u32(rd_value),
            memory_valid=memory_valid,
            memory_write=memory_write,
            memory_address=memory_address,
            memory_write_data=_u32(memory_write_data),
        )
