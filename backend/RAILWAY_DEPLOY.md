# Guia de Deploy no Railway

Este guia explica como fazer o deploy do backend no Railway usando as informações fornecidas.

## Informações do Projeto

- **URL do Backend**: `https://screenshot-to-code-api-production.up.railway.app/`
- **Token do Railway**: `2dac2ae7-2dfd-4c05-a61d-00cf94b56fbf`

## Método 1: Deploy via Railway CLI

### Pré-requisitos

1. Instale o Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Faça login no Railway:
   ```bash
   railway login
   ```

### Deploy

1. Navegue até a pasta do backend:
   ```bash
   cd backend
   ```

2. Inicialize o projeto Railway (se ainda não estiver inicializado):
   ```bash
   railway init
   ```

3. Configure o projeto existente:
   ```bash
   railway link
   ```
   Use o token: `2dac2ae7-2dfd-4c05-a61d-00cf94b56fbf`

4. Configure as variáveis de ambiente (opcional):
   ```bash
   railway variables set ALLOW_ORIGINS=https://seu-frontend.vercel.app
   ```

5. Faça o deploy:
   ```bash
   railway up
   ```

## Método 2: Deploy via GitHub (Recomendado)

### Passos

1. **Conecte o Repositório GitHub ao Railway**:
   - Acesse [Railway Dashboard](https://railway.app)
   - Clique em "New Project"
   - Selecione "Deploy from GitHub repo"
   - Escolha o repositório `Screenshot-to-code`

2. **Configure o Serviço**:
   - **Root Directory**: Deixe vazio (ou configure como raiz do projeto)
   - **Build Command**: (deixe vazio, o Dockerfile cuidará disso)
   - **Start Command**: (deixe vazio, o Dockerfile cuidará disso)
   - **Dockerfile Path**: `backend/Dockerfile`

3. **Configure as Variáveis de Ambiente**:
   - Clique em "Variables"
   - Adicione as seguintes variáveis (se necessário):
     - `ALLOW_ORIGINS`: URL do seu frontend (ex: `https://seu-frontend.vercel.app`)
     - `PORT`: Será definido automaticamente pelo Railway

4. **Deploy**:
   - O Railway detectará automaticamente o Dockerfile
   - O deploy será feito automaticamente a cada push no GitHub

## Método 3: Deploy Manual via Railway Dashboard

1. Acesse o Railway Dashboard
2. Crie um novo projeto
3. Selecione "Empty Project"
4. Clique em "New" > "GitHub Repo"
5. Conecte seu repositório
6. Configure:
   - **Service Name**: `screenshot-to-code-api`
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Port**: `8000` (ou deixe o Railway definir automaticamente)
7. Configure as variáveis de ambiente
8. Clique em "Deploy"

## Verificação do Deploy

Após o deploy, verifique se está funcionando:

```bash
# Health check
curl https://screenshot-to-code-api-production.up.railway.app/healthz

# Deve retornar: {"status":"ok"}

# Teste do endpoint principal
curl https://screenshot-to-code-api-production.up.railway.app/

# Deve retornar uma página HTML simples
```

## Configuração de Domínio Personalizado

1. No Railway Dashboard, vá para o seu projeto
2. Clique em "Settings"
3. Em "Domains", adicione seu domínio personalizado (opcional)

## Troubleshooting

### Problema: Erro ao importar Bootstrap.compiler.classes

**Solução**: Certifique-se de que o Dockerfile está copiando todo o repositório:
```dockerfile
COPY . /app
```

### Problema: Porta não encontrada

**Solução**: O Railway define automaticamente a variável `PORT`. Certifique-se de que o Dockerfile usa `${PORT:-8000}`.

### Problema: CORS errors

**Solução**: Configure a variável de ambiente `ALLOW_ORIGINS` com a URL exata do seu frontend.

### Problema: Arquivo DSL mapping não encontrado

**Solução**: Verifique se o arquivo `backend/assets/web-dsl-mapping.json` existe e está sendo copiado pelo Dockerfile.

## Monitoramento

- Acesse o Railway Dashboard para ver logs em tempo real
- Use `railway logs` no CLI para ver os logs
- Configure alertas no Railway Dashboard para monitorar o serviço

## Atualizações

Para atualizar o backend:

1. Faça as alterações no código
2. Faça commit e push para o GitHub
3. O Railway fará o deploy automaticamente (se configurado)
4. Ou execute `railway up` manualmente

## Suporte

Para mais informações, consulte:
- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)

