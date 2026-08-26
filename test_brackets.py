import sys

def check_brackets(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # We will strip out regex literals to avoid confusing the bracket checker.
    import re
    # Strip line comments
    text = re.sub(r'//.*', '', text)
    # Strip block comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Strip string literals
    text = re.sub(r"'[^']*'", "''", text)
    text = re.sub(r'"[^"]*"', '""', text)
    text = re.sub(r'`[^`]*`', '``', text, flags=re.DOTALL)
    # Strip regex literals like /&/g
    text = re.sub(r'/[^/\n\r]+/[gimuy]*', 'REGEX', text)

    lines = text.split('\n')
    depth = 0
    for i, line in enumerate(lines):
        for char in line:
            if char == '{': depth += 1
            elif char == '}': 
                depth -= 1
                if depth < 0:
                    print(f"Extra '}}' found at line {i+1}")
                    return

    print(f"Final depth: {depth}")

check_brackets('frontend/js/app.js')
