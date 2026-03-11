# Portal da Transparencia - Instituto Meio do Mundo

Aplicacao principal em Django (site publico, admin, API REST e e-SIC).

## Padrao de deploy adotado
- Backend unico: Django (`portal_transparencia`)
- Banco em producao: PostgreSQL via `DATABASE_URL`
- Servidor: Gunicorn
- Arquivos estaticos: WhiteNoise

## Requisitos
- Python 3.12+
- pip
- (opcional) Docker + Docker Compose

## Setup local (Python)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Para desenvolvimento local rapido, voce pode deixar sem `DATABASE_URL` e usar SQLite.

## Rodar local
```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Rodar com Docker (web + postgres)
```bash
copy .env.example .env
docker compose up --build -d
```

URLs:
- App: `http://localhost:8000/`
- Healthcheck: `http://localhost:8000/health/`
- Admin: `http://localhost:8000/admin/`

## Variaveis obrigatorias em producao
- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY=<chave-forte>`
- `DJANGO_ALLOWED_HOSTS=<dominio1,dominio2>`
- `DATABASE_URL=postgresql://usuario:senha@host:5432/banco`

Opcao equivalente ao `DATABASE_URL`: informar `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (e opcionalmente `DB_SSLMODE`).
A aplicacao monta a `DATABASE_URL` automaticamente a partir dessas variaveis.

Em producao, a aplicacao falha na inicializacao de forma explicita se faltar `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` e nenhuma das opcoes de banco (`DATABASE_URL` ou `DB_*`) estiver configurada.
`DATABASE_URL` com SQLite tambem e bloqueado em producao.

Para Vercel sem Postgres provisionado, existe fallback controlado por `ALLOW_VERCEL_SQLITE_FALLBACK=true`.
Nesse modo, o app usa SQLite em `/tmp/vercel.sqlite3` e pode rodar `migrate` automaticamente no boot (`DJANGO_AUTO_MIGRATE_ON_BOOT=true`).
Se precisar acessar o admin nesse modo, configure `DJANGO_BOOTSTRAP_ADMIN_PASSWORD` (e opcionalmente `DJANGO_BOOTSTRAP_ADMIN_USERNAME`/`DJANGO_BOOTSTRAP_ADMIN_EMAIL`) para criar ou atualizar um superusuario no boot.

## Comandos de verificacao
```bash
python manage.py check
python manage.py test
python manage.py check --deploy
```

## Configurar DB na Vercel (script)
Se preferir, use o script interativo para preencher e salvar `DB_*` direto na Vercel:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-vercel-db.ps1 -Scope fabio-anselmos-projects -SetDatabaseUrl -Deploy
```

## Checklist de subida em hospedagem
1. Configurar variaveis de ambiente.
2. Executar migrations.
3. Executar collectstatic.
4. Subir Gunicorn com `portal_transparencia.wsgi:application`.
5. Validar `/health/` retornando `{"status":"ok"}`.
6. Validar login em `/admin/`.
