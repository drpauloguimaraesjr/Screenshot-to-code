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
import typing as t
from bs4 import BeautifulSoup
try:
    import cv2  # type: ignore
except Exception:
    cv2 = None  # OpenCV optional
try:
    import pytesseract  # type: ignore
except Exception:
    pytesseract = None  # Tesseract optional

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


@app.get("/analyze-url")
def analyze_url(url: str = Query(..., description="Full website URL to analyze")):
    """
    Fetch a webpage and return a lightweight analysis: title, meta, headings,
    link summary, and a preview of extracted text.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail="URL must start with http or https")

        resp = requests.get(url, headers={"User-Agent": "Screenshot-to-code/1.0"}, timeout=10)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=f"Upstream error fetching URL: {resp.status_code}")

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts/styles for text extraction
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = (soup.title.string.strip() if soup.title and soup.title.string else None)
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        og_desc_tag = soup.find("meta", attrs={"property": "og:description"})
        meta_description = None
        for t_ in (meta_desc_tag, og_desc_tag):
            if t_ and t_.get("content"):
                meta_description = t_.get("content").strip()
                break

        headings = {
            "h1": [h.get_text(strip=True) for h in soup.find_all("h1")[:10]],
            "h2": [h.get_text(strip=True) for h in soup.find_all("h2")[:10]],
            "h3": [h.get_text(strip=True) for h in soup.find_all("h3")[:10]],
        }

        links = []
        for a in soup.find_all("a")[:25]:
            href = a.get("href")
            text = a.get_text(strip=True)
            if href:
                links.append({"href": href, "text": text})

        # Extract plain text preview
        text_chunks = list(soup.stripped_strings)
        full_text = " ".join(text_chunks)
        preview = full_text[:1000]
        word_count = len(full_text.split())

        return {
            "url": url,
            "status": resp.status_code,
            "title": title,
            "meta_description": meta_description,
            "headings": headings,
            "links_count": len(links),
            "links": links,
            "word_count": word_count,
            "text_preview": preview,
        }
    except HTTPException:
        raise
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Timeout fetching URL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze URL: {str(e)}")


@app.post("/image-to-gui")
async def image_to_gui(
    file: UploadFile = File(...),
    ocr: bool = Query(False, description="Use OCR (requires Tesseract installed)")
):
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

        gui_tokens, segments_info = _generate_gui_from_image(input_path, width, height)

        ocr_texts: t.List[str] = []
        if ocr:
            if pytesseract is None:
                ocr_texts = ["OCR indisponível: instale Tesseract + pytesseract."]
            else:
                try:
                    # Basic OCR on the whole image; per-segment OCR could be added later
                    ocr_texts_raw = pytesseract.image_to_string(img, lang="por+eng")
                    ocr_texts = [line.strip() for line in ocr_texts_raw.splitlines() if line.strip()]
                except Exception as _:
                    ocr_texts = ["Falha ao executar OCR nesta imagem."]

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
            "segments": segments_info,
            "ocr_used": bool(ocr and pytesseract is not None),
            "ocr_texts": ocr_texts,
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


def _generate_gui_from_image(path: str, width: int, height: int) -> t.Tuple[str, t.List[t.Dict[str, t.Any]]]:
    """
    Produce a simple .gui using very lightweight heuristics and optional OpenCV segmentation.
    Returns the tokens and a list of detected segments for debugging/telemetry.
    """
    segments: t.List[t.Dict[str, t.Any]] = []
    if cv2 is None:
        # Fallback to aspect-ratio heuristic if OpenCV isn't available
        if width >= height * 1.3:
            tokens = (
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
            tokens = (
                "header {\n"
                "btn-active, btn-inactive, btn-inactive\n"
                "}\n"
                "row {\n"
                "single { small-title, text, btn-green }\n"
                "}\n"
            )
        return tokens, segments

    # OpenCV-based simple segmentation
    img_cv = cv2.imread(path)
    if img_cv is None:
        # Fallback
        return _generate_gui_from_image(path, width, height)

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thr = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 31, 10)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    morph = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area < (width * height) * 0.002:  # filter tiny noise
            continue
        boxes.append((y, x, w, h))

    # Sort by top (y), then left (x)
    boxes.sort(key=lambda b: (b[0], b[1]))

    # Group into rows by proximity in y
    rows: t.List[t.List[t.Tuple[int, int, int, int]]] = []
    for box in boxes:
        placed = False
        for row in rows:
            # If y overlap or close, treat as same row
            if abs(box[0] - row[0][0]) < max(15, height * 0.02):
                row.append(box)
                placed = True
                break
        if not placed:
            rows.append([box])

    # Sort each row by x
    for row in rows:
        row.sort(key=lambda b: b[1])

    # Build tokens from rows with a simple mapping
    token_lines: t.List[str] = []
    token_lines.append("header {\nbtn-active, btn-inactive, btn-inactive\n}")
    for row in rows[:6]:  # cap rows to avoid huge outputs
        cols = len(row)
        if cols >= 4:
            block = "quadruple { small-title, text, btn-green }\n" * 4
            token_lines.append("row {\n" + block + "}")
        elif cols == 3:
            block = "triple { small-title, text, btn-green }\n" * 1
            # Fallback to multiple singles if 'triple' unknown
            block = ("single { small-title, text, btn-green }\n" * 3)
            token_lines.append("row {\n" + block + "}")
        elif cols == 2:
            block = ("double { small-title, text, btn-green }\n")
            # Fallback to two singles
            block = ("single { small-title, text, btn-green }\n" * 2)
            token_lines.append("row {\n" + block + "}")
        else:
            token_lines.append("row {\nsingle { small-title, text, btn-green }\n}")

    tokens = "\n".join(token_lines) + "\n"
    # Prepare segments info
    for (y, x, w, h) in boxes[:50]:
        segments.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})

    return tokens, segments
