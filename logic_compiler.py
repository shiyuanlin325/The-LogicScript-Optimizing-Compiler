from __future__ import annotations
import copy
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

TOKEN_MAP = {
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
						if buf in TOKEN_MAP:
							cur.append(TOKEN_MAP[buf])
						else:
							var_token = process_variable_name(buf)
							if var_token:
								cur.append(var_token)
							else:
								raise LexicalError(i + 1, message = f"Lexical error: Invalid token '{buf}'")
						buf = ""
					cur.append(TOKEN_MAP[ch])
				else:
					buf += ch
			if buf:
				if buf in TOKEN_MAP:
					cur.append(TOKEN_MAP[buf])
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
		tokens = item["token"]
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
		original_ast = copy.deepcopy(item["ast"])
		working_ast = copy.deepcopy(item["ast"])

		optimized_ast = optimize_ast(working_ast, line_number)

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
	"""Optimize one parsed AST node.

	Recursion is centralized in this function and its helpers.
	Rule functions only rewrite the current node.
	"""
	return _optimize_node(ast)


def _optimize_node(node):
	"""Optimize statements and expressions with a single traversal."""
	if not isinstance(node, list) or not node:
		return node	

	tag = node[0]

	if tag == "LET" and len(node) == 3:
		return ["LET", node[1], _optimize_expression_recursively(node[2])]

	if tag == "IF" and len(node) == 3:
		condition = _optimize_expression_recursively(node[1])
		statement = _optimize_node(node[2])
		return ["IF", condition, statement]

	if tag == "PRINT" and len(node) == 2:
		return node

	return _optimize_expression_recursively(node)

def _optimize_expression_recursively(node: list):

	if not isinstance(node, list) or not node:
		return node
	
	for i in range(len(node)):
		if isinstance(node[i], list):
			node[i] = _optimize_expression_recursively(node[i])
	
	return _optimize_expression(node)

def _optimize_expression(expr):
	"""Optimize expression nodes bottom-up until no more optimizations apply.
	(Maximum 64 iterations to prevent stack overflow from infinite loops.)
	"""
	if not isinstance(expr, list) or not expr:
		return expr

	rules = [
		(_implication_elimination, True), # Applied first to prevent missing optimization opportunities
		(_de_morgan_law, True),
		(_double_negative_law, False),
		(_consensus_theorem, False),
		(_normalization_optimization, False),
		(_idempotent_law, False),
		(_identity_law, False),
		(_negation_law, False),
		(_universal_bound_law, False),
		(_absorption_law, False),
		(_negation_of_true_false, False),
	]

	max_iterations = 64
	for _ in range(max_iterations): # To ensure no stack overflow
		changed = False

		for rule_fn, is_expanding in rules:
			before = copy.deepcopy(expr)
			rule_result = rule_fn(expr)
			if rule_result is not None:
				expr = rule_result

			if expr != before:
				changed = True
				if is_expanding:
					expr = _optimize_expression_recursively(expr)

		if not changed:
			break

	return expr

# The following are the individual optimization rules. 
# Each takes an expression node and returns a new optimized node if applicable, or None if no optimization applies.
def _implication_elimination(expr):
	"""Apply the implication elimination rule: x IMPLIES y  ===>  (NOT x) OR y"""
	if isinstance(expr, list) and len(expr) == 3 and expr[0] == "IMPLIES":
		return ["OR", ["NOT", expr[1]], expr[2]]
	return None

def _double_negative_law(expr):
	"""Apply the double negative law: NOT (NOT x)  ===>  x"""
	if isinstance(expr, list) and len(expr) == 2 and expr[0] == "NOT":
		subexpr = expr[1]
		if isinstance(subexpr, list) and len(subexpr) == 2 and subexpr[0] == "NOT":
			return subexpr[1]
	return None

def _is_negation_pair(left, right) -> bool:
	"""Return whether two expressions are complements of each other."""
	if isinstance(left, list) and len(left) == 2 and left[0] == "NOT" and left[1] == right:
		return True
	if isinstance(right, list) and len(right) == 2 and right[0] == "NOT" and right[1] == left:
		return True
	return False

def _idempotent_law(expr):
	"""Apply idempotent laws: x AND x => x, x OR x => x."""
	if isinstance(expr, list) and len(expr) == 3 and expr[0] in ("AND", "OR"):
		if expr[1] == expr[2]:
			return expr[1]
	return None

def _identity_law(expr):
	"""Apply identity laws: x AND TRUE => x, x OR FALSE => x."""
	if isinstance(expr, list) and len(expr) == 3:
		op, left, right = expr[0], expr[1], expr[2]
		if op == "AND":
			if left == "TRUE":
				return right
			if right == "TRUE":
				return left
		if op == "OR":
			if left == "FALSE":
				return right
			if right == "FALSE":
				return left
	return None

def _negation_law(expr):
	"""Apply complement laws: x AND NOT x => FALSE, x OR NOT x => TRUE."""
	if isinstance(expr, list) and len(expr) == 3:
		op, left, right = expr[0], expr[1], expr[2]
		if _is_negation_pair(left, right):
			if op == "AND":
				return "FALSE"
			if op == "OR":
				return "TRUE"
	return None

def _universal_bound_law(expr):
	"""Apply bound laws: x AND FALSE => FALSE, x OR TRUE => TRUE."""
	if isinstance(expr, list) and len(expr) == 3:
		op, left, right = expr[0], expr[1], expr[2]
		if op == "AND" and (left == "FALSE" or right == "FALSE"):
			return "FALSE"
		if op == "OR" and (left == "TRUE" or right == "TRUE"):
			return "TRUE"
	return None

def _absorption_law(expr):
	"""Apply absorption laws."""
	if not (isinstance(expr, list) and len(expr) == 3):
		return None

	op, left, right = expr[0], expr[1], expr[2]

	if op == "OR":
		if isinstance(right, list) and len(right) == 3 and right[0] == "AND":
			if right[1] == left or right[2] == left:
				return left
		if isinstance(left, list) and len(left) == 3 and left[0] == "AND":
			if left[1] == right or left[2] == right:
				return right

	if op == "AND":
		if isinstance(right, list) and len(right) == 3 and right[0] == "OR":
			if right[1] == left or right[2] == left:
				return left
		if isinstance(left, list) and len(left) == 3 and left[0] == "OR":
			if left[1] == right or left[2] == right:
				return right

	return None

# This part is an exploration using consensus theorem, which is beyond the basic rules taught in class. 
def _consensus_theorem(expr):
	"""Apply consensus theorem and its dual form.

	SOP form: (x AND y) OR ((NOT x) AND z) OR (y AND z) => (x AND y) OR ((NOT x) AND z)
	POS dual: (x OR y) AND ((NOT x) OR z) AND (y OR z) => (x OR y) AND ((NOT x) OR z)
	"""
	if not (isinstance(expr, list) and len(expr) == 3 and expr[0] in ("OR", "AND")):
		return None

	op = expr[0]
	if op == "OR":
		groups = []

		def _collect_or_terms(node):
			if isinstance(node, list) and len(node) == 3 and node[0] == "OR":
				_collect_or_terms(node[1])
				_collect_or_terms(node[2])
			else:
				groups.append(node)

		_collect_or_terms(expr)
		for i in range(len(groups)):
			for j in range(len(groups)):
				if i == j:
					continue
				left = groups[i]
				right = groups[j]
				if not (
					isinstance(left, list) and len(left) == 3 and left[0] == "AND" and
					isinstance(right, list) and len(right) == 3 and right[0] == "AND"
				):
					continue

				left_terms = [left[1], left[2]]
				right_terms = [right[1], right[2]]

				for a in left_terms:
					for b in right_terms:
						if _is_negation_pair(a, b):
							y_candidates = [t for t in left_terms if t != a]
							z_candidates = [t for t in right_terms if t != b]
							if not y_candidates or not z_candidates:
								continue
							y = y_candidates[0]
							z = z_candidates[0]
							consensus_term = ["AND", y, z]
							if consensus_term in groups:
								new_terms = [t for t in groups if t != consensus_term]
								if len(new_terms) == 1:
									return new_terms[0]
								return _build_binary_expression("OR", new_terms)

	if op == "AND":
		groups = []

		def _collect_and_terms(node):
			if isinstance(node, list) and len(node) == 3 and node[0] == "AND":
				_collect_and_terms(node[1])
				_collect_and_terms(node[2])
			else:
				groups.append(node)

		_collect_and_terms(expr)
		for i in range(len(groups)):
			for j in range(len(groups)):
				if i == j:
					continue
				left = groups[i]
				right = groups[j]
				if not (
					isinstance(left, list) and len(left) == 3 and left[0] == "OR" and
					isinstance(right, list) and len(right) == 3 and right[0] == "OR"
				):
					continue

				left_terms = [left[1], left[2]]
				right_terms = [right[1], right[2]]

				for a in left_terms:
					for b in right_terms:
						if _is_negation_pair(a, b):
							y_candidates = [t for t in left_terms if t != a]
							z_candidates = [t for t in right_terms if t != b]
							if not y_candidates or not z_candidates:
								continue
							y = y_candidates[0]
							z = z_candidates[0]
							consensus_term = ["OR", y, z]
							if consensus_term in groups:
								new_terms = [t for t in groups if t != consensus_term]
								if len(new_terms) == 1:
									return new_terms[0]
								return _build_binary_expression("AND", new_terms)

	return None

def _negation_of_true_false(expr):
	"""Apply NOT TRUE/FALSE simplification."""
	if isinstance(expr, list) and len(expr) == 2 and expr[0] == "NOT":
		if expr[1] == "TRUE":
			return "FALSE"
		if expr[1] == "FALSE":
			return "TRUE"
	return None

def _de_morgan_law(expr):
	"""Apply De Morgan laws on NOT over binary operators."""
	if isinstance(expr, list) and len(expr) == 2 and expr[0] == "NOT":
		subexpr = expr[1]
		if isinstance(subexpr, list) and len(subexpr) == 3:
			op, left, right = subexpr[0], subexpr[1], subexpr[2]
			if op == "AND":
				return ["OR", ["NOT", left], ["NOT", right]]
			if op == "OR":
				return ["AND", ["NOT", left], ["NOT", right]]
	return None

def _build_binary_expression(operator: str, terms: list):
	"""Rebuild a binary expression from flattened terms."""
	current = terms[0]
	for term in terms[1:]:
		current = [operator, current, term]
	return current

# Beyond the basic rules taught in class, this is an exploration of normalization by flattening nested expressions and removing duplicates.
# With this optimization, expressions like (A AND (B AND A)) can be simplified to (A AND B) by flattening and removing duplicates,
# which is not covered by the basic rules but can lead to more concise expressions.
def _normalization_optimization(expr):
	"""Flatten nested OR/AND expressions and remove duplicate terms."""
	if not (isinstance(expr, list) and len(expr) == 3 and expr[0] in ("AND", "OR")):
		return None

	operator = expr[0]
	flattened_terms = []

	def _collect_terms(node):
		if isinstance(node, list) and len(node) == 3 and node[0] == operator:
			_collect_terms(node[1])
			_collect_terms(node[2])
		else:
			flattened_terms.append(node)

	_collect_terms(expr)

	unique_terms = []
	for term in flattened_terms:
		if term not in unique_terms:
			unique_terms.append(term)

	if len(unique_terms) == 1:
		return unique_terms[0]

	normalized_expr = _build_binary_expression(operator, unique_terms)
	if normalized_expr != expr and len(unique_terms) < len(flattened_terms):
		return normalized_expr

	return None


# ---------------------------------
# phase4.
# ---------------------------------

def evaluate_ast(ast: object, state: dict[str, str], line_number: int) -> str:
	"""evaluate AST boolean value

	 AST（string+list） state    line_number

	ExecutionError: undefined variable or invalid AST
	"""
	# true/false   VAR
	if isinstance(ast, str):
		if ast in ("TRUE", "FALSE"):
			return ast
		if ast.startswith("VAR_"):
			if ast not in state:
				raise ExecutionError(line_number, f"Execution error: Undefined variable '{ast}'")
			return state[ast]
		raise ExecutionError(line_number, f"Execution error: Invalid AST node '{ast}'")

	#list
	if not isinstance(ast, list) or len(ast) < 2:
		raise ExecutionError(line_number, "Execution error: Invalid compound AST structure")

	operator = ast[0]

	# non-operation
	if operator == "NOT":
		if len(ast) != 2:
			raise ExecutionError(line_number, "Execution error: Invalid NOT operation")
		operand_val = evaluate_ast(ast[1], state, line_number)
		return "FALSE" if operand_val == "TRUE" else "TRUE"

	# AND、OR、IMPLIES
	if operator in ("AND", "OR", "IMPLIES"):
		if len(ast) != 3:
			raise ExecutionError(line_number, f"Execution error: Invalid {operator} operation")
		left_val = evaluate_ast(ast[1], state, line_number)
		right_val = evaluate_ast(ast[2], state, line_number)

		if operator == "AND":
			return "TRUE" if (left_val == "TRUE" and right_val == "TRUE") else "FALSE"
		if operator == "OR":
			return "TRUE" if (left_val == "TRUE" or right_val == "TRUE") else "FALSE"
		if operator == "IMPLIES":
			# 蕴含真值表：T->T=T, T->F=F, F->T=T, F->F=T
			return "FALSE" if (left_val == "TRUE" and right_val == "FALSE") else "TRUE"

	raise ExecutionError(line_number, f"Execution error: Unknown operator '{operator}'")


def extract_variables(ast: object) -> set[str]:
	#extract all variables
	variables = set()

	if isinstance(ast, str):
		if ast.startswith("VAR_"):
			variables.add(ast)
		return variables

	if isinstance(ast, list):
		for node in ast:
			variables.update(extract_variables(node))

	return variables


def verify_equivalence(
	original_ast: list,
	optimized_ast: list,
	line_number: int=0,
) -> dict:
	"""Test whether the original AST and the optimized AST are logically equivalent

	generate 2ⁿ rows truth table，and compare

	original_ast optimized_ast line_number

	Returns a verification dictionary in the required JSON format.。
	"""
	# Extract all unique variables from the two ASTs.
	original_vars = extract_variables(original_ast)
	optimized_vars = extract_variables(optimized_ast)
	all_vars = sorted(original_vars.union(optimized_vars))
	num_vars = len(all_vars)

	ast_original_column = []
	ast_optimized_column = []
	is_equivalent = True

	# generate 2ⁿ rows truth table，and compare
	for i in range(2 ** num_vars-1,-1,-1):
		state = {}
		for j in range(num_vars):
			# Generate TRUE/FALSE values using bitwise operations.
			bit = (i >> (num_vars - 1 - j)) & 1
			state[all_vars[j]] = "TRUE" if bit else "FALSE"

		# calculate two AST
		try:
			orig_result = evaluate_ast(original_ast, state, line_number)
			opt_result = evaluate_ast(optimized_ast, state, line_number)
		except ExecutionError:
			# If the calculation fails during verification, mark it as not equivalent.
			is_equivalent = False
			orig_result = "FALSE"
			opt_result = "TRUE"

		ast_original_column.append(orig_result)
		ast_optimized_column.append(opt_result)

		# test the equivalence
		if orig_result != opt_result:
			is_equivalent = False

	return {
		"line": line_number,
		"variables_tested": all_vars,
		"ast_original_column": ast_original_column,
		"ast_optimized_column": ast_optimized_column,
		"is_equivalent": "TRUE" if is_equivalent else "FALSE",
	}


def execute_statement(
	ast: list,
	state: dict[str, str],
	line_number: int,
) -> Optional[str]:
	"""Execute a single statement AST.

		Returns the output string for a PRINT statement; otherwise, returns None.
	"""
	if not isinstance(ast, list) or len(ast) < 2:
		raise ExecutionError(line_number, "Execution error: Invalid statement AST")

	statement_type = ast[0]

	# LET
	if statement_type == "LET":
		if len(ast) != 3:
			raise ExecutionError(line_number, "Execution error: Invalid LET statement")
		var_token = ast[1]
		if not (isinstance(var_token, str) and var_token.startswith("VAR_")):
			raise ExecutionError(line_number, "Execution error: Invalid variable in LET statement")
		expr_result = evaluate_ast(ast[2], state, line_number)
		state[var_token] = expr_result
		return None

	# IF
	if statement_type == "IF":
		if len(ast) != 3:
			raise ExecutionError(line_number, "Execution error: Invalid IF statement")
		condition_result = evaluate_ast(ast[1], state, line_number)
		if condition_result == "TRUE":
			return execute_statement(ast[2], state, line_number)
		return None

	# PRINT
	if statement_type == "PRINT":
		if len(ast) != 2:
			raise ExecutionError(line_number, "Execution error: Invalid PRINT statement")
		var_token = ast[1]
		if not (isinstance(var_token, str) and var_token.startswith("VAR_")):
			raise ExecutionError(line_number, "Execution error: Invalid variable in LET statement")
		if var_token not in state:
			raise ExecutionError(line_number, f"Execution error: Undefined variable in PRINT statement '{var_token}'")
		return state[var_token]

	raise ExecutionError(line_number, f"Execution error: Unknown statement type '{statement_type}'")


def run_execution_phase(
	optimizer_output: list[dict],
	verifications_seed: list[dict]=[],
) -> dict:
	"""Executes the optimized AST and returns the final Phase 4 structure.


	optimizer_output: A list of optimized AST records from Phase 3.
	verifications_seed: A list of validation metadata from Phase 3.

	return:
		The final Phase 4 dictionary complying with the required JSON format.
	"""
	verifications = []
	final_state_dictionary: dict[str, str] = {}
	printed_output = []

	# Perform equivalence verification on all optimized lines.
	for item in verifications_seed:
		line_number = item["line"]
		original_ast = item["original_ast"]
		optimized_ast = item["optimized_ast"]

		# Extract the expression part from the LET statement for verification.
		# LET AST：["LET", "VAR_X", statement]
		if (isinstance(original_ast, list) and len(original_ast) >= 3 and
				isinstance(optimized_ast, list) and len(optimized_ast) >= 3 and
				original_ast[0] == "LET" and optimized_ast[0] == "LET"):
			verification_result = verify_equivalence(
				original_ast[2],
				optimized_ast[2],
				line_number
			)
		else:
			# for non-let we validate the entire expression.
			verification_result = verify_equivalence(original_ast, optimized_ast, line_number)

		verifications.append(verification_result)

	#  Execute all statements line by line
	for item in optimizer_output:
		line_number = item["line"]
		ast = item["ast"]

		print_result = execute_statement(ast, final_state_dictionary, line_number)

		if print_result is not None:
			printed_output.append({
				"line": line_number,
				"output": print_result,
			})

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