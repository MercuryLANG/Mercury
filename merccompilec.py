import sys
import os
from pathlib import Path
import importlib.util

def compile_source(source_code: str, module_dir: Path = None) -> str:
    lines = source_code.splitlines()
    processed_lines = []
    indent_level = 0
    module_dir = module_dir or Path('.')
    in_multiline_comment = False

    for raw_line in lines:
        line = raw_line.rstrip('\n')
        stripped_line = line.strip()

        if in_multiline_comment:
            if '*+' in stripped_line:
                after = stripped_line.split('*+', 1)[1].strip()
                in_multiline_comment = False
                if after:
                    stripped_line = after
                else:
                    continue
            else:
                processed_lines.append('# ' + stripped_line)
                continue

        if '+*' in stripped_line:
            before = stripped_line.split('+*', 1)[0].strip()
            if '*+' in stripped_line:
                after = stripped_line.split('*+', 1)[1].strip()
                stripped_line = (before + ' ' + after).strip()
            else:
                if before:
                    processed_lines.append(before)
                in_multiline_comment = True
                continue

        for tok in ('++', '--', '//'):
            if tok in stripped_line:
                parts = stripped_line.split(tok, 1)
                code_part = parts[0].rstrip()
                comment_part = parts[1].strip()
                if code_part:
                    processed_lines.append('    ' * indent_level + code_part)
                processed_lines.append('# ' + comment_part)
                stripped_line = ''
                break

        if not stripped_line:
            continue

        if not stripped_line.endswith(';') and not stripped_line.endswith('(') and stripped_line != ')':
            raise SyntaxError(f"Missing semicolon at end of line:\n{raw_line}")

        if stripped_line.endswith(';'):
            stripped_line = stripped_line[:-1].rstrip()

        if stripped_line.startswith('var '):
            stripped_line = stripped_line[len('var '):].lstrip()

        if 'write(' in stripped_line:
            stripped_line = stripped_line.replace('write(', 'print(')
        if 'userinput(' in stripped_line:
            stripped_line = stripped_line.replace('userinput(', 'input(')

        if stripped_line.startswith('use '):
            module_name = stripped_line[len('use '):].strip()
            py_file = module_dir / f"{module_name}.py"
            merc_file = module_dir / f"{module_name}.merc"
            if py_file.exists():
                stripped_line = f'import {module_name}'
            elif merc_file.exists():
                merc_source = merc_file.read_text()
                compiled_mercury = compile_source(merc_source, module_dir=module_dir)
                tmp_py = module_dir / f"__merc_{module_name}.py"
                tmp_py.write_text(compiled_mercury)
                stripped_line = f'import __merc_{module_name} as {module_name}'
            else:
                stripped_line = f'import {module_name}'

        if stripped_line.startswith('func ') and stripped_line.endswith('('):
            stripped_line = stripped_line.replace('func ', 'def ')
            processed_lines.append('    ' * indent_level + stripped_line + ':')
            indent_level += 1
            continue

        if stripped_line.startswith('return '):
            processed_lines.append('    ' * indent_level + stripped_line)
            continue

        block_keywords = ['if ', 'else', 'while ', 'for ']
        is_block = False
        for kw in block_keywords:
            if stripped_line.startswith(kw) and stripped_line.endswith('('):
                is_block = True
                condition = stripped_line[len(kw):-1].strip()
                if kw == 'else':
                    processed_lines.append('    ' * max(indent_level - 1, 0) + 'else:')
                elif kw.startswith('for '):
                    if '..' in condition and 'in' in condition:
                        var_name, range_part = condition.split('in', 1)
                        start, end = range_part.split('..', 1)
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

        if stripped_line == ')':
            indent_level = max(indent_level - 1, 0)
            continue

        processed_lines.append('    ' * indent_level + stripped_line)

    return '\n'.join(processed_lines)


def read_file(file_path: str) -> str:
    return Path(file_path).read_text()

def write_file(file_path: str, content: str) -> None:
    Path(file_path).write_text(content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python merccompile.py <source_file>")
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

