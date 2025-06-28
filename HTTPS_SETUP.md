# 🔒 Настройка HTTPS для SmartAla

Руководство по настройке SSL/HTTPS для вашего приложения SmartAla.

## 🎯 Варианты настройки HTTPS

### Вариант 1: Let's Encrypt (Рекомендуемый для продакшена)
### Вариант 2: Самоподписанные сертификаты (Для тестирования)
### Вариант 3: Cloudflare SSL (Простейший)

---

## 🌟 Вариант 1: Let's Encrypt (Бесплатные SSL сертификаты)

### Требования:
- Доменное имя, указывающее на ваш сервер
- Открытые порты 80 и 443

### Шаг 1: Установка Certbot
```bash
sudo apt update
sudo apt install -y certbot
```

### Шаг 2: Остановка приложения (временно)
```bash
cd ~/smartala
docker-compose down
```

### Шаг 3: Получение SSL сертификата
```bash
# Замените your-domain.com на ваш домен
sudo certbot certonly --standalone -d your-domain.com
```

### Шаг 4: Копирование сертификатов
```bash
# Создание директории для SSL
sudo mkdir -p ~/smartala/ssl

# Копирование сертификатов
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ~/smartala/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ~/smartala/ssl/key.pem

# Установка прав доступа
sudo chown $USER:$USER ~/smartala/ssl/*.pem
chmod 600 ~/smartala/ssl/*.pem
```

### Шаг 5: Обновление nginx.conf
```bash
cd ~/smartala
nano nginx.conf
```

Раскомментируйте и обновите SSL секцию:
```nginx
# HTTPS server (for production)
server {
    listen 443 ssl http2;
    server_name your-domain.com;  # Замените на ваш домен

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozTLS:10m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Proxy to Flask app
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://smartala_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

И обновите HTTP сервер для редиректа на HTTPS:
```nginx
# HTTP server (redirect to HTTPS)
server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}
```

### Шаг 6: Запуск с SSL
```bash
docker-compose up -d --build
```

### Шаг 7: Автообновление сертификатов
```bash
# Создание скрипта обновления
cat > ~/renew-ssl.sh << 'EOF'
#!/bin/bash
sudo certbot renew --quiet
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ~/smartala/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ~/smartala/ssl/key.pem
sudo chown $USER:$USER ~/smartala/ssl/*.pem
cd ~/smartala && docker-compose restart nginx
EOF

chmod +x ~/renew-ssl.sh

# Добавление в crontab для автообновления
echo "0 3 * * * ~/renew-ssl.sh" | crontab -
```

---

## 🔧 Вариант 2: Самоподписанные сертификаты (Для тестирования)

### Шаг 1: Создание самоподписанного сертификата
```bash
cd ~/smartala

# Создание приватного ключа
openssl genrsa -out ssl/key.pem 2048

# Создание сертификата
openssl req -new -x509 -key ssl/key.pem -out ssl/cert.pem -days 365 -subj "/C=KZ/ST=Almaty/L=Almaty/O=SmartAla/CN=localhost"

# Установка прав
chmod 600 ssl/*.pem
```

### Шаг 2: Обновление nginx.conf (как в Варианте 1)
```bash
nano nginx.conf
```

### Шаг 3: Запуск
```bash
docker-compose up -d --build
```

**Примечание**: Браузер будет показывать предупреждение о небезопасном соединении, но вы можете продолжить.

---

## ☁️ Вариант 3: Cloudflare SSL (Самый простой)

### Шаг 1: Регистрация домена в Cloudflare
1. Зарегистрируйтесь на [cloudflare.com](https://cloudflare.com)
2. Добавьте ваш домен
3. Измените DNS серверы у регистратора домена

### Шаг 2: Настройка SSL в Cloudflare
1. Перейдите в SSL/TLS → Overview
2. Выберите "Flexible" или "Full"
3. Включите "Always Use HTTPS"

### Шаг 3: Настройка DNS записи
```
Type: A
Name: @
Content: YOUR_SERVER_IP
Proxy status: Proxied (оранжевое облако)
```

### Шаг 4: Ваше приложение остается на HTTP
Cloudflare автоматически обеспечивает HTTPS между пользователем и Cloudflare.

---

## 🔄 Обновление docker-compose.yml для HTTPS

Если используете Let's Encrypt или самоподписанные сертификаты, обновите `docker-compose.yml`:

```yaml
version: '3.8'

services:
  smartala-app:
    build: .
    container_name: smartala-navigation
    ports:
      - "5002:5002"  # Только внутренний порт
    environment:
      - FLASK_ENV=production
      - GEMINI_API_KEY=AIzaSyAa6831q1q_61pxjnatffMqWQEMPp9jRjQ
      - GOOGLE_MAPS_API_KEY=AIzaSyBI_q34br_taffgYVlIs7hQ25yl3QjEXk0
    volumes:
      - ./audio_uploads:/app/audio_uploads
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - smartala-network

  nginx:
    image: nginx:alpine
    container_name: smartala-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - smartala-app
    restart: unless-stopped
    networks:
      - smartala-network

networks:
  smartala-network:
    driver: bridge
```

---

## 🧪 Проверка HTTPS

### Проверка сертификата
```bash
# Проверка SSL сертификата
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Проверка через curl
curl -I https://your-domain.com
```

### Проверка в браузере
1. Откройте `https://your-domain.com`
2. Проверьте замок в адресной строке
3. Убедитесь, что нет предупреждений

---

## 🚨 Устранение проблем

### Проблема: "SSL certificate problem"
```bash
# Проверка файлов сертификатов
ls -la ~/smartala/ssl/
cat ~/smartala/ssl/cert.pem | openssl x509 -text -noout
```

### Проблема: "Connection refused"
```bash
# Проверка портов
sudo netstat -tulpn | grep :443
docker-compose logs nginx
```

### Проблема: "Mixed content"
Убедитесь, что все ресурсы (CSS, JS, изображения) загружаются через HTTPS.

---

## 📋 Итоговая проверка

После настройки HTTPS ваше приложение будет доступно по адресам:
- `https://your-domain.com` - основной HTTPS доступ
- `http://your-domain.com` - автоматический редирект на HTTPS

### Команды для управления
```bash
# Перезапуск с SSL
docker-compose restart

# Проверка логов SSL
docker-compose logs nginx

# Обновление сертификатов (Let's Encrypt)
~/renew-ssl.sh
```

Выберите подходящий вариант в зависимости от ваших потребностей! 