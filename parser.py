from __future__ import annotations
import json
import sys
from typing import Optional


"""
For error.
"""

class CompilerError(Exception):
	"""Base class for compiler pipeline errors."""

	def __init__(self, phase: str, line: int, message: str) -> None:
		super().__init__(message)
		self.phase = phase
		self.line = line
		self.message = message


class LexicalError(CompilerError):
	"""Raised when lexical analysis fails."""

	def __init__(self, line: int, message: str = "Lexical error") -> None:
		super().__init__("phase_1_lexer", line, message)


class ParseError(CompilerError):
	"""Raised when syntax validation fails."""

	def __init__(self, line: int, message: str = "Syntax error") -> None:
		super().__init__("phase_2_parser", line, message)


class OptimizationError(CompilerError):
	"""Raised when optimization fails."""

	def __init__(self, line: int, message: str = "Optimization error") -> None:
		super().__init__("phase_3_optimizer", line, message)


class ExecutionError(CompilerError):
	"""Raised when execution fails."""

	def __init__(self, line: int, message: str = "Execution error") -> None:
		super().__init__("phase_4_execution", line, message)


def build_error_payload(error: CompilerError) -> dict:
	"""Convert a compiler error into the required JSON error object."""
	return {
		"phase": error.phase,
		"line": error.line,
	}


"""
For io.
"""

def read_source_file(input_filename: str) -> list[str]:
	"""Read source lines from the input file."""
	with open(input_filename, "r") as file:
		return file.readlines()


def write_output_file(output_filename: str, result: dict) -> None:
	"""Write the final pipeline result to JSON."""
	with open(output_filename, "w") as out_file:
		json.dump(result, out_file, indent=2)


"""
For the detailed 4 phases.
"""
# --------------------------
# Phase 1: Lexical Analysis
# --------------------------

# Example input
# let p = T
# let q = F
# let r = (NOT ((NOT p) AND q))
# if r then print p

token_map = {
	"let": "LET",
	"if": "IF",
	"then": "THEN",
	"print": "PRINT",
	"T": "TRUE",
	"F": "FALSE",
	"AND": "AND",
	"OR": "OR",
	"NOT": "NOT",
	"IMPLIES": "IMPLIES",
	"=": "EQ",
	"(": "L_PAREN",
	")": "R_PAREN"
}

def process_variable_name(name: str) -> Optional[str]:

	"""Used for mapping variable names to tokens.
	Only single-letter variables are allowed."""

	if len(name) == 1 and name.isalpha() and name.islower():
		return "VAR_" + name.upper()
	else:
		return None

def run_lexer_phase(codes: list[str]) -> list[dict]:

	"""Tokenizes the input code lines into a list of dictionaries containing line numbers and tokens.
	If a lexical error is encountered, raise a LexicalError."""

	output = []
	for i, line in enumerate(codes):
		cur = []  # Token list for the current line
		for word in line.split():
			buf = ""  # Buffer to hold the current word being processed
			for ch in word:
				if ch in ("(", ")"):
					if buf:
						if buf in token_map:
							cur.append(token_map[buf])
						else:
							var_token = process_variable_name(buf)
							if var_token:
								cur.append(var_token)
							else:
								raise LexicalError(i + 1, message = f"Lexical error: Invalid token '{buf}'")
						buf = ""
					cur.append(token_map[ch])
				else:
					buf += ch
			if buf:
				if buf in token_map:
					cur.append(token_map[buf])
				else:
					var_token = process_variable_name(buf)
					if var_token:
						cur.append(var_token)
					else:
						raise LexicalError(i + 1, message = f"Lexical error: Invalid token '{buf}'")
		output.append({"line": i + 1, "token": cur})
	return output

# Example output
# {'line': 1, 'token': ['LET', 'VAR_P', 'EQ', 'TRUE']}
# {'line': 2, 'token': ['LET', 'VAR_Q', 'EQ', 'FALSE']}
# {'line': 3, 'token': ['LET', 'VAR_R', 'EQ', 'L_PAREN', 'NOT', 'L_PAREN', 'L_PAREN', 'NOT', 'VAR_P', 'R_PAREN', 'AND', 'VAR_Q', 'R_PAREN', 'R_PAREN']}
# {'line': 4, 'token': ['IF', 'VAR_R', 'THEN', 'PRINT', 'VAR_P']}

# -------------------------------------------
# Phase 2: Syntax Validation & AST Generation
# -------------------------------------------

BASE_EXPRESSIONS = {"TRUE", "FALSE"}
BINARY_OPERATORS = {"AND", "OR", "IMPLIES"}


def is_variable(token: str) -> bool:
	"""Return whether a token is a valid variable token."""
	return token.startswith("VAR_") and len(token) == 5 and token[-1].isalpha()


def run_parser_phase(lexer_output: list[dict]) -> list[dict]:

	"""Parse tokenized lines into AST records."""

	phase_output = []

	for item in lexer_output:
		line_number = item["line"]
		tokens = item["tokens"]
		ast = parse_line(tokens, line_number)

		phase_output.append({
			"line": line_number,
			"ast": ast,
		})

	return phase_output


def parse_line(tokens: list[str], line_number: int) -> list:
	"""Parse one full line and ensure no extra tokens remain."""
	ast, next_index = parse_statement(tokens, 0, line_number)
	if next_index != len(tokens):
		raise ParseError(line_number, "Unexpected extra tokens")
	return ast


def parse_statement(
    tokens: list[str],
    index: int,
    line_number: int,
) -> tuple[list, int]:
    """Parse a statement starting at index."""
    if index >= len(tokens):
        raise ParseError(line_number, "Missing statement")

    token = tokens[index]

    if token == "LET":
        return parse_let_statement(tokens, index, line_number)

    if token == "IF":
        return parse_if_statement(tokens, index, line_number)

    if token == "PRINT":
        return parse_print_statement(tokens, index, line_number)

    raise ParseError(line_number, f"Invalid statement start: {token}")


def parse_let_statement(
    tokens: list[str],
    index: int,
    line_number: int,
) -> tuple[list, int]:
    """Parse: LET VAR_X EQ expression"""
    if index + 2 >= len(tokens):
        raise ParseError(line_number, "Incomplete LET statement")

    if tokens[index] != "LET":
        raise ParseError(line_number, "Expected LET")

    variable_token = tokens[index + 1]
    eq_token = tokens[index + 2]

    if not is_variable(variable_token):
        raise ParseError(line_number, "LET must be followed by a variable")

    if eq_token != "EQ":
        raise ParseError(line_number, "Missing EQ in LET statement")

    expr_ast, next_index = parse_expression(tokens, index + 3, line_number)

    return ["LET", variable_token, expr_ast], next_index


def parse_if_statement(
    tokens: list[str],
    index: int,
    line_number: int,
) -> tuple[list, int]:
    """Parse: IF expression THEN statement"""
    if tokens[index] != "IF":
        raise ParseError(line_number, "Expected IF")

    condition_ast, next_index = parse_expression(tokens, index + 1, line_number)

    if next_index >= len(tokens) or tokens[next_index] != "THEN":
        raise ParseError(line_number, "Missing THEN in IF statement")

    statement_ast, final_index = parse_statement(tokens, next_index + 1, line_number)

    return ["IF", condition_ast, statement_ast], final_index


def parse_print_statement(
    tokens: list[str],
    index: int,
    line_number: int,
) -> tuple[list, int]:
    """Parse: PRINT VAR_X"""
    if index + 1 >= len(tokens):
        raise ParseError(line_number, "Incomplete PRINT statement")

    if tokens[index] != "PRINT":
        raise ParseError(line_number, "Expected PRINT")

    variable_token = tokens[index + 1]

    if not is_variable(variable_token):
        raise ParseError(line_number, "PRINT must be followed by a variable")

    return ["PRINT", variable_token], index + 2


def parse_expression(
    tokens: list[str],
    index: int,
    line_number: int,
) -> tuple[object, int]:
    """Parse an expression from tokens[index:]."""
    if index >= len(tokens):
        raise ParseError(line_number, "Missing expression")

    token = tokens[index]

    if token in BASE_EXPRESSIONS or is_variable(token):
        return token, index + 1

    if token != "L_PAREN":
        raise ParseError(line_number, f"Invalid expression token: {token}")

    return parse_parenthesized_expression(tokens, index, line_number)


def parse_parenthesized_expression(
    tokens: list[str],
    index: int,
    line_number: int,
) -> tuple[list, int]:
    """Parse a parenthesized recursive expression."""
    if tokens[index] != "L_PAREN":
        raise ParseError(line_number, "Expected L_PAREN")

    if index + 1 >= len(tokens):
        raise ParseError(line_number, "Incomplete parenthesized expression")

    operator = tokens[index + 1]

    # Unary NOT: (NOT E)
    if operator == "NOT":
        expr_ast, next_index = parse_expression(tokens, index + 2, line_number)

        if next_index >= len(tokens) or tokens[next_index] != "R_PAREN":
            raise ParseError(line_number, "Missing R_PAREN after NOT expression")

        return ["NOT", expr_ast], next_index + 1

    # Binary: (E1 AND E2), (E1 OR E2), (E1 IMPLIES E2)
    left_ast, next_index = parse_expression(tokens, index + 1, line_number)

    if next_index >= len(tokens):
        raise ParseError(line_number, "Missing binary operator")

    operator = tokens[next_index]
    if operator not in BINARY_OPERATORS:
        raise ParseError(line_number, f"Expected binary operator, got {operator}")

    right_ast, next_index = parse_expression(tokens, next_index + 1, line_number)

    if next_index >= len(tokens) or tokens[next_index] != "R_PAREN":
        raise ParseError(line_number, "Missing R_PAREN after binary expression")

    return [operator, left_ast, right_ast], next_index + 1

# ------------------------------
# Phase 3: The Optimization Pass
# ------------------------------

def run_optimizer_phase(parser_output: list[dict]) -> tuple[list[dict], list[dict]]:
	"""Optimize ASTs.

	Returns:
		A tuple:
		- optimized phase output
		- verification metadata for phase 4
	"""
	optimized_output = []
	verifications_seed = []

	for item in parser_output:
		line_number = item["line"]
		original_ast = item["ast"]

		optimized_ast = optimize_ast(original_ast, line_number)

		optimized_output.append({
			"line": line_number,
			"ast": optimized_ast,
		})

		if original_ast != optimized_ast:
			verifications_seed.append({
				"line": line_number,
				"original_ast": original_ast,
				"optimized_ast": optimized_ast,
			})

	return optimized_output, verifications_seed


def optimize_ast(ast: list, line_number: int):
	"""Placeholder optimizer entry.

	Replace with your actual optimizer integration.
	"""
	return ast

# ---------------------------------
# Phase 4: Verification & Execution
# ---------------------------------

def run_execution_phase(
	optimizer_output: list[dict],
	verifications_seed: list[dict],
) -> dict:
	"""Execute the optimized AST and return the final phase-4 structure."""
	verifications = []
	final_state_dictionary: dict[str, str] = {}
	printed_output = []

	# Placeholder verification step
	for item in verifications_seed:
		verifications.append({
			"line": item["line"],
			"variables_tested": [],
			"ast_original_column": [],
			"ast_optimized_column": [],
			"is_equivalent": "TRUE",
		})

	# Placeholder execution step
	# Replace this with real evaluator logic later.

	return {
		"verifications": verifications,
		"final_state_dictionary": final_state_dictionary,
		"printed_output": printed_output,
	}


"""
For the whole compiler execution.
"""

def run_pipeline(source_lines: list[str]) -> dict:
	"""Run the full 4-phase compiler pipeline."""
	result: dict = {}

	try:
		# -------------------------
		# Phase 1: Lexer
		# -------------------------
		lexer_output = run_lexer_phase(source_lines)
		result["phase_1_lexer"] = lexer_output

		# -------------------------
		# Phase 2: Parser
		# -------------------------
		parser_output = run_parser_phase(lexer_output)
		result["phase_2_parser"] = parser_output

		# -------------------------
		# Phase 3: Optimizer
		# -------------------------
		optimizer_output, verifications_seed = run_optimizer_phase(parser_output)
		result["phase_3_optimizer"] = optimizer_output

		# -------------------------
		# Phase 4: Execution
		# -------------------------
		execution_output = run_execution_phase(optimizer_output, verifications_seed)
		result["phase_4_execution"] = execution_output

	except CompilerError as error:
		result["error"] = build_error_payload(error)

	return result


def main() -> None:
	"""Command-line entry point."""
	if len(sys.argv) != 3:
		print("Usage: python logic_compiler.py <input_file> <output_file>")
		sys.exit(1)

	input_filename = sys.argv[1]
	output_filename = sys.argv[2]

	source_lines = read_source_file(input_filename)
	result = run_pipeline(source_lines)
	write_output_file(output_filename, result)


if __name__ == "__main__":
	main()