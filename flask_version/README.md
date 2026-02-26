# Versao Flask

Esta pasta contem uma versao do portal em Flask.

## Instalar
```bash
cd flask_version
..\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
```

## Executar
```bash
cd flask_version
..\\.venv\\Scripts\\python.exe app.py
```

Acesse: `http://127.0.0.1:5000/`

## Endpoints
- `GET /` portal
- `POST /api/esic/submit/` envio e-SIC
- `GET /health` healthcheck

## Banco
- SQLite local: `flask_version/flask_portal.db`
