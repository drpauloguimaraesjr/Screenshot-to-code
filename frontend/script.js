const urlInput = document.getElementById('backendUrl');
const statusEl = document.getElementById('status');
const previewEl = document.getElementById('preview');
const downloadEl = document.getElementById('downloadLink');
const HEALTH_BTN = document.getElementById('checkHealth');
const SITE_URL_INPUT = document.getElementById('siteUrl');
const FETCH_SITE_BTN = document.getElementById('fetchSite');

// Helpers
const getBaseUrl = () => (urlInput.value || '').replace(/\/$/, '');
const saveBaseUrl = () => localStorage.setItem('backendUrl', urlInput.value || '');
const loadBaseUrl = () => localStorage.getItem('backendUrl') || '';

// Init: load from query (?api=...) or localStorage
(() => {
  const qp = new URLSearchParams(window.location.search);
  const fromQuery = qp.get('api');
  const fromLS = loadBaseUrl();
  const initial = fromQuery || fromLS || urlInput.value;
  if (initial) urlInput.value = initial;
})();

urlInput.addEventListener('change', saveBaseUrl);

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const baseUrl = getBaseUrl();
  const fileInput = document.getElementById('guiFile');

  const file = fileInput.files[0];
  if (!file) {
    statusEl.textContent = 'Selecione um arquivo .gui primeiro.';
    return;
  }

  const formData = new FormData();
  formData.append('file', file, file.name);

  statusEl.className = '';
  statusEl.textContent = 'Enviando e gerando HTML...';
  downloadEl.style.display = 'none';
  previewEl.src = 'about:blank';

  try {
    const resp = await fetch(`${baseUrl}/compile-gui`, {
      method: 'POST',
      body: formData,
    });

    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`Erro ${resp.status}: ${errText}`);
    }

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);

    // Mostrar no iframe
    previewEl.src = url;

    // Habilitar download
    downloadEl.href = url;
    downloadEl.download = (file.name.replace(/\.[Gg][Uu][Ii]$/, '') || 'output') + '.html';
    downloadEl.style.display = 'inline-block';

    statusEl.className = 'ok';
    statusEl.textContent = 'HTML gerado com sucesso.';
  } catch (err) {
    statusEl.className = 'err';
    statusEl.textContent = 'Falha ao gerar: ' + err.message;
  }
});

HEALTH_BTN?.addEventListener('click', async () => {
  const baseUrl = getBaseUrl();
  statusEl.className = '';
  statusEl.textContent = 'Testando conexão...';
  try {
    const r = await fetch(`${baseUrl}/healthz`, { method: 'GET' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const js = await r.json().catch(() => ({}));
    statusEl.className = 'ok';
    statusEl.textContent = `OK: ${r.status} ${js.status ? '('+js.status+')' : ''}`;
  } catch (e) {
    statusEl.className = 'err';
    statusEl.textContent = 'Falha de conexão: ' + e.message;
  }
});

FETCH_SITE_BTN?.addEventListener('click', async () => {
  const baseUrl = getBaseUrl();
  const siteUrl = (SITE_URL_INPUT?.value || '').trim();
  if (!siteUrl) {
    statusEl.className = '';
    statusEl.textContent = 'Informe um URL do site.';
    return;
  }

  statusEl.className = '';
  statusEl.textContent = 'Buscando HTML do site...';
  downloadEl.style.display = 'none';
  previewEl.src = 'about:blank';

  try {
    const u = new URL(`${baseUrl}/fetch-url`);
    u.searchParams.set('url', siteUrl);
    const resp = await fetch(u.toString(), { method: 'GET' });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`Erro ${resp.status}: ${errText}`);
    }

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    previewEl.src = url;

    // Nome de arquivo baseado no host
    let downloadName = 'site.html';
    try {
      const parsed = new URL(siteUrl);
      downloadName = (parsed.hostname || 'site') + '.html';
    } catch {}

    downloadEl.href = url;
    downloadEl.download = downloadName;
    downloadEl.style.display = 'inline-block';

    statusEl.className = 'ok';
    statusEl.textContent = 'HTML do site carregado com sucesso.';
  } catch (err) {
    statusEl.className = 'err';
    statusEl.textContent = 'Falha ao buscar site: ' + err.message;
  }
});
