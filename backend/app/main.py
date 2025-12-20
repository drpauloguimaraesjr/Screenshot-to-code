import sys
import os
import shutil
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from .config import settings
from ..core.compiler_adapter import get_compiler, render_content_with_text
import requests
from urllib.parse import urlparse, urljoin
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

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes de validação
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_DIMENSION = 1920  # pixels
SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

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


def _validate_file_size(contents: bytes, max_size: int = MAX_FILE_SIZE) -> None:
    """Valida o tamanho do arquivo enviado."""
    if len(contents) > max_size:
        size_mb = max_size / 1024 / 1024
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande. Tamanho máximo permitido: {size_mb}MB"
        )


def _is_valid_image_format(contents: bytes) -> bool:
    """Valida se o arquivo é uma imagem válida usando magic bytes."""
    if contents.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
        return True
    if contents.startswith(b'\xff\xd8\xff'):  # JPEG
        return True
    if contents.startswith(b'GIF87a') or contents.startswith(b'GIF89a'):  # GIF
        return True
    return False


@app.post("/compile-gui")
async def compile_gui(file: UploadFile = File(...)):
    """Compila um arquivo .gui para HTML."""
    if not file.filename or not file.filename.lower().endswith('.gui'):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos .gui são aceitos. Por favor, envie um arquivo com extensão .gui"
        )

    logger.info(f"Compilando arquivo GUI: {file.filename}")

    tmp_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(tmp_dir, file.filename)
        output_path = os.path.join(tmp_dir, os.path.splitext(file.filename)[0] + '.html')

        # Write uploaded file
        with open(input_path, 'wb') as f:
            contents = await file.read()
            _validate_file_size(contents)
            f.write(contents)

        # Read file content and pass to Compiler.compile (the Compiler expects the token content)
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as fh:
            tokens_content = fh.read()

        compiler = get_compiler(DSL_MAPPING_PATH)
        result = compiler.compile(tokens_content, output_path, rendering_function=render_content_with_text)

        if result == "Parsing Error":
            logger.error(f"Erro de parsing ao compilar {file.filename}")
            raise HTTPException(
                status_code=500,
                detail="Erro de parsing ao compilar tokens GUI. Verifique se o arquivo .gui está no formato correto."
            )

        # Read the generated HTML file
        with open(output_path, 'rb') as f:
            html_content = f.read()

        logger.info(f"Compilação concluída com sucesso: {file.filename}")
        return HTMLResponse(content=html_content, media_type='text/html')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao compilar {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao compilar arquivo GUI: {str(e)}"
        )
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass  # Ignore cleanup errors


@app.get("/fetch-url")
def fetch_url(url: str = Query(..., description="URL completa do site para buscar")):
    """
    Busca o HTML bruto de uma URL e retorna para pré-visualização.
    """
    logger.info(f"Buscando HTML da URL: {url}")
    try:
        # Basic validation
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(
                status_code=400,
                detail="URL deve começar com http:// ou https://"
            )

        # Fetch with a simple UA and timeout
        resp = requests.get(url, headers={"User-Agent": "Screenshot-to-code/1.0"}, timeout=10)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Erro ao buscar URL: status {resp.status_code}"
            )

        content = resp.text
        logger.info(f"HTML buscado com sucesso: {url} ({len(content)} bytes)")
        # Return HTML directly. Frontend will preview and allow download.
        return HTMLResponse(content=content)
    except HTTPException:
        raise
    except requests.Timeout:
        logger.warning(f"Timeout ao buscar URL: {url}")
        raise HTTPException(status_code=504, detail="Tempo limite excedido ao buscar URL")
    except Exception as e:
        logger.error(f"Erro ao buscar URL {url}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Falha ao buscar URL: {str(e)}")


@app.get("/analyze-url")
def analyze_url(url: str = Query(..., description="URL completa do site para analisar")):
    """
    Busca uma página web e retorna uma análise leve: título, meta tags, headings,
    resumo de links e uma prévia do texto extraído.
    """
    logger.info(f"Analisando URL: {url}")
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(
                status_code=400,
                detail="URL deve começar com http:// ou https://"
            )

        resp = requests.get(url, headers={"User-Agent": "Screenshot-to-code/1.0"}, timeout=10)
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Erro ao buscar URL: status {resp.status_code}"
            )

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts/styles for text extraction
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Title (prioriza og:title)
        title = None
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            title = og_title.get("content").strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Meta description (prioriza og:description)
        meta_description = None
        og_desc_tag = soup.find("meta", attrs={"property": "og:description"})
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        for t_ in (og_desc_tag, meta_desc_tag):
            if t_ and t_.get("content"):
                meta_description = t_.get("content").strip()
                break

        # Open Graph image
        og_image = None
        og_image_tag = soup.find("meta", attrs={"property": "og:image"})
        if og_image_tag and og_image_tag.get("content"):
            og_image = og_image_tag.get("content").strip()
            # Normalizar URL relativa
            if not og_image.startswith(("http://", "https://")):
                og_image = urljoin(url, og_image)

        # Canonical URL
        canonical = None
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        if canonical_tag and canonical_tag.get("href"):
            canonical = canonical_tag.get("href").strip()
            if not canonical.startswith(("http://", "https://")):
                canonical = urljoin(url, canonical)

        headings = {
            "h1": [h.get_text(strip=True) for h in soup.find_all("h1")[:10]],
            "h2": [h.get_text(strip=True) for h in soup.find_all("h2")[:10]],
            "h3": [h.get_text(strip=True) for h in soup.find_all("h3")[:10]],
        }

        # Normalizar links
        links = []
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        for a in soup.find_all("a")[:25]:
            href = a.get("href")
            text = a.get_text(strip=True)
            if href:
                # Normalizar URLs relativas
                if not href.startswith(("http://", "https://", "mailto:", "tel:")):
                    href = urljoin(base_url, href)
                links.append({"href": href, "text": text})

        # Extract plain text preview
        text_chunks = list(soup.stripped_strings)
        full_text = " ".join(text_chunks)
        preview = full_text[:1000]
        word_count = len(full_text.split())

        logger.info(f"Análise concluída: {url} ({word_count} palavras)")

        return {
            "url": url,
            "status": resp.status_code,
            "title": title,
            "meta_description": meta_description,
            "og_image": og_image,
            "canonical": canonical,
            "headings": headings,
            "links_count": len(links),
            "links": links,
            "word_count": word_count,
            "text_preview": preview,
        }
    except HTTPException:
        raise
    except requests.Timeout:
        logger.warning(f"Timeout ao analisar URL: {url}")
        raise HTTPException(status_code=504, detail="Tempo limite excedido ao analisar URL")
    except Exception as e:
        logger.error(f"Erro ao analisar URL {url}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Falha ao analisar URL: {str(e)}")


@app.post("/image-to-gui")
async def image_to_gui(
    file: UploadFile = File(...),
    ocr: bool = Query(False, description="Usar OCR (requer Tesseract instalado)")
):
    """
    Gera um scaffold .gui simples a partir de uma imagem usando segmentação básica
    e retorna tanto o .gui gerado quanto o HTML compilado.
    """
    if not file.filename or not any(file.filename.lower().endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Envie uma imagem válida. Formatos aceitos: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        )

    logger.info(f"Processando imagem para GUI: {file.filename} (OCR: {ocr})")

    tmp_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(tmp_dir, file.filename)
        output_path = os.path.join(tmp_dir, os.path.splitext(file.filename)[0] + '.html')

        # Save uploaded image
        with open(input_path, 'wb') as f:
            contents = await file.read()
            _validate_file_size(contents)
            
            # Validar formato de imagem
            if not _is_valid_image_format(contents):
                raise HTTPException(
                    status_code=400,
                    detail="Arquivo não parece ser uma imagem válida. Verifique o formato."
                )
            
            f.write(contents)

        # Open image and derive a simple layout heuristic
        try:
            img = Image.open(input_path)
            width, height = img.size
            
            # Otimizar imagens muito grandes
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                logger.info(f"Redimensionando imagem de {width}x{height} para processamento")
                ratio = min(MAX_IMAGE_DIMENSION / width, MAX_IMAGE_DIMENSION / height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                img.save(input_path, optimize=True)
                width, height = new_size
                logger.info(f"Imagem redimensionada para {width}x{height}")
        except Exception as e:
            logger.error(f"Erro ao abrir imagem {file.filename}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Não foi possível abrir a imagem enviada: {str(e)}"
            )

        gui_tokens, segments_info = _generate_gui_from_image(input_path, width, height)

        ocr_texts: t.List[str] = []
        if ocr:
            if pytesseract is None:
                logger.warning("OCR solicitado mas Tesseract não disponível")
                ocr_texts = ["OCR indisponível: instale Tesseract + pytesseract."]
            else:
                try:
                    # Basic OCR on the whole image; per-segment OCR could be added later
                    logger.info("Executando OCR na imagem")
                    ocr_texts_raw = pytesseract.image_to_string(img, lang="por+eng")
                    ocr_texts = [line.strip() for line in ocr_texts_raw.splitlines() if line.strip()]
                    logger.info(f"OCR extraiu {len(ocr_texts)} linhas de texto")
                except Exception as e:
                    logger.error(f"Erro ao executar OCR: {str(e)}", exc_info=True)
                    ocr_texts = [f"Falha ao executar OCR nesta imagem: {str(e)}"]

        # Compile generated tokens
        logger.info(f"Compilando GUI gerada ({len(segments_info)} segmentos detectados)")
        compiler = get_compiler(DSL_MAPPING_PATH)
        result = compiler.compile(gui_tokens, output_path, rendering_function=render_content_with_text)
        if result == "Parsing Error":
            logger.error("Erro de parsing ao compilar GUI gerada")
            raise HTTPException(
                status_code=500,
                detail="Erro de parsing ao compilar GUI gerada. Tente com outra imagem."
            )

        # Read compiled HTML
        with open(output_path, 'r', encoding='utf-8', errors='ignore') as fh:
            html_content = fh.read()

        logger.info(f"Processamento concluído com sucesso: {file.filename}")

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
        logger.error(f"Erro ao gerar GUI de {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao gerar .gui a partir da imagem: {str(e)}"
        )
    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass


def _generate_gui_from_image(
    path: str,
    width: int,
    height: int,
    use_opencv: bool = True
) -> t.Tuple[str, t.List[t.Dict[str, t.Any]]]:
    """
    Produz um .gui simples usando heurísticas leves e segmentação opcional com OpenCV.
    Retorna os tokens e uma lista de segmentos detectados para debug/telemetria.
    """
    segments: t.List[t.Dict[str, t.Any]] = []
    
    def _fallback_heuristic() -> str:
        """Gera tokens usando heurística baseada em proporção de tela."""
        if width >= height * 1.3:
            return (
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
            return (
                "header {\n"
                "btn-active, btn-inactive, btn-inactive\n"
                "}\n"
                "row {\n"
                "single { small-title, text, btn-green }\n"
                "}\n"
            )
    
    if cv2 is None or not use_opencv:
        # Fallback to aspect-ratio heuristic if OpenCV isn't available
        logger.debug("Usando heurística de fallback (OpenCV não disponível)")
        return _fallback_heuristic(), segments

    # OpenCV-based simple segmentation
    img_cv = cv2.imread(path)
    if img_cv is None:
        # Fallback seguro - não recursão infinita
        logger.warning(f"Não foi possível ler imagem com OpenCV, usando heurística de fallback")
        return _fallback_heuristic(), segments

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
