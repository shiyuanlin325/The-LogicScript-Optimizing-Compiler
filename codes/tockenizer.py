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

def process_variable_name(name):
    if len(name) == 1 and name.isalpha():
        return "VAR_" + name.upper()
    else:
        return None

def tokenize(codes):
    output = []
    for i, line in enumerate(codes):
        for word in line.split():
            cur = []
            if word in token_map:
                cur.append(token_map[word])
            else:
                var_token = process_variable_name(word)
                if var_token:
                    cur.append(var_token)
                else:
                    output.clear()
                    return [False, i+1]
        output.append({"line": i + 1, "tokens": cur})
    return output