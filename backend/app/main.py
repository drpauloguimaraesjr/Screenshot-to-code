import sys
import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from .config import settings
from ..core.compiler_adapter import get_compiler, render_content_with_text

app = FastAPI(title=settings.APP_NAME)

# Allow CORS so the frontend (hosted elsewhere) can call this API.
# For production, replace ['*'] with the exact origin(s) (e.g. https://your-frontend.vercel.app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DSL_MAPPING_PATH = settings.resolve_dsl_mapping_path(repo_root)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index():
    return "<h3>Screenshot-to-code API</h3><p>Use POST /compile-gui to upload a .gui file and receive HTML.</p>"


@app.post("/compile-gui")
async def compile_gui(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith('.gui'):
        raise HTTPException(status_code=400, detail="Only .gui files are accepted for now")

    tmp_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(tmp_dir, file.filename)
        output_path = os.path.join(tmp_dir, os.path.splitext(file.filename)[0] + '.html')

        # Write uploaded file
        with open(input_path, 'wb') as f:
            contents = await file.read()
            f.write(contents)

        # Read file content and pass to Compiler.compile (the Compiler expects the token content)
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as fh:
            tokens_content = fh.read()

        compiler = get_compiler(DSL_MAPPING_PATH)
        result = compiler.compile(tokens_content, output_path, rendering_function=render_content_with_text)

        if result == "Parsing Error":
            raise HTTPException(status_code=500, detail="Parsing Error while compiling GUI tokens")

        # Read the generated HTML file
        with open(output_path, 'rb') as f:
            html_content = f.read()

        return HTMLResponse(content=html_content, media_type='text/html')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compiling GUI: {str(e)}")
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass  # Ignore cleanup errors
