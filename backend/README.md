# Backend - Screenshot-to-code API

API FastAPI para compilar arquivos `.gui` em HTML usando o compilador Bootstrap.

## Estrutura

```
backend/
├── app/
│   ├── main.py          # Aplicação FastAPI principal
│   └── config.py        # Configurações e variáveis de ambiente
├── core/
│   └── compiler_adapter.py  # Adaptador para o compilador Bootstrap
├── assets/
│   └── web-dsl-mapping.json  # Mapeamento DSL para HTML
├── requirements.txt     # Dependências Python
├── Dockerfile          # Configuração Docker
├── railway.json       # Configuração Railway
└── nixpacks.toml      # Configuração Nixpacks (Railway)

```

## Endpoints

### `GET /`
Retorna uma página HTML simples com informações sobre a API.

### `GET /healthz`
Endpoint de health check. Retorna `{"status": "ok"}`.

### `POST /compile-gui`
Compila um arquivo `.gui` em HTML.

**Parâmetros:**
- `file`: Arquivo `.gui` (multipart/form-data)

**Resposta:**
- Arquivo HTML gerado

**Exemplo:**
```bash
curl -X POST https://screenshot-to-code-api-production.up.railway.app/compile-gui \
  -F "file=@exemplo.gui" \
  -o resultado.html
```

## Variáveis de Ambiente

- `PORT`: Porta do servidor (padrão: 8000)
- `HOST`: Host do servidor (padrão: 0.0.0.0)
- `ALLOW_ORIGINS`: Origens CORS permitidas, separadas por vírgula (padrão: *)
- `ALLOW_METHODS`: Métodos HTTP permitidos (padrão: *)
- `ALLOW_HEADERS`: Headers permitidos (padrão: *)
- `DSL_MAPPING_PATH`: Caminho para o arquivo DSL mapping (opcional)

## Deploy no Railway

### Opção 1: Usando Dockerfile (Recomendado)

1. Conecte seu repositório GitHub ao Railway
2. O Railway detectará automaticamente o `Dockerfile` na pasta `backend/`
3. Configure as variáveis de ambiente se necessário
4. O Railway fará o deploy automaticamente

### Opção 2: Usando Nixpacks

1. Conecte seu repositório GitHub ao Railway
2. O Railway usará o arquivo `nixpacks.toml` para construir a aplicação
3. Configure as variáveis de ambiente se necessário

### Configuração no Railway

1. Acesse o Railway Dashboard
2. Crie um novo projeto
3. Conecte o repositório GitHub
4. Configure o Root Directory como `backend/` (se necessário)
5. Configure o Build Command (se usando Nixpacks):
   ```
   pip install -r backend/requirements.txt
   ```
6. Configure o Start Command:
   ```
   uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
   ```
7. Configure as variáveis de ambiente:
   - `PORT`: Será definido automaticamente pelo Railway
   - `ALLOW_ORIGINS`: Configure com a URL do seu frontend (ex: `https://seu-frontend.vercel.app`)

## Execução Local

### Pré-requisitos

- Python 3.10+
- pip

### Instalação

```bash
cd backend
pip install -r requirements.txt
```

### Execução

```bash
uvicorn app.main:app --reload --port 8000
```

A API estará disponível em `http://localhost:8000`

### Teste Local

```bash
# Health check
curl http://localhost:8000/healthz

# Compilar arquivo .gui
curl -X POST http://localhost:8000/compile-gui \
  -F "file=@caminho/para/arquivo.gui" \
  -o resultado.html
```

## Dependências

- `fastapi`: Framework web
- `uvicorn`: Servidor ASGI
- `python-multipart`: Suporte para upload de arquivos
- `jinja2`: Template engine (usado pelo compilador)
- `numpy`: Biblioteca numérica (usada pelo compilador)

## Notas

- O backend depende do módulo `Bootstrap.compiler.classes` que deve estar presente no repositório
- O arquivo `web-dsl-mapping.json` é necessário para o funcionamento do compilador
- O Railway define automaticamente a variável `PORT` - não é necessário configurá-la manualmente

