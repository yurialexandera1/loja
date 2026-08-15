#!/usr/bin/env bash
# Como ROOT: sudo bash /home/yuri/loja_django/deploy/setup.sh
set -euo pipefail
APP=/home/yuri/loja_django
ln -sfn $APP /opt/loja
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='loja'" | grep -q 1; then echo 'role loja ja existe'; else sudo -u postgres psql -c "CREATE ROLE loja WITH LOGIN PASSWORD 'loja_senha_45';"; fi
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='loja'" | grep -q 1; then echo 'db loja ja existe'; else sudo -u postgres psql -c "CREATE DATABASE loja OWNER loja;"; fi
cp $APP/deploy/loja.socket /etc/systemd/system/loja.socket
cp $APP/deploy/loja.service /etc/systemd/system/loja.service
if [ -f /etc/nginx/sites-available/loja ]; then echo 'nginx site ja existe'; else cp $APP/deploy/nginx-loja.conf /etc/nginx/sites-available/loja; ln -sf /etc/nginx/sites-available/loja /etc/nginx/sites-enabled/loja; fi
sudo -u yuri bash -c "cd $APP && source venv/bin/activate && python manage.py migrate && python manage.py collectstatic --noinput"
systemctl daemon-reload
systemctl enable loja.socket loja.service
systemctl restart loja.socket loja.service
nginx -t && systemctl reload nginx
echo 'Loja instalada em http://45.231.36.139 (Postgres + gunicorn + nginx)'
