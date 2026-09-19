import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def check_results(path: Path) -> tuple[int, list[str]]:
    root = ET.parse(path).getroot()
    testcases = root.findall(".//testcase")
    failures = []
    for testcase in testcases:
        failure = testcase.find("failure")
        error = testcase.find("error")
        if failure is not None or error is not None:
            detail = failure if failure is not None else error
            name = testcase.attrib.get("name", "unnamed")
            message = detail.attrib.get("message", "failed") if detail is not None else "failed"
            failures.append(f"{name}: {message}")
    return len(testcases), failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail on cocotb JUnit failures")
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    if not args.results.is_file():
        print(f"error: missing cocotb results: {args.results}", file=sys.stderr)
        return 1

    test_count, failures = check_results(args.results)
    if test_count == 0:
        print(f"error: no cocotb tests recorded in {args.results}", file=sys.stderr)
        return 1
    if failures:
        print(f"error: {len(failures)}/{test_count} cocotb tests failed", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"cocotb results: {test_count} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
