#!/usr/bin/env python3
import os
import sys

# Make compiler package importable when running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Bootstrap', 'compiler'))

from classes.Compiler import Compiler
from classes.Utils import Utils

TEXT_PLACE_HOLDER = "[]"

def render_content_with_text(key, value):
    if key is None or value is None:
        return value
    if key.find("btn") != -1:
        value = value.replace(TEXT_PLACE_HOLDER, Utils.get_random_text())
    elif key.find("title") != -1:
        value = value.replace(TEXT_PLACE_HOLDER, Utils.get_random_text(length_text=5, space_number=0))
    elif key.find("text") != -1:
        value = value.replace(TEXT_PLACE_HOLDER,
                              Utils.get_random_text(length_text=56, space_number=7, with_upper_case=False))
    return value


def main():
    if len(sys.argv) < 2:
        print("Usage: compile_example.py <path/to/file.gui>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print("File not found:", input_file)
        sys.exit(1)

    output_file = os.path.splitext(input_file)[0] + '.html'

    dsl_path = os.path.join(os.path.dirname(__file__), '..', 'Bootstrap', 'compiler', 'assets', 'web-dsl-mapping.json')
    dsl_path = os.path.normpath(dsl_path)
    compiler = Compiler(dsl_path)
    compiler.compile(input_file, output_file, rendering_function=render_content_with_text)

    print('Wrote', output_file)


if __name__ == '__main__':
    main()
