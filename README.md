# Projeto Sala de Som — Simulador

App Streamlit para planeamento financeiro de uma sala de ensaios + gravação de música em Portugal.

## Correr localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

A app abre em `http://localhost:8501`. Password: `projetosaladesom`.

## Deploy no Streamlit Community Cloud

1. Cria uma conta gratuita em https://streamlit.io/cloud (login com GitHub).
2. Cria um repositório novo no GitHub (público ou privado) e faz push desta pasta:
   ```bash
   cd "Projeto Sala de Som"
   git init
   git add .
   git commit -m "Initial commit — simulador Sala de Som"
   git branch -M main
   git remote add origin https://github.com/<o-teu-user>/projeto-sala-de-som.git
   git push -u origin main
   ```
3. Em https://share.streamlit.io/ clica **New app**.
4. Escolhe o repositório, branch `main`, `Main file path` = `app.py`.
5. Clica **Deploy**. Ao fim de ~2 minutos tens um URL público.
6. Partilha o URL — quem tiver o link e a password entra e edita os valores.

### Notas
- Streamlit Community Cloud é gratuito para apps públicas.
- Não é preciso configurar `secrets.toml`: a password é literal no código (é apenas um menu de entrada, não segurança real).
- Cada visitante tem a sua própria sessão — as alterações não se cruzam entre utilizadores. Para partilhar uma "versão", basta cada um fazer download do Excel.
