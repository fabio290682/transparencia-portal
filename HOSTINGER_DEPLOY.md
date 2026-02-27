# Deploy na Hostinger (VPS) - Django Dinamico

Este projeto ficou pronto para deploy backend completo (sem site estatico).

## 1) Preparar VPS (Ubuntu)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip nginx
```

## 2) Subir codigo
```bash
cd /var/www
sudo git clone https://github.com/SEU_USUARIO/SEU_REPO.git portal
cd portal
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 3) Variaveis de ambiente (.env)
Crie `/var/www/portal/.env`:
```env
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=gere-uma-chave-forte
DJANGO_ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
DATABASE_URL=postgresql://USUARIO:SENHA@HOST:5432/NOME_DB
```

## 4) Migrar e coletar static
```bash
set -a
source .env
set +a
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

## 5) Service systemd (Gunicorn)
Crie `/etc/systemd/system/portal.service`:
```ini
[Unit]
Description=Portal Django Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/portal
EnvironmentFile=/var/www/portal/.env
ExecStart=/var/www/portal/.venv/bin/gunicorn portal_transparencia.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative:
```bash
sudo systemctl daemon-reload
sudo systemctl enable portal
sudo systemctl start portal
sudo systemctl status portal
```

## 6) Nginx reverse proxy
Crie `/etc/nginx/sites-available/portal`:
```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/portal/staticfiles/;
    }

    location /media/ {
        alias /var/www/portal/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Ative:
```bash
sudo ln -s /etc/nginx/sites-available/portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 7) SSL (Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

## 8) Atualizar aplicacao
```bash
cd /var/www/portal
git pull
source .venv/bin/activate
pip install -r requirements.txt
set -a && source .env && set +a
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart portal
```

