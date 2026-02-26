# Portal da Transparencia - Instituto Meio do Mundo

Projeto Django para portal institucional com:
- site publico de transparencia
- area administrativa customizada
- API REST (DRF)
- formulario e-SIC

## Requisitos
- Python 3.12+ (recomendado)
- pip

## Instalar
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configurar ambiente
1. Copie `.env.example` para `.env`.
2. Preencha:
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_DEBUG`

## Rodar local
```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Testes e checks
```bash
python manage.py check
python manage.py test
python manage.py check --deploy
```

## Publicacao (deploy)
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Use servidor WSGI/ASGI (Gunicorn/Uvicorn + Nginx/Proxy).  
Nao use `runserver` em producao.

## GitHub - primeiro envio
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <URL_DO_REPOSITORIO>
git push -u origin main
```

## Observacoes
- `db.sqlite3`, `media/`, `.venv/` e `staticfiles/` estao no `.gitignore`.
- Se quiser versionar arquivos de exemplo de media, use uma pasta separada como `samples/`.
