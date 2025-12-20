# Screenshot-to-code — System Overview

This document summarizes what the system does, how it's structured, how to run it locally, deploy it, and validate features.

## Overview
- **Purpose:** Convert domain-specific layout files (`.gui`) into HTML/CSS, generate a basic `.gui` from screenshots (with optional OCR), preview raw HTML for a given URL, and analyze a URL’s content.
- **Frontend (live):** https://screenshot-to-code-web-drpauloguimaraesjrs-projects.vercel.app
- **Backend:** FastAPI service with endpoints for GUI compilation, image-to-GUI, URL fetch, and URL analysis.

## Architecture
- **Backend (FastAPI):** Entry in [backend/app/main.py](backend/app/main.py). Configuration in [backend/app/config.py](backend/app/config.py). Docker image defined by [Dockerfile](Dockerfile).
- **Compiler integration:** Adapter loads the Bootstrap compiler and mapping; see [Bootstrap/compiler](Bootstrap/compiler).
- **Frontend (static):** HTML/CSS/JS under [frontend](frontend), main page [frontend/index.html](frontend/index.html).
- **Assets & examples:**
  - `.gui` samples: [Bootstrap/resources/eval_light](Bootstrap/resources/eval_light)
  - Sample images: [HTML/images](HTML/images)
- **Deployment:**
  - Backend: Railway (Docker-based).
  - Frontend: Vercel (static site via [vercel.json](vercel.json)).
  - OCR in production enabled by installing Tesseract in [Dockerfile](Dockerfile).

## Features
- **.gui → HTML:** Upload a `.gui` and receive compiled HTML.
- **Screenshot → .gui → HTML:** Upload an image; the backend generates a naive `.gui` via simple segmentation and compiles it to HTML. Optional OCR (requires Tesseract in the container/OS).
- **URL → HTML (preview):** Fetch and display raw HTML from a URL.
- **URL Analysis:** Extracts title, meta description, headings (H1–H3), first links, word count, and text preview.

## API Endpoints
- **GET /healthz:** Health check.
- **POST /compile-gui:**
  - Form-data: `file` = `.gui` file
  - Response: HTML content
- **POST /image-to-gui?ocr=1|0:**
  - Form-data: `file` = `.png/.jpg/.jpeg`
  - Response (JSON): `{ gui, html, width, height, segments, ocr_used, ocr_texts }`
- **GET /fetch-url?url=...:**
  - Response: Raw HTML of the target page
- **GET /analyze-url?url=...:**
  - Response (JSON): `{ url, status, title, meta_description, headings, links_count, links, word_count, text_preview }`

### Quick Tests (PowerShell)
```powershell
# Health
Invoke-RestMethod -Uri "http://127.0.0.1:8000/healthz" -Method GET

# Compile a .gui example
$gui = "Bootstrap/resources/eval_light/00CDC9A8-3D73-4291-90EF-49178E408797.gui"
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/compile-gui" -Method POST -Form @{ file = Get-Item $gui } -OutFile output.html
Start-Process .\output.html

# Image → .gui → HTML (with OCR enabled if available)
$image = "HTML/images/86.jpg"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/image-to-gui?ocr=1" -Method POST -Form @{ file = Get-Item $image } | Out-File -Encoding utf8 resp.json

# Analyze a URL
Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze-url?url=https://example.com" -Method GET | Out-File -Encoding utf8 analyze.json
```

## Frontend Usage
- Open [frontend/index.html](frontend/index.html) in a browser.
- **Backend URL:** The input defaults to production; you can override via `?api=` query param or edit the field (persists in localStorage).
- Actions:
  - "Testar conexão" → calls `/healthz`
  - Upload `.gui` → calls `/compile-gui`
  - Upload image (+ optional OCR) → calls `/image-to-gui`
  - "Buscar HTML do site" → calls `/fetch-url`
  - "Analisar URL" → calls `/analyze-url` and shows the JSON summary

## Environment Variables (Backend)
- **`ALLOW_ORIGINS`**: comma-separated list of allowed CORS origins (e.g., `https://screenshot-to-code-web-drpauloguimaraesjrs-projects.vercel.app`)
- **`ALLOW_METHODS`**: allowed methods (e.g., `GET,POST`)
- **`ALLOW_HEADERS`**: allowed headers (e.g., `*`)
- **`HOST`**: host binding (default `0.0.0.0`)
- **`PORT`**: port (default `8000`)
- **`DSL_MAPPING_PATH`**: optional path to a custom DSL mapping JSON

Configured and consumed in [backend/app/config.py](backend/app/config.py).

## Local Setup
- One-command setup script: [scripts/local_setup.ps1](scripts/local_setup.ps1)
```powershell
cd "C:\Users\Cairo\screenshot to code\Screenshot-to-code\scripts"
# Optionally set CORS to your Vercel domain
.\nlocal_setup.ps1 -AllowOrigins "https://screenshot-to-code-web-drpauloguimaraesjrs-projects.vercel.app" -Host "127.0.0.1" -Port 8000
```
Manual steps (if you prefer):
```powershell
cd "C:\Users\Cairo\screenshot to code\Screenshot-to-code"
py -3.11 -m venv .venv
.
.venv\Scripts\Activate.ps1
.
.venv\Scripts\python.exe -m pip install --upgrade pip
.
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.
.venv\Scripts\python.exe -m pip install -r requirements.txt
.
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

## Deployment
- **Frontend (Vercel):** Served statically via [vercel.json](vercel.json); output directory is `frontend/`.
  - Supports `?api=` override for backend base URL.
- **Backend (Railway):** Uses [Dockerfile](Dockerfile). If auto-deploy from GitHub is enabled, pushes rebuild automatically.

### OCR in Production
- Tesseract OCR is installed in the Docker image (`tesseract-ocr`, `tesseract-ocr-eng`, `tesseract-ocr-por`).
- Verify with `image-to-gui?ocr=1`; the JSON response includes `ocr_used: true` if OCR ran.

## Packaging
- Create a ZIP of the project (excluding `.git` and `.venv`): [scripts/zip_project.ps1](scripts/zip_project.ps1)
```powershell
cd "C:\Users\Cairo\screenshot to code\Screenshot-to-code\scripts"
.
zip_project.ps1 -Output "Screenshot-to-code.zip"
```

## Troubleshooting
- **Port 8000 in use:**
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1 -Property OwningProcess
Stop-Process -Id <PID> -Force
```
- **CORS errors:** Ensure `ALLOW_ORIGINS` contains your Vercel domain exactly.
- **OCR missing:** In local Windows, install Tesseract (e.g., `winget install UB-Mannheim.TesseractOCR`). In production, ensure Docker rebuild completed.
- **Large files:** Keep `.venv` and caches out of Git; use [.gitignore](.gitignore) and [.dockerignore](.dockerignore).

## Next Steps
- Improve image segmentation and component detection; map components to a richer DSL.
- Add visual debug overlays in the frontend for detected segments.
- Expand URL analysis: `og:title`, `og:image`, `canonical`, link normalization.
