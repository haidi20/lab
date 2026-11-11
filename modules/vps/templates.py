NGINX_DEFAULT = '''server {
    listen 80 default_server;
    listen 443 ssl default_server;
    server_name _;

    ssl_certificate /etc/letsencrypt/live/haidinata.my.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/haidinata.my.id/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    root /var/www/hello;
    index index.html;

    location /api {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
'''

NGINX_BE = '''server {
    listen 443 ssl;
    server_name be.haidinata.my.id;

    ssl_certificate /etc/letsencrypt/live/be.haidinata.my.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/be.haidinata.my.id/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
server {
    if ($host = be.haidinata.my.id) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name be.haidinata.my.id;
    return 404;
}
'''

NGINX_CI_MONITOR = '''server {
    server_name ci.haidinata.my.id;

    root /var/www/ci-monitor;
    index index.php;

    location / {
        try_files $uri /index.php?$query_string;
    }

    location ~ \\.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;
    }

    location ~ /\\. {
        deny all;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/ci.haidinata.my.id/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/ci.haidinata.my.id/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}server {
    if ($host = ci.haidinata.my.id) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name ci.haidinata.my.id;
    return 404; # managed by Certbot


}
'''

NGINX_KARTA = '''server {
    server_name karta.haidinata.my.id;
    root /var/www/karta/public;
    index index.php;
    client_max_body_size 100M;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \\.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;
    }

    location ~ /\\.(?!well-known) {
        deny all;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/karta.haidinata.my.id/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/karta.haidinata.my.id/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = karta.haidinata.my.id) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name karta.haidinata.my.id;
    return 404; # managed by Certbot


}
'''

NGINX_KLINIK = '''server {
    server_name inventory.haidinata.my.id;
    root /var/www/klinik/src/public;
    index index.php;
    client_max_body_size 100M;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location /app/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    location ~ \\.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;
    }

    location ~ /\\.(?!well-known) {
        deny all;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/inventory.haidinata.my.id/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/inventory.haidinata.my.id/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = inventory.haidinata.my.id) {
        return 301 https://$host$request_uri;
    } # managed by Certbot


    listen 80;
    server_name inventory.haidinata.my.id;
    return 404; # managed by Certbot


}
'''

BE_SERVICE = '''[Unit]
Description=haidi20 BE (Bun + Hono)
After=network.target

[Service]
Type=simple
WorkingDirectory=/var/www/hello-repo/be
ExecStart=/root/.bun/bin/bun run src/index.ts
Environment=PORT=3000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
'''

NGINX_SITES = {
    'default': NGINX_DEFAULT,
    'be-haidi20': NGINX_BE,
    'ci-monitor': NGINX_CI_MONITOR,
    'karta': NGINX_KARTA,
    'klinik': NGINX_KLINIK,
}


def strip_ssl(nginx_block):
    """Remove SSL directives from an nginx server block for HTTP-only bootstrap."""
    lines = []
    skip_until_empty = False
    for line in nginx_block.splitlines():
        stripped = line.strip()
        if stripped.startswith('ssl_') or stripped.startswith('include /etc/letsencrypt'):
            if stripped.endswith(';'):
                continue
            skip_until_empty = True
            continue
        if skip_until_empty:
            if stripped.endswith(';'):
                skip_until_empty = False
                continue
            continue
        if 'listen 443 ssl' in stripped and 'default_server' in stripped:
            lines.append(line.replace('443 ssl', '443'))
        elif 'listen 443 ssl;' in stripped:
            lines.append(line.replace('443 ssl;', '443;'))
        elif stripped.startswith('# managed by Certbot'):
            continue
        else:
            lines.append(line)
    return '\n'.join(lines)

CICD_PORTFOLIO = '''name: Deploy Portfolio
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v2
      - run: cd fe && bun install && bun run build
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: root
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /var/www/hello-repo && git pull
            cd fe && bun install && bun run build
            rm -rf /var/www/hello && mkdir -p /var/www/hello
            cp -r fe/dist/. /var/www/hello/
            systemctl reload nginx
'''

CICD_LARAVEL = '''name: Deploy {name}
on:
  push:
    branches: [{branch}]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: root
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd {repo_dir} && git pull origin {branch}
            composer install --no-dev --optimize-autoloader
            php artisan migrate --force
            php artisan config:cache && php artisan route:cache
            systemctl reload nginx
'''
