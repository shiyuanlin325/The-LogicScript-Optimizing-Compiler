# The LogicScript Optimizing Compiler

## 1. Project Overview

This project implements a four-phase optimizing compiler for a custom micro-language called **LogicScript**.

The compiler is designed to:

1. read a LogicScript source file,
2. perform lexical analysis,
3. validate syntax and generate an Abstract Syntax Tree (AST),
4. optimize logical expressions,
5. verify optimization correctness,
6. execute the optimized program,
7. export the full pipeline trace as a JSON file.

The project is based on the specification in **Project 1: The LogicScript Optimizing Compiler**.

---

## 2. Final Submission Format

The final submission is centered on **one main Python file**:

logic_compiler.py

---

## 3.Implementation Pipeline

### (2) Phase 2: Syntax Validation and AST Generation

This phase checks whether the token sequence follows the recursive grammar rules and converts each statement into a nested-list AST.

Examples:

(NOT p) → ["NOT", "VAR_P"]  <br>
(p AND q) → ["AND", "VAR_P", "VAR_Q"] <br>
let x = (p OR T) → ["LET", "VAR_X", ["OR", "VAR_P", "TRUE"]]

If the token order is invalid, if parentheses are mismatched, or if required structure is missing, the compiler stops and records a Phase 2 error.

The parser is divided into several focused functions:
* **is_variable**: Return whether a token is a valid variable token.
* **run_parser_phase**: Parse tokenized lines into AST records.
* **parse_line**: Parse one full line and ensure no extra tokens remain.
* **parse_statement**: Parse a statement starting at index.
* **parse_let_statement**:Parse: LET VAR_X EQ expression
* **parse_if_statement**:Parse: IF expression THEN statement
* **parse_print_statement**: Parse: PRINT VAR_X
* **parse_expression**: Parse an expression
* **parse_parenthesized_expression**: Parse a parenthesized recursive expression.

This decomposition makes each function responsible for one syntactic rule, reducing ambiguity and helping isolate bugs.

When the function capture any error in the parser phase, it will raise a ParseError which includes the num of error line and a message "phase_2_parser" showing
the stopped phase.
