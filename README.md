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
├─ docker-compose.app.yml
├─ docker-compose.sonarqube.yml
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

## Levantar el proyecto y SonarQube

Necesitas Docker Desktop abierto y Node.js instalado. Los dos archivos Compose
están en la raíz: `docker-compose.app.yml` levanta la API y su PostgreSQL;
`docker-compose.sonarqube.yml` levanta SonarQube y su propio PostgreSQL. Ejecuta
los comandos siguientes en **PowerShell**, desde la raíz del repositorio.

1. **Preparar la aplicación (solo la primera vez).** Si ya tienes `.env`, omite
   este paso. Si no, créalo y reemplaza `JWTClaveSecreta` y
   `BaseDatosPassword` por valores privados. No subas `.env` a Git.

   ```powershell
   Copy-Item .env.example .env
   ```

2. **Levantar la API y su base de datos.**

   ```powershell
   docker compose -f docker-compose.app.yml up -d --build
   ```

   Comprueba la API en **http://localhost:17841/docs**.

3. **Levantar el frontend.** En otra terminal PowerShell, desde la raíz:

   ```powershell
   cd src/frontend
   npm ci
   npm run dev
   ```

   Abre **http://localhost:18473**. Deja abierta esta terminal mientras uses
   el frontend.

4. **Levantar SonarQube.** En una terminal PowerShell situada en la raíz:

   ```powershell
   docker compose -f docker-compose.sonarqube.yml -p sonar-lab up -d
   ```

   Abre **http://localhost:9000**. En una instalación nueva, entra con
   `admin` / `admin` y cambia la contraseña; si ya lo configuraste, usa tu
   contraseña actual. `-p sonar-lab` conserva los datos de la instalación
   previa del laboratorio.

**Para detener todo:** pulsa `Ctrl+C` en la terminal del frontend. Desde la
raíz, ejecuta estos dos comandos; `down` no borra los volúmenes de datos:

```powershell
docker compose -f docker-compose.app.yml down
docker compose -f docker-compose.sonarqube.yml -p sonar-lab down
```

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

Con los contenedores arriba, crear una sola vez una base local exclusiva para
tests (si ya existe, omitir el primer comando) y ejecutar:

```bash
docker compose -f docker-compose.app.yml exec -T db createdb -U postgres sistema_mensajeria_segura_test
docker compose -f docker-compose.app.yml run --rm --no-deps -e BaseDatosNombre=sistema_mensajeria_segura_test api pytest -v --cov=src --cov-branch --cov-report=xml:coverage.xml
```

Esto corre todos los tests de:

- Módulo 1
- Módulo 2
- Módulo 3
- Módulo 4

---

## Preparación del laboratorio DAST

`docker-compose.sonarqube.yml` contiene el Compose del curso para SonarQube;
`docker-compose.app.yml` levanta la aplicación y su base de datos. El archivo
`sonar-project.properties` define la versión
`fase1`, el código fuente, los tests y la ruta del reporte de cobertura. El
token de SonarQube se pasa como variable de entorno `SONAR_TOKEN` en la sesión
del terminal; no se guarda en archivos ni en el repositorio.

El comando anterior genera `coverage.xml` desde la raíz del repositorio. Los
tests limpian todas las tablas de la base de datos configurada; por eso usan
`sistema_mensajeria_segura_test` y no la base de la aplicación. Luego se puede
ejecutar `sonar-scanner` desde la raíz, con SonarQube activo en
`http://localhost:9000` y `SONAR_TOKEN` definido en el entorno. En la interfaz
de SonarQube, configurar *New Code* como *Previous version* y el Quality Gate
del curso.

Para importar Semgrep en el mismo análisis, generar el SARIF y pasar al escáner
`-Dsonar.sarifReportPaths=artifacts/fase1/entrega/semgrep.sarif`. El escaneo de
Fase 1 ya importó ese archivo; el registro local está en
`artifacts/fase1/soporte/sonar-scan-semgrep.log`. El token se introduce en la
sesión del terminal cuando se ejecuta el análisis y se borra de esa sesión al
terminar; nunca se pega en un comando guardado, captura o reporte.

Para ZAP, usar el frontend `http://localhost:18473` y la definición OpenAPI
`http://localhost:17841/openapi.json` para el API scan. Registrar dos usuarios
de prueba después de correr los tests; iniciar sesión sin MFA con uno de ellos
y usar su `accessToken` como encabezado `Authorization: Bearer <token>` en las
peticiones autenticadas de ZAP. El token vence según `JWTMinutosExpiracion` en
`.env`, así que hay que renovarlo antes de un escaneo prolongado. Los datos y
tokens de prueba deben mantenerse fuera del repositorio y de las capturas.

Para la Fase 2, cambiar `sonar.projectVersion` a `fase2`, generar de nuevo
`coverage.xml` con las pruebas de regresión y repetir el escaneo ZAP sobre los
mismos objetivos.
