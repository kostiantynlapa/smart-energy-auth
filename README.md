# Система автентифікації та API-шлюз — Smart Energy

MVP-реалізація мікросервісу автентифікації та API-шлюзу для проєкту Smart Energy.

## Сервіси

### 1. Сервіс автентифікації (порт 8001)

**Призначення**: реєстрація користувачів та генерація JWT-токенів з 2FA через TOTP.

**Ендпоінти**:

#### POST `/register`
Реєстрація нового користувача та налаштування TOTP для 2FA.

Запит:
```json
{
  "username": "alice",
  "password": "SecurePass123!",
  "allowed_storages": ["postgres", "mongodb"]
}
```

Відповідь:
```json
{
  "qr_code_base64": "iVBORw0KGgoAAAANSUhEUg...",
  "totp_secret": "JBSWY3DPEBLW64TMMQ======"
}
```

Кроки:
1. Відскануйте QR-код у застосунку Google Authenticator
2. Збережіть `totp_secret` як резервний варіант
3. Тепер у користувача увімкнено 2FA

#### POST `/login`
Автентифікація користувача за паролем та TOTP-кодом для отримання JWT.

Запит:
```json
{
  "username": "alice",
  "password": "SecurePass123!",
  "totp_code": "123456"
}
```

Відповідь:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Вміст JWT** (після декодування):
```json
{
  "sub": "alice",
  "allowed_storages": ["postgres", "mongodb"],
  "exp": 1708367400
}
```

#### GET `/health`
Перевірка стану сервісу.

Відповідь:
```json
{
  "status": "healthy"
}
```

---

### 2. API-шлюз (порт 8000)

**Призначення**: маршрутизація запитів з перевіркою JWT та контролем доступу (RBAC).

**Ендпоінти**:

#### POST `/query`
Виконання запиту до конкретного сховища з JWT-авторизацією.

**Вимоги**:
- Заголовок `Authorization: Bearer <JWT>`
- Токен має містити `db_type` у claims `allowed_storages`

Запит:
```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgres",
    "query": "SELECT * FROM users"
  }'
```

Відповідь (200 OK):
```json
{
  "result": "mock data from postgres",
  "source": "postgres",
  "message": "Query executed on postgres for user alice"
}
```

**Помилки**:

| Ситуація | Код | Повідомлення |
|---|---|---|
| Відсутній заголовок Authorization | 401 | Missing Authorization header |
| Невірний формат заголовка | 401 | Invalid Authorization header format |
| Невалідний або прострочений токен | 401 | Invalid or expired token |
| Немає доступу до сховища | 403 | Access denied to storage: mongodb |

---

## Встановлення та запуск

### Вимоги
- Python 3.12+
- pip

### Встановлення залежностей

```bash
pip install -r requirements.txt
```

**requirements.txt** включає:
- fastapi
- uvicorn
- passlib[bcrypt]
- pyotp
- python-jose[cryptography]
- qrcode[pil]
- python-dotenv
- pydantic
- pydantic-settings

### Налаштування змінних середовища

Обидва сервіси використовують `SECRET_KEY` з файлу `.env`:

**auth_service/.env**:
```env
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars-12345
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

**gateway/.env**:
```env
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars-12345
```

⚠️ **ВАЖЛИВО**: обидва сервіси повинні використовувати **однаковий SECRET_KEY**!

---

## Запуск сервісів

### Термінал 1: Сервіс автентифікації (порт 8001)

```bash
cd smart-energy-auth
uvicorn auth_service.main:app --port 8001 --reload
```

Swagger UI: http://localhost:8001/docs

### Термінал 2: API-шлюз (порт 8000)

```bash
cd smart-energy-auth
uvicorn gateway.main:app --port 8000 --reload
```

Swagger UI: http://localhost:8000/docs

---

## Повний приклад використання

### Крок 1: Реєстрація

```bash
curl -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "MySecurePass123!",
    "allowed_storages": ["postgres", "mongodb"]
  }'
```

Збережіть `totp_secret`. Відскануйте QR-код у Google Authenticator.

### Крок 2: Отримання TOTP-коду

У застосунку-автентифікаторі з'явиться 6-значний код, який оновлюється кожні 30 секунд.

### Крок 3: Вхід та отримання JWT

```bash
curl -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "MySecurePass123!",
    "totp_code": "123456"
  }'
```

### Крок 4: Запит через шлюз

```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <ваш_токен>" \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgres",
    "query": "SELECT * FROM users"
  }'
```

### Крок 5: Перевірка RBAC

Користувач alice має доступ лише до `["postgres", "mongodb"]`. Спроба звернутися до `hdfs`:

```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <ваш_токен>" \
  -H "Content-Type: application/json" \
  -d '{"db_type": "hdfs"}'
```

Відповідь (403 Forbidden):
```json
{
  "detail": "Access denied to storage: hdfs"
}
```

---

## Безпека

### Автентифікація
- ✅ Хешування паролів bcrypt (з сіллю, відповідає NIST)
- ✅ TOTP 2FA з підтримкою Google Authenticator
- ✅ Допуск розсинхронізації годинника ±30 секунд

### Авторизація
- ✅ Stateless JWT-автентифікація
- ✅ RBAC — контроль доступу на рівні сховищ
- ✅ Термін дії токена (за замовчуванням 15 хвилин)

### API-шлюз
- ✅ Перевірка Bearer-токена
- ✅ Загальні повідомлення про помилки (без витоку інформації)
- ✅ RBAC на рівні кожного запиту
- ✅ CORS увімкнено для MVP

---

## Структура проєкту

```
smart-energy-auth/
├── auth_service/
│   ├── __init__.py
│   ├── main.py                # Головний FastAPI-застосунок
│   ├── models.py              # Pydantic-схеми
│   ├── users_db.py            # Сховище в пам'яті
│   ├── config.py              # Налаштування
│   ├── .env                   # Змінні середовища
│   └── utils/
│       ├── __init__.py
│       ├── password.py        # Утиліти bcrypt
│       ├── totp.py            # Генерація та перевірка TOTP
│       └── jwt.py             # Створення та перевірка JWT
│
├── gateway/
│   ├── __init__.py
│   ├── main.py                # API-шлюз
│   └── .env                   # Змінні середовища
│
├── admin_ui/
│   └── index.html             # Адмін-панель
│
├── auth_ui/
│   ├── index.html             # Сторінка входу
│   └── register.html          # Сторінка реєстрації
│
├── requirements.txt
└── README.md
```

---

## Тестування через Swagger UI

### Сервіс автентифікації
Відкрийте http://localhost:8001/docs

1. Виконайте `POST /register` з тестовими даними
2. Відскануйте QR-код і отримайте TOTP-код
3. Виконайте `POST /login` з TOTP-кодом
4. Скопіюйте JWT-токен

### API-шлюз
Відкрийте http://localhost:8000/docs

1. Натисніть кнопку "Authorize" (вгорі праворуч)
2. Введіть токен у форматі `Bearer <токен>`
3. Спробуйте `POST /query`


## Документація API

- Сервіс автентифікації: http://localhost:8001/docs
- API-шлюз: http://localhost:8000/docs