from dataclasses import asdict

try:
    from .reference_model import RV32IReferenceModel, Retirement
except ImportError:
    from reference_model import RV32IReferenceModel, Retirement


class RetirementMismatch(AssertionError):
    """A DUT retirement differed from the independent architectural model."""


class RetirementScoreboard:
    def __init__(self, program: dict[int, int]) -> None:
        self.program = program
        self.model = RV32IReferenceModel()
        self.observations: list[dict[str, object]] = []

    def observe(self, actual: Retirement) -> Retirement:
        expected_instruction = self.program.get(self.model.pc)
        if expected_instruction is None:
            raise RetirementMismatch(
                f"unexpected retirement {len(self.observations)} at "
                f"PC 0x{actual.pc:08x}; model PC 0x{self.model.pc:08x} "
                "has no instruction"
            )

        expected = self.model.step(expected_instruction)
        mismatches = []
        for field_name in Retirement.__dataclass_fields__:
            expected_value = getattr(expected, field_name)
            actual_value = getattr(actual, field_name)
            if actual_value != expected_value:
                if isinstance(expected_value, bool):
                    detail = f"expected {expected_value}, got {actual_value}"
                else:
                    detail = (
                        f"expected 0x{expected_value:08x}, "
                        f"got 0x{actual_value:08x}"
                    )
                mismatches.append(f"  {field_name}: {detail}")

        self.observations.append(
            {
                "index": len(self.observations),
                "expected": asdict(expected),
                "actual": asdict(actual),
                "mismatches": mismatches,
            }
        )
        if mismatches:
            raise RetirementMismatch(
                f"retirement mismatch at index {len(self.observations) - 1}:\n"
                + "\n".join(mismatches)
            )
        return expected
