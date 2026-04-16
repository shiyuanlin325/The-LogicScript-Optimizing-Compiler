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

def process_variable_name(name):
    if len(name) == 1 and name.isalpha():
        return "VAR_" + name.upper()
    else:
        return None

def tokenize(codes):
    output = []
    for i, line in enumerate(codes):
        cur = [] # Token list for the current line
        for word in line.split():
            buf = "" # Buffer to hold the current word being processed
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
                                output.clear()
                                return [False, i+1]
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
                        output.clear()
                        return [False, i + 1]
        output.append({"line": i+1, "token": cur})
    return output

if __name__ == "__main__":
    codes = [
        "let p = T",
        "let q = F",
        "let r = (NOT ((NOT p) AND q))",
        "if r then print p"
    ]
    result = tokenize(codes)
    if result[0] == False:
        print(f"Error at line {result[1]}")
    else:
        for item in result:
            print(item)

# Example output
# {'line': 1, 'token': ['LET', 'VAR_P', 'EQ', 'TRUE']}
# {'line': 2, 'token': ['LET', 'VAR_Q', 'EQ', 'FALSE']}
# {'line': 3, 'token': ['LET', 'VAR_R', 'EQ', 'L_PAREN', 'NOT', 'L_PAREN', 'L_PAREN', 'NOT', 'VAR_P', 'R_PAREN', 'AND', 'VAR_Q', 'R_PAREN', 'R_PAREN']}
# {'line': 4, 'token': ['IF', 'VAR_R', 'THEN', 'PRINT', 'VAR_P']}