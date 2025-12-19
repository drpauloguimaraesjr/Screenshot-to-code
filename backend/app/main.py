import sys
import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from .config import settings
from ..core.compiler_adapter import get_compiler, render_content_with_text
import requests
from urllib.parse import urlparse
from PIL import Image

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


@app.get("/fetch-url")
def fetch_url(url: str = Query(..., description="Full website URL to fetch")):
    """
    Fetch a webpage HTML by URL and return the raw HTML.
    This is a passthrough helper for previewing existing sites in the frontend.
    """
    try:
        # Basic validation
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail="URL must start with http or https")

        # Fetch with a simple UA and timeout
        resp = requests.get(url, headers={"User-Agent": "Screenshot-to-code/1.0"}, timeout=10)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=f"Upstream error fetching URL: {resp.status_code}")

        content = resp.text
        # Return HTML directly. Frontend will preview and allow download.
        return HTMLResponse(content=content)
    except HTTPException:
        raise
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Timeout fetching URL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch URL: {str(e)}")


@app.post("/image-to-gui")
async def image_to_gui(file: UploadFile = File(...)):
    """
    Naive screenshot-to-GUI: generate a simple .gui scaffold from an image
    and return both the generated .gui and compiled HTML.
    This is a minimal MVP without ML; it uses image size heuristics.
    """
    if not file.filename or not any(file.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg"]):
        raise HTTPException(status_code=400, detail="Envie uma imagem (.png, .jpg, .jpeg)")

    tmp_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(tmp_dir, file.filename)
        output_path = os.path.join(tmp_dir, os.path.splitext(file.filename)[0] + '.html')

        # Save uploaded image
        with open(input_path, 'wb') as f:
            contents = await file.read()
            f.write(contents)

        # Open image and derive a simple layout heuristic
        try:
            img = Image.open(input_path)
            width, height = img.size
        except Exception:
            raise HTTPException(status_code=400, detail="Não foi possível abrir a imagem enviada")

        # Very naive heuristic: wide images -> multiple cards, tall images -> single content
        if width >= height * 1.3:
            gui_tokens = (
                "header {\n"
                "btn-active, btn-inactive, btn-inactive, btn-inactive, btn-inactive\n"
                "}\n"
                "row {\n"
                "quadruple { small-title, text, btn-green }\n"
                "quadruple { small-title, text, btn-orange }\n"
                "quadruple { small-title, text, btn-red }\n"
                "quadruple { small-title, text, btn-green }\n"
                "}\n"
                "row {\n"
                "single { small-title, text, btn-blue }\n"
                "}\n"
            )
        else:
            gui_tokens = (
                "header {\n"
                "btn-active, btn-inactive, btn-inactive\n"
                "}\n"
                "row {\n"
                "single { small-title, text, btn-green }\n"
                "}\n"
            )

        # Compile generated tokens
        compiler = get_compiler(DSL_MAPPING_PATH)
        result = compiler.compile(gui_tokens, output_path, rendering_function=render_content_with_text)
        if result == "Parsing Error":
            raise HTTPException(status_code=500, detail="Erro de parsing ao compilar GUI gerada")

        # Read compiled HTML
        with open(output_path, 'r', encoding='utf-8', errors='ignore') as fh:
            html_content = fh.read()

        return {
            "gui": gui_tokens,
            "html": html_content,
            "width": width,
            "height": height,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao gerar .gui: {str(e)}")
    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass
