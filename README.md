# Sistema de Mensajería Segura

Sistema local de mensajería segura desarrollado en Python con FastAPI, PostgreSQL, Docker y React. El proyecto implementa autenticación segura, cifrado híbrido, firmas digitales, blockchain simplificado y autenticación multifactor con TOTP.

---

## Objetivo General

Construir una aplicación de mensajería segura que permita registrar usuarios, proteger sus credenciales y llaves, intercambiar mensajes cifrados y firmados, verificar la integridad de los mensajes y registrar cada transacción en una mini blockchain, todo dentro de un entorno local y reproducible con Docker.

---

## Funcionalidades Implementadas

### Gestión de Identidad y Hashing

- Registro de usuarios con nombre, correo único y contraseña
- Hashing de contraseñas con Argon2id
- Generación automática de par de llaves RSA 2048
- Almacenamiento de llave pública en formato PEM
- Cifrado de llave privada con clave derivada usando PBKDF2HMAC y AES GCM
- Login con verificación de credenciales
- Emisión de JWT

### Cifrado Híbrido de Mensajes

- Cifrado individual con AES-256 GCM
- Cifrado de clave AES con RSA-OAEP
- Descifrado end-to-end
- Mensajería grupal con una clave AES compartida y cifrada por miembro
- Recuperación de mensajes descifrados desde API

### Firmas Digitales y Blockchain

- Firma digital del hash SHA-256 del mensaje
- Verificación de firma al recuperar mensajes
- Detección de firma inválida y alerta al usuario
- Mini blockchain con bloque génesis
- Encadenamiento de hashes
- Proof of work simplificado
- Registro automático de transacciones al enviar mensajes
- Verificación de integridad de la cadena

### MFA e Integración Final

- Activación de MFA con TOTP compatible con Google Authenticator
- Flujo de login con MFA
- Access token y refresh token
- Endpoints protegidos con JWT
- Frontend React para demostrar el flujo completo
- Despliegue local con Docker Compose

---

## Tecnologías Utilizadas

### Backend

- Python 3.12.10
- FastAPI
- SQLAlchemy
- PostgreSQL
- Argon2id
- Cryptography
- PyJWT
- PyOTP
- Qrcode

### Frontend

- React
- Vite
- JavaScript
- CSS

### Infraestructura

- Docker
- Docker Compose

---

## Estructura del Proyecto

```text
proyecto2/
├─ README.md
├─ docker-compose.yml
├─ Dockerfile
├─ requirements.txt
├─ pytest.ini
├─ docs/
│  ├─ arquitectura.md
│  └─ analisis.md
├─ src/
│  ├─ api/
│  ├─ auth/
│  ├─ users/
│  ├─ crypto/
│  ├─ signatures/
│  ├─ blockchain/
│  └─ frontend/
│     ├─ package.json
│     ├─ vite.config.js
│     ├─ index.html
│     └─ src/
│        ├─ App.jsx
│        ├─ main.jsx
│        ├─ styles.css
│        └─ servicios/
│           └─ api.js
└─ tests/
```

---

## Endpoints Principales

### Autenticación

| Método | Endpoint           |
| ------ | ------------------ |
| `POST` | `/auth/register`   |
| `POST` | `/auth/login`      |
| `POST` | `/auth/mfa/enable` |
| `POST` | `/auth/mfa/verify` |
| `POST` | `/auth/mfa/login`  |
| `POST` | `/auth/refresh`    |

### Usuarios

| Método | Endpoint              |
| ------ | --------------------- |
| `GET`  | `/users/{userId}/key` |

### Mensajes

| Metodo | Endpoint                     |
| ------ | ---------------------------- |
| `POST` | `/groups`                    |
| `POST` | `/messages/{destId}`         |
| `POST` | `/groups/{groupId}/messages` |
| `GET`  | `/messages/{userId}`         |

### Grupos

| Metodo | Endpoint                     |
| ------ | ---------------------------- |
| `POST` | `/groups`                    |
| `POST` | `/messages/{destId}`         |
| `POST` | `/groups/{groupId}/messages` |
| `GET`  | `/messages/{userId}`         |

### Blockchain

| Método | Endpoint             |
| ------ | -------------------- |
| `GET`  | `/blockchain`        |
| `GET`  | `/blockchain/verify` |

---

## Cómo Correr el Backend

### Requisitos Previos

Debe tener instalado:

- Docker Desktop
- Docker Compose
- Node.js

> No es necesario instalar PostgreSQL localmente si va a usar Docker.

### Paso 1 — Abrir el proyecto

Ubicarse en la raíz del proyecto:

```bash
cd Sistema-Mensajeria-Segura
```

### Paso 2 — Levantar backend y base de datos

Desde la raíz del proyecto ejecutar:

```bash
docker compose up --build
```

Esto levanta:

- La API FastAPI
- La base de datos PostgreSQL

### Paso 3 — Verificar que el backend esté arriba

Abrir en el navegador:

```
http://localhost:8000/docs
```

También puede verificar el estado de salud:

```
http://localhost:8000/salud/db
```

Si todo está bien, la API debe responder que la base de datos está conectada.

---

## Cómo Correr el Frontend React

El frontend se ejecuta por separado en modo desarrollo con Vite.

### Requisitos Previos del Frontend

Debe tener instalado Node.js. Para verificarlo:

```bash
node -v
npm -v
```

### Paso 1 — Entrar a la carpeta del frontend

```bash
cd src/frontend
```

### Paso 2 — Instalar dependencias

```bash
npm install
```

### Paso 3 — Levantar el frontend

```bash
npm run dev
```

### Paso 4 — Abrir el frontend

```
http://localhost:5173
```

> El frontend usa proxy hacia `http://localhost:8000`, por lo que el backend debe estar ejecutándose al mismo tiempo.

---

### Para conectarse a la base de datos desde cli en caso se necesite verificar algo

```bash
docker exec -it sistema_mensajeria_db psql -U postgres -d sistema_mensajeria_segura
```

## Flujo Recomendado para Probar el Sistema

### Prueba Básica Completa

1. Registrar dos usuarios
2. Iniciar sesión con uno de ellos
3. Activar MFA si se desea probar la fase 4 completa
4. Completar login con MFA
5. Enviar mensaje individual firmado y cifrado a otro usuario
6. Iniciar sesión con el destinatario
7. Recuperar mensajes
8. Verificar que el mensaje se descifra y la firma aparece como **verificada**
9. Consultar blockchain
10. Verificar integridad de la cadena

### Prueba Grupal

1. Registrar tres usuarios
2. Iniciar sesión con el creador
3. Crear grupo
4. Enviar mensaje grupal
5. Iniciar sesión con otro miembro
6. Recuperar mensajes
7. Confirmar que el mensaje grupal se descifra correctamente

---

## Cómo Ejecutar los Tests

Con los contenedores arriba, ejecutar:

```bash
docker exec -it sistema_mensajeria_api pytest -v
```

Esto corre todos los tests de:

- Módulo 1
- Módulo 2
- Módulo 3
- Módulo 4

---
