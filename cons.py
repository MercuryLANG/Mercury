import merccompilec
from merccompilec import compile_source
import sys
from pathlib import Path

def main():
    while True:
        user_input = input("Mercury> ")
        if user_input.lower() in ('exit', 'quit'):
            break
        try:
            compiled_code = compile_source(user_input)
            exec(compiled_code)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
