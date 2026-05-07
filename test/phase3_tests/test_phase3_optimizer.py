from __future__ import annotations

from pathlib import Path
import importlib
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

optimizer_module = importlib.import_module("logic_compiler")


def read_source_lines(filename: str) -> list[str]:
    path = TESTS_DIR / filename
    with open(path, "r", encoding="utf-8") as file:
        return file.readlines()
    
OPTIMIZATION_CASES = [
    (
        "phase3_01_double_negative.txt",
        [["LET", "VAR_P", "VAR_Q"]],
    ),
    (
        "phase3_02_implication_elimination.txt",
        [["LET", "VAR_P", ["OR", ["NOT", "VAR_Q"], "VAR_R"]]],
    ),
    (
        "phase3_03_idempotent.txt",
        [["LET", "VAR_P", "VAR_Q"]],
    ),
    (
        "phase3_04_identity.txt",
        [["LET", "VAR_P", "VAR_Q"]],
    ),
    (
        "phase3_05_negation_law.txt",
        [["LET", "VAR_P", "FALSE"]],
    ),
    (
        "phase3_06_universal_bound.txt",
        [["LET", "VAR_P", "TRUE"]],
    ),
    (
        "phase3_07_absorption.txt",
        [["LET", "VAR_P", "VAR_Q"]],
    ),
    (
        "phase3_08_negation_of_true_false.txt",
        [["LET", "VAR_P", "FALSE"]],
    ),
    (
        "phase3_09_de_morgan.txt",
        [["LET", "VAR_P", ["OR", ["NOT", "VAR_Q"], ["NOT", "VAR_R"]]]],
    ),
    (
        "phase3_10_implication_implication_double_negative.txt",
        [[
            "LET",
            "VAR_P",
            [
                "OR",
                ["AND", "VAR_Q", ["NOT", "VAR_R"]],
                ["NOT", "VAR_Q"],
            ],
        ]],
    ),
    (
        "phase3_11_de_morgan_double_negative.txt",
        [["LET", "VAR_P", ["OR", "VAR_Q", ["NOT", "VAR_R"]]]],
    ),
    (
        "phase3_12_multiple_line.txt",
        [
            ["LET", "VAR_P", "TRUE"],
            ["LET", "VAR_Q", "FALSE"],
            ["LET", "VAR_R", ["OR", "VAR_P", ["NOT", "VAR_Q"]]],
            ["IF", "VAR_R", ["PRINT", "VAR_P"]],
        ],
    ),
    (
        "phase3_13_complicated_expression.txt",
        [
            ["LET", "VAR_A", "TRUE"],
            ["LET", "VAR_B", "FALSE"],
            ["LET", "VAR_C", "TRUE"],
            ["IF", "VAR_B", ["PRINT", "VAR_A"]],
        ],
    ),
    (
        "phase3_14_extremely_complicated_expression.txt",
        [
            ["LET", "VAR_A", "TRUE"],
            ["LET", "VAR_B", "FALSE"],
            ["LET", "VAR_C", "TRUE"],
            ["LET", "VAR_D", "VAR_A"],
            [
                "LET",
                "VAR_E",
                [
                    "OR",
                    ["AND", "VAR_A", ["NOT", "VAR_B"]],
                    ["OR", ["NOT", "VAR_C"], ["AND", "VAR_D", "VAR_A"]],
                ],
            ],
            [
                "IF",
                [
                    "OR",
                    ["AND", ["OR", ["NOT", "VAR_A"], ["NOT", "VAR_B"]], "VAR_C"],
                    ["AND", ["OR", ["NOT", "VAR_A"], "VAR_B"], ["OR", "VAR_D", ["NOT", "VAR_B"]]],
                ],
                [
                    "LET",
                    "VAR_Z",
                    [
                        "OR",
                        ["AND", ["OR", ["NOT", "VAR_A"], ["AND", ["NOT", "VAR_B"], ["NOT", "VAR_C"]]], ["OR", "VAR_A", ["NOT", "VAR_C"]]],
                        "VAR_D",
                    ],
                ],
            ],
        ],
    ),
    (
        "phase3_15_normalized_then_idempotent.txt",
        [["LET", "VAR_P", ["OR", "VAR_Q", "VAR_R"]]],
    ),
    (
        "phase3_16_multiple_line.txt",
        [
            ["LET", "VAR_P", "TRUE"],
            ["LET", "VAR_Q", "FALSE"],
            ["LET", "VAR_R", ["OR", "VAR_P", ["NOT", "VAR_Q"]]],
            ["IF", "VAR_R", ["PRINT", "VAR_P"]],
        ],
    ),
    (
        "phase3_17_consensus_theorem.txt",
        [
            [
                "LET",
                "VAR_P",
                [
                    "OR",
                    ["AND", "VAR_A", "VAR_B"],
                    ["AND", ["NOT", "VAR_A"], "VAR_C"],
                ],
            ],
            [
                "LET",
                "VAR_Q",
                [
                    "AND",
                    ["OR", "VAR_A", "VAR_B"],
                    ["OR", ["NOT", "VAR_A"], "VAR_C"],
                ],
            ],
        ],
    ),
]


@pytest.mark.parametrize("filename, expected_tokens", OPTIMIZATION_CASES)
def test_optimization_cases(filename: str, expected_tokens: list[list[str]]) -> None:

    """Test that valid input files are optimized correctly."""

    source_lines = read_source_lines(filename)
    lexer_output = optimizer_module.run_lexer_phase(source_lines)
    parser_output = optimizer_module.run_parser_phase(lexer_output)
    optimized_output, _ = optimizer_module.run_optimizer_phase(parser_output)
    token_list = [item["ast"] for item in optimized_output]
    assert token_list == expected_tokens