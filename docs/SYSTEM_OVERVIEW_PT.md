# Screenshot-to-code — Visão Geral do Sistema (PT-BR)

Este documento resume o que o sistema faz, como está estruturado, como rodar localmente, como publicar e como validar as funcionalidades.

## Visão Geral
- **Propósito:** Converter arquivos de layout em DSL (`.gui`) para HTML/CSS, gerar um `.gui` básico a partir de screenshots (com OCR opcional), pré-visualizar o HTML bruto de uma URL e analisar o conteúdo de uma página.
- **Frontend (online):** https://screenshot-to-code-web-drpauloguimaraesjrs-projects.vercel.app
- **Backend:** Serviço FastAPI com endpoints para compilação de GUI, image-to-GUI, busca de HTML e análise de URL.

## Arquitetura
- **Backend (FastAPI):** Ponto de entrada em [backend/app/main.py](backend/app/main.py). Configurações em [backend/app/config.py](backend/app/config.py). Imagem Docker definida em [Dockerfile](Dockerfile).
- **Integração com o Compiler:** Adaptador carrega o compiler do Bootstrap e o mapeamento; veja [Bootstrap/compiler](Bootstrap/compiler).
- **Frontend (estático):** HTML/CSS/JS em [frontend](frontend), página principal [frontend/index.html](frontend/index.html).
- **Assets & exemplos:**
  - Exemplos `.gui`: [Bootstrap/resources/eval_light](Bootstrap/resources/eval_light)
  - Imagens de exemplo: [HTML/images](HTML/images)
- **Publicação:**
  - Backend: Railway (baseado em Docker).
  - Frontend: Vercel (site estático via [vercel.json](vercel.json)).
  - OCR em produção habilitado instalando Tesseract no [Dockerfile](Dockerfile).

## Funcionalidades
- **.gui → HTML:** Faça upload de um `.gui` e receba o HTML compilado.
- **Screenshot → .gui → HTML:** Faça upload de uma imagem; o backend gera um `.gui` simples por segmentação e compila para HTML. OCR opcional (requer Tesseract no container/SO).
- **URL → HTML (prévia):** Busca e exibe o HTML bruto de uma URL.
- **Análise de URL:** Extrai título, meta descrição, headings (H1–H3), alguns links, contagem de palavras e uma prévia do texto.

## Endpoints da API
- **GET /healthz:** Verifica saúde do serviço.
- **POST /compile-gui:**
  - Form-data: `file` = arquivo `.gui`
  - Resposta: conteúdo HTML
- **POST /image-to-gui?ocr=1|0:**
  - Form-data: `file` = `.png/.jpg/.jpeg`
  - Resposta (JSON): `{ gui, html, width, height, segments, ocr_used, ocr_texts }`
- **GET /fetch-url?url=...:**
  - Resposta: HTML bruto da página alvo
- **GET /analyze-url?url=...:**
  - Resposta (JSON): `{ url, status, title, meta_description, headings, links_count, links, word_count, text_preview }`

### Testes Rápidos (PowerShell)
```powershell
# Saúde
Invoke-RestMethod -Uri "http://127.0.0.1:8000/healthz" -Method GET

# Compilar um .gui de exemplo
$gui = "Bootstrap/resources/eval_light/00CDC9A8-3D73-4291-90EF-49178E408797.gui"
Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/compile-gui" -Method POST -Form @{ file = Get-Item $gui } -OutFile output.html
Start-Process .\output.html

# Imagem → .gui → HTML (com OCR se disponível)
$image = "HTML/images/86.jpg"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/image-to-gui?ocr=1" -Method POST -Form @{ file = Get-Item $image } | Out-File -Encoding utf8 resp.json

# Analisar uma URL
Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze-url?url=https://example.com" -Method GET | Out-File -Encoding utf8 analyze.json
```

## Uso do Frontend
- Abra [frontend/index.html](frontend/index.html) no navegador.
- **URL do Backend:** Por padrão usa produção; você pode sobrescrever via `?api=` na URL ou alterando o campo (persistência via localStorage).
- Ações:
  - "Testar conexão" → chama `/healthz`
  - Upload de `.gui` → chama `/compile-gui`
  - Upload de imagem (+ OCR opcional) → chama `/image-to-gui`
  - "Buscar HTML do site" → chama `/fetch-url`
  - "Analisar URL" → chama `/analyze-url` e exibe o resumo JSON

## Variáveis de Ambiente (Backend)
- **`ALLOW_ORIGINS`**: lista separada por vírgula de origens CORS permitidas (ex.: `https://screenshot-to-code-web-drpauloguimaraesjrs-projects.vercel.app`)
- **`ALLOW_METHODS`**: métodos permitidos (ex.: `GET,POST`)
- **`ALLOW_HEADERS`**: headers permitidos (ex.: `*`)
- **`HOST`**: host de binding (padrão `0.0.0.0`)
- **`PORT`**: porta (padrão `8000`)
- **`DSL_MAPPING_PATH`**: caminho opcional para um JSON de mapeamento DSL customizado

Configuradas e lidas em [backend/app/config.py](backend/app/config.py).

## Setup Local
- Script de setup: [scripts/local_setup.ps1](scripts/local_setup.ps1)
```powershell
cd "C:\Users\Cairo\screenshot to code\Screenshot-to-code\scripts"
# Opcional: definir CORS para seu domínio Vercel
.\nlocal_setup.ps1 -AllowOrigins "https://screenshot-to-code-web-drpauloguimaraesjrs-projects.vercel.app" -Host "127.0.0.1" -Port 8000
```
Passos manuais (se preferir):
```powershell
cd "C:\Users\Cairo\screenshot to code\Screenshot-to-code"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

## Publicação
- **Frontend (Vercel):** Servido estaticamente via [vercel.json](vercel.json); diretório é `frontend/`.
  - Suporta `?api=` para sobrescrever a URL base do backend.
- **Backend (Railway):** Usa [Dockerfile](Dockerfile). Com deploy automático via GitHub, cada push reconstrói a imagem.

### OCR em Produção
- Tesseract OCR instalado na imagem Docker (`tesseract-ocr`, `tesseract-ocr-eng`, `tesseract-ocr-por`).
- Valide com `image-to-gui?ocr=1`; a resposta inclui `ocr_used: true` se o OCR rodou.

## Empacotamento
- Criar um ZIP do projeto (exclui `.git` e `.venv`): [scripts/zip_project.ps1](scripts/zip_project.ps1)
```powershell
cd "C:\Users\Cairo\screenshot to code\Screenshot-to-code\scripts"
.\zip_project.ps1 -Output "Screenshot-to-code.zip"
```

## Solução de Problemas
- **Porta 8000 em uso:**
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1 -Property OwningProcess
Stop-Process -Id <PID> -Force
```
- **Erros de CORS:** Verifique se `ALLOW_ORIGINS` contém exatamente o domínio do seu Vercel.
- **OCR ausente:** No Windows local, instale Tesseract (ex.: `winget install UB-Mannheim.TesseractOCR`). Em produção, confirme que o rebuild do Docker foi concluído.
- **Arquivos grandes:** Mantenha `.venv` e caches fora do Git; use [.gitignore](.gitignore) e [.dockerignore](.dockerignore).

## Próximos Passos
- Melhorar a segmentação de imagem e a detecção de componentes; mapear para uma DSL mais rica.
- Adicionar overlays visuais no frontend para depurar segmentos detectados.
- Expandir a análise de URL: `og:title`, `og:image`, `canonical`, normalização de links.
