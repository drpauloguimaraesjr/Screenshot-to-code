from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import tempfile

app = FastAPI(title="Screenshot-to-code API")

# Allow CORS so the frontend (hosted elsewhere) can call this API.
# For production, replace ['*'] with the exact origin(s) (e.g. https://your-frontend.vercel.app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make the compiler importable from the repo Bootstrap/compiler
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
compiler_path = os.path.join(repo_root, 'Bootstrap', 'compiler')
sys.path.insert(0, compiler_path)

from classes.Compiler import Compiler
from classes.Utils import Utils


def render_content_with_text(key, value):
    TEXT_PLACE_HOLDER = "[]"
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


@app.get("/", response_class=HTMLResponse)
def index():
    return "<h3>Screenshot-to-code API</h3><p>Use POST /compile-gui to upload a .gui file and receive HTML.</p>"


@app.post("/compile-gui")
async def compile_gui(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.gui'):
        raise HTTPException(status_code=400, detail="Only .gui files are accepted for now")

    tmp_dir = tempfile.mkdtemp()
    input_path = os.path.join(tmp_dir, file.filename)
    output_path = os.path.join(tmp_dir, os.path.splitext(file.filename)[0] + '.html')

    with open(input_path, 'wb') as f:
        contents = await file.read()
        f.write(contents)

    # Read file content and pass to Compiler.compile (the Compiler expects the token content)
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as fh:
        tokens_content = fh.read()

    dsl_mapping = os.path.join(compiler_path, 'assets', 'web-dsl-mapping.json')
    compiler = Compiler(dsl_mapping)
    result = compiler.compile(tokens_content, output_path, rendering_function=render_content_with_text)

    if result == "Parsing Error":
        raise HTTPException(status_code=500, detail="Parsing Error while compiling GUI tokens")

    return FileResponse(output_path, media_type='text/html', filename=os.path.basename(output_path))
