from __future__ import annotations

from pathlib import Path
import importlib
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

lexer_module = importlib.import_module("logic_compiler")


def read_source_lines(filename: str) -> list[str]:
    path = TESTS_DIR / filename
    with open(path, "r", encoding="utf-8") as file:
        return file.readlines()


VALID_CASES = [
    (
        "phase1_valid_01_single_line.txt",
        [["LET", "VAR_P", "EQ", "TRUE"]],
    ),
    (
        "phase1_valid_02_multiple_line.txt",
        [
            ["LET", "VAR_P", "EQ", "TRUE"],
            ["LET", "VAR_Q", "EQ", "FALSE"],
            [
                "LET",
                "VAR_R",
                "EQ",
                "L_PAREN",
                "NOT",
                "L_PAREN",
                "L_PAREN",
                "NOT",
                "VAR_P",
                "R_PAREN",
                "AND",
                "VAR_Q",
                "R_PAREN",
                "R_PAREN",
            ],
            ["IF", "VAR_R", "THEN", "PRINT", "VAR_P"],
        ],
    ),
]

INVALID_CASES = [
    ("phase1_invalid_01_capital_variable.txt", 1),
    ("phase1_invalid_02_over_length_variable.txt", 1),
    ("phase1_invalid_03_numeric_variable.txt", 1),
    ("phase1_invalid_04_underscore_variable.txt", 1),
    ("phase1_invalid_05_unknown_boolean_literal.txt", 1),
    ("phase1_invalid_06_double_equal.txt", 1),
    ("phase1_invalid_07_invalid_symbol_in_expr.txt", 1),
    ("phase1_invalid_08_error_on_line_2.txt", 2),
]


def test_parser_module_exports() -> None:
    assert hasattr(lexer_module, "run_lexer_phase")
    assert hasattr(lexer_module, "LexicalError")
    assert hasattr(lexer_module, "run_pipeline")

@pytest.mark.parametrize("filename, expected_tokens", VALID_CASES)
def test_valid_cases(filename: str, expected_tokens: list[list[str]]) -> None:

    """Test that valid input files are tokenized correctly."""

    source_lines = read_source_lines(filename)
    lexer_output = lexer_module.run_lexer_phase(source_lines)
    token_list = [item["token"] for item in lexer_output]
    assert token_list == expected_tokens

@pytest.mark.parametrize("filename, error_line", INVALID_CASES)
def test_invalid_cases(filename: str, error_line: int) -> None:

    """Test that invalid input files raise LexicalError at the correct line."""

    source_lines = read_source_lines(filename)

    with pytest.raises(lexer_module.LexicalError) as exc_info:
        lexer_module.run_lexer_phase(source_lines)

    assert exc_info.value.line == error_line
    assert exc_info.value.phase == "phase_1_lexer"