# Mercury Compiler v2
import sys
import os
from pathlib import Path
import importlib.util

def compile_source(source_code: str, module_dir: Path = None) -> str:
    """
    Transpile Mercury code to Python code.
    Supports:
    - var x = ...;
    - write(...);
    - userinput(...);
    - use module; -> Python/pip/.py/.mer modules
    - if [condition] (...), else (...), for [...], while [...]
    - func name(args) (...)
    - Semicolons required
    """
    lines = source_code.splitlines()
    processed_lines = []
    indent_level = 0
    module_dir = module_dir or Path('.')

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        # Semicolon enforcement (except block starts or closing parens)
        if not stripped_line.endswith(';') and not stripped_line.endswith('(') and stripped_line not in [')']:
            raise SyntaxError(f"Missing semicolon at end of line:\n{line}")
        if stripped_line.endswith(';'):
            stripped_line = stripped_line[:-1]

        # Variables
        if stripped_line.startswith('var '):
            stripped_line = stripped_line[len('var '):].lstrip()

        # Print/Input
        if 'write(' in stripped_line:
            stripped_line = stripped_line.replace('write(', 'print(')
        if 'userinput(' in stripped_line:
            stripped_line = stripped_line.replace('userinput(', 'input(')

        # Module imports
        if stripped_line.startswith('use '):
            module_name = stripped_line[len('use '):].strip()
            py_file = module_dir / f"{module_name}.py"
            mer_file = module_dir / f"{module_name}.mer"
            if py_file.exists():
                stripped_line = f'import {module_name}'
            elif mer_file.exists():
                # Compile Mercury module to Python temporarily
                mer_source = mer_file.read_text()
                compiled_mer = compile_source(mer_source, module_dir=module_dir)
                tmp_py = module_dir / f"__mer_{module_name}.py"
                tmp_py.write_text(compiled_mer)
                stripped_line = f'import __mer_{module_name} as {module_name}'
            else:
                # Assume pip/stdlib
                stripped_line = f'import {module_name}'

        # Functions
        if stripped_line.startswith('func ') and stripped_line.endswith('('):
            stripped_line = stripped_line.replace('func ', 'def ')
            processed_lines.append('    ' * indent_level + stripped_line + ':')
            indent_level += 1
            continue

        # Control flow blocks
        block_keywords = ['if ', 'else', 'while ', 'for ']
        is_block = False
        for kw in block_keywords:
            if stripped_line.startswith(kw) and stripped_line.endswith('('):
                is_block = True
                condition = stripped_line[len(kw):-1].strip()
                if kw == 'else':
                    processed_lines.append('    ' * (indent_level - 1) + 'else:')
                elif kw.startswith('for '):
                    if '..' in condition and 'in' in condition:
                        var_name, range_part = condition.split('in')
                        start, end = range_part.split('..')
                        processed_lines.append(
                            '    ' * indent_level + f'for {var_name.strip()} in range({start.strip()},{end.strip()}):'
                        )
                    else:
                        processed_lines.append('    ' * indent_level + f'for {condition}:')
                else:
                    processed_lines.append('    ' * indent_level + f'{kw.strip()}{condition}:')
                indent_level += 1
                break
        if is_block:
            continue

        # Closing parenthesis reduces indentation
        if stripped_line == ')':
            indent_level = max(indent_level - 1, 0)
            continue

        # Add normal line with indentation
        processed_lines.append('    ' * indent_level + stripped_line)

    return '\n'.join(processed_lines)


def read_file(file_path: str) -> str:
    return Path(file_path).read_text()


def write_file(file_path: str, content: str) -> None:
    Path(file_path).write_text(content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <source_file>")
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"File '{source_file}' not found.")
        sys.exit(1)

    source_code = read_file(source_file)
    compiled_code = compile_source(source_code, module_dir=source_file.parent)

    output_file = source_file.with_suffix('.py')
    write_file(output_file, compiled_code)
    print(f"Compiled to '{output_file}'.")


if __name__ == "__main__":
    main()
