import os

# Try to import the project Compiler and Utils from Bootstrap
try:
    from Bootstrap.compiler.classes.Compiler import Compiler
    from Bootstrap.compiler.classes.Utils import Utils
except Exception as e:  # pragma: no cover
    # Provide a clear error to help users include the Bootstrap package
    raise ImportError(
        "Could not import Compiler/Utils from Bootstrap.compiler.classes. "
        "Ensure the 'Bootstrap' folder is present at the repository root or set PYTHONPATH accordingly."
    ) from e


def get_compiler(dsl_mapping_path: str) -> Compiler:
    if not os.path.exists(dsl_mapping_path):
        raise FileNotFoundError(f"DSL mapping not found: {dsl_mapping_path}")
    return Compiler(dsl_mapping_path)


def render_content_with_text(key: str | None, value: str | None) -> str | None:
    TEXT_PLACE_HOLDER = "[]"
    if key is None or value is None:
        return value
    if key.find("btn") != -1:
        value = value.replace(TEXT_PLACE_HOLDER, Utils.get_random_text())
    elif key.find("title") != -1:
        value = value.replace(TEXT_PLACE_HOLDER, Utils.get_random_text(length_text=5, space_number=0))
    elif key.find("text") != -1:
        value = value.replace(
            TEXT_PLACE_HOLDER,
            Utils.get_random_text(length_text=56, space_number=7, with_upper_case=False),
        )
    return value
