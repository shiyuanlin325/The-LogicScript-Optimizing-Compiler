from __future__ import annotations

from pathlib import Path
import importlib
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

parser_module = importlib.import_module("logic_compiler")


def read_source_lines(filename: str) -> list[str]:
    path = TESTS_DIR / filename
    with open(path, "r", encoding="utf-8") as file:
        return file.readlines()


VALID_CASES = [
    (
        "phase2_valid_01_basic_let.txt",
        [["LET", "VAR_P", "TRUE"]],
    ),
    (
        "phase2_valid_02_print.txt",
        [["PRINT", "VAR_P"]],
    ),
    (
        "phase2_valid_03_not_expr.txt",
        [["LET", "VAR_X", ["NOT", "VAR_P"]]],
    ),
    (
        "phase2_valid_04_binary_expr.txt",
        [
            ["LET", "VAR_X", ["AND", "VAR_P", "VAR_Q"]],
            ["LET", "VAR_Y", ["OR", "VAR_P", "FALSE"]],
            ["LET", "VAR_Z", ["IMPLIES", "VAR_P", "VAR_Q"]],
        ],
    ),
    (
        "phase2_valid_05_nested_expr.txt",
        [["LET", "VAR_R", ["NOT", ["AND", ["NOT", "VAR_P"], "VAR_Q"]]]],
    ),
    (
        "phase2_valid_06_if_print.txt",
        [["IF", "VAR_P", ["PRINT", "VAR_Q"]]],
    ),
    (
        "phase2_valid_07_if_let.txt",
        [["IF", "VAR_P", ["LET", "VAR_Q", ["NOT", "VAR_R"]]]],
    ),
    (
        "phase2_valid_08_nested_if.txt",
        [["IF", "VAR_P", ["IF", "VAR_Q", ["PRINT", "VAR_R"]]]],
    ),
    (
        "phase2_valid_09_multiline_program.txt",
        [
            ["LET", "VAR_P", "TRUE"],
            ["LET", "VAR_Q", "FALSE"],
            ["LET", "VAR_R", ["NOT", ["AND", ["NOT", "VAR_P"], "VAR_Q"]]],
            ["IF", "VAR_R", ["PRINT", "VAR_P"]],
        ],
    ),
]


INVALID_CASES = [
    ("phase2_invalid_01_missing_then.txt", 1),
    ("phase2_invalid_02_missing_rhs_binary.txt", 1),
    ("phase2_invalid_03_extra_rparen.txt", 1),
    ("phase2_invalid_04_missing_rparen.txt", 1),
    ("phase2_invalid_05_invalid_then_statement_expr.txt", 1),
    ("phase2_invalid_06_if_after_if.txt", 1),
    ("phase2_invalid_07_print_missing_var.txt", 1),
    ("phase2_invalid_08_let_missing_eq.txt", 1),
    ("phase2_invalid_09_let_missing_expr.txt", 1),
    ("phase2_invalid_10_extra_tokens.txt", 1),
    ("phase2_invalid_11_error_on_line_2.txt", 2),
]


def test_parser_module_exports() -> None:
    assert hasattr(parser_module, "run_lexer_phase")
    assert hasattr(parser_module, "run_parser_phase")
    assert hasattr(parser_module, "ParseError")
    assert hasattr(parser_module, "run_pipeline")


@pytest.mark.parametrize(("filename", "expected_ast"), VALID_CASES)
def test_phase2_valid_cases(filename: str, expected_ast: list) -> None:
    source_lines = read_source_lines(filename)

    lexer_output = parser_module.run_lexer_phase(source_lines)
    parser_output = parser_module.run_parser_phase(lexer_output)

    ast_list = [item["ast"] for item in parser_output]
    assert ast_list == expected_ast


@pytest.mark.parametrize(("filename", "expected_line"), INVALID_CASES)
def test_phase2_invalid_cases(filename: str, expected_line: int) -> None:
    source_lines = read_source_lines(filename)

    lexer_output = parser_module.run_lexer_phase(source_lines)

    with pytest.raises(parser_module.ParseError) as exc_info:
        parser_module.run_parser_phase(lexer_output)

    error = exc_info.value
    assert hasattr(error, "line")
    assert error.line == expected_line
    assert error.phase == "phase_2_parser"


def test_pipeline_success_shape() -> None:
    source_lines = read_source_lines("phase2_valid_09_multiline_program.txt")
    result = parser_module.run_pipeline(source_lines)

    assert "phase_1_lexer" in result
    assert "phase_2_parser" in result
    assert "phase_3_optimizer" in result
    assert "phase_4_execution" in result
    assert "error" not in result

    assert result["phase_2_parser"][0]["line"] == 1
    assert result["phase_2_parser"][1]["line"] == 2
    assert result["phase_2_parser"][2]["line"] == 3
    assert result["phase_2_parser"][3]["line"] == 4


def test_pipeline_phase2_error_shape() -> None:
    source_lines = read_source_lines("phase2_invalid_11_error_on_line_2.txt")
    result = parser_module.run_pipeline(source_lines)

    assert "phase_1_lexer" in result
    assert "error" in result
    assert result["error"]["phase"] == "phase_2_parser"
    assert result["error"]["line"] == 2
    assert "phase_2_parser" not in result


def test_pipeline_phase1_error_shape() -> None:
    source_lines = ["let abc = T\n"]
    result = parser_module.run_pipeline(source_lines)

    assert "error" in result
    assert result["error"]["phase"] == "phase_1_lexer"
    assert result["error"]["line"] == 1