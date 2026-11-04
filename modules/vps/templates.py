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

    location / {
    location /api {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

        try_files $uri $uri/ /index.html;
    }
}
'''

NGINX_BE = '''server {
    listen 80;
    server_name be.haidinata.my.id;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
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
    ssl_certificate /etc/letsencrypt/live/karta.haidinata.my.id/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/karta.haidinata.my.id/privkey.pem; # managed by Certbot
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
