# 📡 API Backend - Informações para o Frontend

## 🔗 URL Base da API

```
https://screenshot-to-code-api-production.up.railway.app
```

## 📋 Endpoints Disponíveis

### 1. Health Check
Verifica se a API está funcionando.

**GET** `/healthz`

**Resposta:**
```json
{
  "status": "ok"
}
```

**Exemplo:**
```javascript
const response = await fetch('https://screenshot-to-code-api-production.up.railway.app/healthz');
const data = await response.json();
console.log(data); // { status: "ok" }
```

---

### 2. Página Inicial
Retorna informações sobre a API.

**GET** `/`

**Resposta:**
```html
<h3>Screenshot-to-code API</h3>
<p>Use POST /compile-gui to upload a .gui file and receive HTML.</p>
```

---

### 3. Compilar Arquivo .gui → HTML ⭐
Endpoint principal para compilar arquivos `.gui` em HTML.

**POST** `/compile-gui`

**Parâmetros:**
- `file`: Arquivo `.gui` (multipart/form-data)

**Resposta:**
- HTML gerado (text/html)

**Códigos de Status:**
- `200`: Sucesso - retorna HTML
- `400`: Arquivo inválido (não é .gui)
- `500`: Erro ao compilar

**Exemplo JavaScript:**
```javascript
async function compileGui(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(
      'https://screenshot-to-code-api-production.up.railway.app/compile-gui',
      {
        method: 'POST',
        body: formData
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro ao compilar');
    }

    const html = await response.text();
    return html;
  } catch (error) {
    console.error('Erro:', error.message);
    throw error;
  }
}

// Uso:
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];
const html = await compileGui(file);
document.getElementById('result').innerHTML = html;
```

**Exemplo com React:**
```jsx
import { useState } from 'react';

function CompileGui() {
  const [html, setHtml] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file || !file.name.endsWith('.gui')) {
      setError('Por favor, selecione um arquivo .gui');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(
        'https://screenshot-to-code-api-production.up.railway.app/compile-gui',
        {
          method: 'POST',
          body: formData
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao compilar');
      }

      const htmlContent = await response.text();
      setHtml(htmlContent);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".gui"
        onChange={handleFileUpload}
        disabled={loading}
      />
      {loading && <p>Compilando...</p>}
      {error && <p style={{ color: 'red' }}>Erro: {error}</p>}
      {html && (
        <div dangerouslySetInnerHTML={{ __html: html }} />
      )}
    </div>
  );
}
```

**Exemplo com Fetch API (vanilla JS):**
```javascript
const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const result = document.getElementById('result');

const API_BASE = 'https://screenshot-to-code-api-production.up.railway.app';

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  if (!fileInput.files.length) {
    alert('Escolha um arquivo .gui');
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  result.innerText = 'Enviando...';

  try {
    const response = await fetch(`${API_BASE}/compile-gui`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      result.innerText = 'Erro: ' + (error.detail || response.statusText);
      return;
    }

    const html = await response.text();
    result.innerHTML = '<h3>Resultado</h3>' + html;
  } catch (err) {
    result.innerText = 'Erro de rede: ' + err.message;
  }
});
```

**Exemplo cURL:**
```bash
curl -X POST https://screenshot-to-code-api-production.up.railway.app/compile-gui \
  -F "file=@exemplo.gui" \
  -o resultado.html
```

---

## 🔒 CORS (Cross-Origin Resource Sharing)

A API está configurada para aceitar requisições de qualquer origem (`*`). Se você quiser restringir para domínios específicos, configure a variável de ambiente `ALLOW_ORIGINS` no Railway.

**Configuração atual:**
- `ALLOW_ORIGINS`: `*` (permite todas as origens)
- `ALLOW_METHODS`: `*` (permite todos os métodos)
- `ALLOW_HEADERS`: `*` (permite todos os headers)

---

## 📝 Notas Importantes

1. **Formato do arquivo**: Apenas arquivos `.gui` são aceitos
2. **Tamanho do arquivo**: Não há limite explícito, mas arquivos muito grandes podem causar timeout
3. **Resposta**: O HTML retornado pode ser inserido diretamente no DOM
4. **Erros**: Sempre verifique o status da resposta antes de processar

---

## 🧪 Teste Rápido

```javascript
// Teste de health check
fetch('https://screenshot-to-code-api-production.up.railway.app/healthz')
  .then(res => res.json())
  .then(data => console.log('API Status:', data))
  .catch(err => console.error('Erro:', err));
```

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique se a URL está correta
2. Verifique se o arquivo é `.gui`
3. Verifique os logs do Railway para erros do servidor
4. Teste o endpoint `/healthz` primeiro para confirmar que a API está online

---

**Última atualização**: Backend deployado e funcionando no Railway 🚀
