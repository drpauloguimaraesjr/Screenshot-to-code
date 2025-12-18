const form = document.getElementById('uploadForm')
const fileInput = document.getElementById('fileInput')
const result = document.getElementById('result')

// API base URL (change if you redeploy backend elsewhere)
const API_BASE = 'https://screenshot-to-code-api-production.up.railway.app'

form.addEventListener('submit', async (e) => {
  e.preventDefault()
  if (!fileInput.files.length) return alert('Escolha um arquivo .gui')
  const file = fileInput.files[0]
  const fd = new FormData()
  fd.append('file', file)

  result.innerText = 'Enviando...'

  try {
    const resp = await fetch(`${API_BASE}/compile-gui`, { method: 'POST', body: fd })
    if (!resp.ok) {
      const err = await resp.json()
      result.innerText = 'Erro: ' + (err.detail || resp.statusText)
      return
    }
    const html = await resp.text()
    result.innerHTML = '<h3>Resultado</h3>' + html
  } catch (err) {
    result.innerText = 'Erro de rede: ' + err.message
  }
})
