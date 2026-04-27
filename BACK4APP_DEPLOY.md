# Deploy na Back4app Containers (Django completo)

Este projeto esta pronto para deploy dinamico com Docker na Back4app.

## 1) Estrutura usada
- `Dockerfile`
- `entrypoint.sh` (migrate + collectstatic + gunicorn)
- `requirements.txt`

## 2) Subir para GitHub
```bash
git add .
git commit -m "Prepare Back4app deployment"
git push origin main
```

## 3) Criar app na Back4app
1. Acesse Back4app Containers.
2. Clique em **Create New App**.
3. Escolha **GitHub** e conecte seu repositório.
4. Branch: `main`.
5. Deploy.

## 4) Variaveis de ambiente obrigatorias
Defina no painel da Back4app:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY=<chave-forte>`
- `DJANGO_ALLOWED_HOSTS=<seu-app>.b4a.app`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://<seu-app>.b4a.app`
- `DATABASE_URL=<url-postgres>`

Opcional:
- `GUNICORN_WORKERS=3`
- `GUNICORN_TIMEOUT=120`

## 5) Banco de dados
Use PostgreSQL gerenciado (Back4app DB ou externo).
Exemplo:
`postgresql://usuario:senha@host:5432/nome_db`

## 6) Pos-deploy
No primeiro deploy, `entrypoint.sh` ja executa:
- `python manage.py migrate`
- `python manage.py collectstatic --noinput`

Para criar admin:
```bash
python manage.py createsuperuser
```
(execute no terminal do container)

## 7) Verificacao
- Home: `https://<seu-app>.b4a.app/`
- Admin: `https://<seu-app>.b4a.app/admin/`

