# Arquitectura del sistema

El sistema fue diseñado como una aplicacion local de mensajeria segura basada en una arquitectura cliente servidor. El backend implementa toda la logica criptografica, de autenticacion, persistencia y verificacion de integridad. El frontend React funciona como interfaz de demostracion para consumir los endpoints del backend y recorrer el flujo funcional completo.

La arquitectura integra cuatro capas principales:

1. gestion de identidad y proteccion de credenciales
2. cifrado hibrido de mensajes
3. firmas digitales y blockchain
4. autenticacion multifactor e integracion final

## Componentes principales

## Backend API
El backend fue construido con FastAPI y concentra:
- registro y autenticacion de usuarios
- generacion y proteccion de llaves
- emision y validacion de JWT
- logica de MFA con TOTP
- cifrado y descifrado de mensajes
- firma y verificacion digital
- gestion de grupos
- registro de transacciones en blockchain
- exposicion de endpoints REST

## Base de datos
PostgreSQL almacena:
- usuarios
- llaves publicas
- llaves privadas cifradas
- secretos TOTP
- grupos y miembros
- mensajes cifrados
- claves cifradas por destinatario
- bloques de la blockchain

## Frontend
El frontend React permite:
- registrar usuarios
- iniciar sesion
- activar MFA
- validar TOTP
- enviar mensajes individuales
- crear grupos
- enviar mensajes grupales
- recuperar mensajes
- consultar blockchain
- verificar integridad de la cadena

## Contenedores
Docker Compose orquesta:
- servicio de base de datos
- servicio de backend

---

## Arquitectura general

```text
+--------------------+          +------------------------+          +----------------------+
|      Frontend      |  HTTP    |      FastAPI API       |  SQL     |      PostgreSQL      |
|   React + Vite     +--------->+  Auth Crypto Chain MFA +--------->+  Datos del sistema   |
|   localhost:5173   |          |    localhost:8000      |          |      puerto 5432     |
+--------------------+          +------------------------+          +----------------------+
```
# Documentación del Sistema

---

## Flujo General del Sistema

```
Usuario
  |
  v
Frontend React
  |
  v
FastAPI
  |
  +--> Módulo Auth
  +--> Módulo Crypto
  +--> Módulo Signatures
  +--> Módulo Blockchain
  +--> Módulo Users
  |
  v
PostgreSQL
```

---

## Módulos del Backend

### Módulo Auth

**Responsabilidades:**
- Registrar usuarios
- Generar hash de contraseña
- Generar par de llaves RSA
- Cifrar llave privada con clave derivada
- Autenticar usuarios
- Emitir access token y refresh token
- Activar y verificar MFA con TOTP

**Archivos principales:**
- `src/auth/modelos.py`
- `src/auth/servicio.py`
- `src/auth/rutas.py`
- `src/auth/seguridad.py`
- `src/auth/criptografia.py`
- `src/auth/tokens.py`
- `src/auth/mfa.py`
- `src/auth/dependencias.py`

---

### Módulo Users

**Responsabilidades:**
- Exponer llave pública del usuario
- Resolver información pública necesaria para cifrado y verificación

**Archivo principal:**
- `src/users/rutas.py`

---

### Módulo Crypto

**Responsabilidades:**
- Cifrado AES-256 GCM
- Cifrado RSA-OAEP de la clave AES
- Descifrado de mensajes
- Manejo de mensajes individuales y grupales
- Gestión de grupos
- Recuperación de mensajes
- Validación de acceso autenticado

**Archivos principales:**
- `src/crypto/modelos.py`
- `src/crypto/seguridad.py`
- `src/crypto/servicio.py`
- `src/crypto/rutas.py`
- `src/crypto/esquemas.py`

---

### Módulo Signatures

**Responsabilidades:**
- Calcular hash SHA-256 del plaintext
- Firmar con RSA-PSS
- Verificar firma con llave pública del remitente

**Archivo principal:**
- `src/signatures/seguridad.py`

---

### Módulo Blockchain

**Responsabilidades:**
- Crear bloque génesis
- Minar bloques con dificultad simplificada
- Encadenar hashes
- Registrar transacciones automáticamente
- Verificar integridad de la cadena
- Exponer endpoints de consulta y validación

**Archivos principales:**
- `src/blockchain/modelos.py`
- `src/blockchain/servicio.py`
- `src/blockchain/rutas.py`
- `src/blockchain/esquemas.py`

---
## Modelo de datos principal

### Tabla `usuarios`

Esta tabla representa la identidad base del sistema. Almacena la informacion principal de cada usuario, sus credenciales protegidas, su material criptografico y, opcionalmente, su secreto TOTP para MFA.

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | `uuid` | Identificador unico del usuario |
| `email` | `character varying(255)` | Correo electronico del usuario, unico en el sistema |
| `displayName` | `character varying(100)` | Nombre visible del usuario dentro de la aplicacion |
| `passwordHash` | `character varying(255)` | Hash seguro de la contrasena generado con Argon2id |
| `publicKey` | `text` | Llave publica RSA del usuario en formato PEM |
| `encryptedPrivateKey` | `text` | Llave privada cifrada con una clave derivada desde la contrasena |
| `totpSecret` | `character varying(32)` | Secreto TOTP para MFA, presente solo si el usuario activa MFA |
| `createdAt` | `timestamp with time zone` | Fecha y hora de creacion del usuario |

### Restricciones e indices
- PK: `usuarios_pkey` sobre `id`
- UNIQUE: `ix_usuarios_email` sobre `email`

### Uso y justificacion
Esta tabla es el punto central de la arquitectura porque conecta autenticacion, cifrado, firma digital y MFA. Se justifica mantener en una sola entidad el correo, el hash de contrasena, la llave publica, la llave privada cifrada y el secreto TOTP, ya que todos forman parte de la identidad criptografica del usuario.

---

### Tabla `grupos`

Esta tabla almacena la informacion general de cada grupo de mensajeria.

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | `uuid` | Identificador unico del grupo |
| `nombre` | `character varying(100)` | Nombre del grupo |
| `creadoPor` | `uuid` | Usuario creador del grupo |
| `createdAt` | `timestamp with time zone` | Fecha y hora de creacion del grupo |

### Restricciones e indices
- PK: `grupos_pkey` sobre `id`
- FK: `grupos_creadoPor_fkey` → `usuarios(id)`

### Uso y justificacion
Esta tabla existe para modelar la identidad propia de cada grupo. Se separa de la membresia porque un grupo tiene atributos propios, como nombre, creador y fecha de creacion, que no pertenecen a la relacion usuario-grupo sino al grupo mismo.

---

### Tabla `grupos_miembros`

Esta tabla relaciona usuarios con grupos. Define la membresia de cada grupo.

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | `uuid` | Identificador unico del registro de membresia |
| `groupId` | `uuid` | Grupo al que pertenece el usuario |
| `userId` | `uuid` | Usuario miembro del grupo |
| `addedAt` | `timestamp with time zone` | Fecha y hora en que se agrego el miembro al grupo |

### Restricciones e indices
- PK: `grupos_miembros_pkey` sobre `id`
- INDEX: `ix_grupos_miembros_groupId`
- INDEX: `ix_grupos_miembros_userId`
- UNIQUE: `uq_grupos_miembros_group_user` sobre (`groupId`, `userId`)
- FK: `grupos_miembros_groupId_fkey` → `grupos(id)`
- FK: `grupos_miembros_userId_fkey` → `usuarios(id)`

### Uso y justificacion
Esta tabla se justifica porque la relacion entre usuarios y grupos es de muchos a muchos. Un usuario puede pertenecer a varios grupos y un grupo puede tener varios usuarios. El constraint unico evita duplicar la membresia del mismo usuario dentro del mismo grupo.

---

### Tabla `mensajes`

Esta tabla almacena el mensaje cifrado principal y sus metadatos comunes. Soporta tanto mensajes individuales como grupales.

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | `uuid` | Identificador unico del mensaje |
| `senderId` | `uuid` | Usuario remitente del mensaje |
| `recipientId` | `uuid` | Usuario destinatario si el mensaje es individual |
| `groupId` | `uuid` | Grupo destinatario si el mensaje es grupal |
| `ciphertext` | `text` | Contenido cifrado del mensaje en Base64 |
| `encryptedKey` | `text` | Clave AES cifrada con RSA OAEP para mensaje individual |
| `nonce` | `character varying(24)` | Nonce o IV del cifrado AES GCM en Base64 |
| `authTag` | `character varying(24)` | Tag de autenticacion generado por AES GCM |
| `signature` | `text` | Firma digital del hash del plaintext |
| `createdAt` | `timestamp with time zone` | Fecha y hora de envio del mensaje |

### Restricciones e indices
- PK: `mensajes_pkey` sobre `id`
- INDEX: `ix_mensajes_groupId`
- INDEX: `ix_mensajes_recipientId`
- INDEX: `ix_mensajes_senderId`
- CHECK: `ck_mensajes_individual_o_grupal`
- FK: `mensajes_groupId_fkey` → `grupos(id)`
- FK: `mensajes_recipientId_fkey` → `usuarios(id)`
- FK: `mensajes_senderId_fkey` → `usuarios(id)`

### Regla
La restriccion `ck_mensajes_individual_o_grupal` asegura que un mensaje sea:
- individual, con `recipientId` lleno y `groupId` nulo
- o grupal, con `groupId` lleno y `recipientId` nulo

Nunca ambos al mismo tiempo.

### Uso y justificacion
Esta tabla concentra el contenido cifrado del mensaje y los datos compartidos por todos los destinatarios. En mensajes individuales, aqui mismo se almacena la clave AES cifrada. En mensajes grupales, el contenido cifrado sigue estando aqui, pero las claves AES cifradas por miembro se mueven a otra tabla para evitar duplicar el ciphertext.

---

### Tabla `mensajes_destinatarios`

Esta tabla complementa a `mensajes` en el caso de mensajes grupales. Guarda una clave AES cifrada distinta por cada miembro del grupo.

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | `uuid` | Identificador unico del registro |
| `messageId` | `uuid` | Mensaje grupal al que pertenece la clave cifrada |
| `userId` | `uuid` | Usuario destinatario de esa clave AES cifrada |
| `encryptedKey` | `text` | Clave AES del mensaje cifrada con la llave publica del usuario |
| `createdAt` | `timestamp with time zone` | Fecha y hora de creacion del registro |

### Restricciones e indices
- PK: `mensajes_destinatarios_pkey` sobre `id`
- INDEX: `ix_mensajes_destinatarios_messageId`
- INDEX: `ix_mensajes_destinatarios_userId`
- UNIQUE: `uq_mensajes_destinatarios_message_user` sobre (`messageId`, `userId`)
- FK: `mensajes_destinatarios_messageId_fkey` → `mensajes(id)`
- FK: `mensajes_destinatarios_userId_fkey` → `usuarios(id)`

### Uso y justificacion
Esta tabla existe para resolver correctamente la mensajeria grupal. El mensaje se cifra una sola vez con AES GCM, pero la clave AES debe protegerse de forma distinta para cada miembro usando su llave publica. Esto evita repetir el mensaje cifrado varias veces y mantiene el diseño limpio, eficiente y escalable.

---

### Tabla `bloques_blockchain`

Esta tabla representa la mini blockchain del sistema. Cada bloque registra una transaccion asociada al envio de un mensaje.

| Columna | Tipo | Descripcion |
|---|---|---|
| `indice` | `integer` | Numero secuencial del bloque dentro de la cadena |
| `timestamp` | `timestamp with time zone` | Fecha y hora de creacion del bloque |
| `senderId` | `character varying(36)` | Identificador del remitente asociado a la transaccion |
| `recipientId` | `character varying(36)` | Identificador del destinatario o del grupo asociado a la transaccion |
| `messageHash` | `character varying(64)` | Hash SHA 256 del plaintext original |
| `previousHash` | `character varying(64)` | Hash del bloque anterior |
| `nonce` | `integer` | Nonce encontrado durante el proof of work simplificado |
| `hashActual` | `character varying(64)` | Hash SHA 256 final del bloque actual |

### Restricciones e indices
- PK: `bloques_blockchain_pkey` sobre `indice`
- UNIQUE: `bloques_blockchain_hashActual_key` sobre `hashActual`

### Uso y justificacion
Esta tabla implementa una blockchain simplificada con fines academicos y de trazabilidad. Se justifica porque permite registrar de forma encadenada cada transaccion relevante del sistema, detectar alteraciones posteriores y demostrar integridad estructural mediante el enlace entre `previousHash` y `hashActual`.

---

## Flujos del Sistema

### Flujo de Registro y Protección de Llaves

```
Registro usuario
   |
   +--> Validar correo único
   +--> Hash de contraseña con Argon2id
   +--> Generar par RSA 2048
   +--> Derivar clave desde contraseña
   +--> Cifrar llave privada con AES GCM
   +--> Guardar usuario en PostgreSQL
```

---

### Flujo de Envío de Mensaje Individual

```
Remitente autenticado
   |
   +--> Obtiene llave pública del destinatario
   +--> Calcula hash SHA-256 del plaintext
   +--> Firma el hash con RSA-PSS
   +--> Genera clave AES-256 efímera
   +--> Cifra plaintext con AES GCM
   +--> Cifra clave AES con RSA-OAEP
   +--> Guarda mensaje
   +--> Registra transacción en blockchain
```

---

### Flujo de Envío de Mensaje Grupal

```
Remitente autenticado
   |
   +--> Verifica pertenencia al grupo
   +--> Calcula hash SHA-256 del plaintext
   +--> Firma el hash con RSA-PSS
   +--> Genera una clave AES-256 efímera
   +--> Cifra el plaintext una sola vez
   +--> Cifra la misma clave AES con la llave pública de cada miembro
   +--> Guarda mensaje grupal
   +--> Guarda claves cifradas por miembro
   +--> Registra transacción en blockchain
```

---

### Flujo de Recuperación de Mensajes

```
Usuario autenticado
   |
   +--> Solicita sus mensajes
   +--> Usa su password para descifrar su llave privada
   +--> Recupera la clave AES correspondiente
   +--> Descifra el mensaje
   +--> Recalcula hash SHA-256 del plaintext
   +--> Verifica firma con la llave pública del remitente
   +--> Retorna mensaje como VERIFICADO o NO_VERIFICADO
```

---

### Flujo MFA

```
Usuario autenticado
   |
   +--> Activa MFA
   +--> Backend genera secreto TOTP
   +--> Backend construye otpauth URL
   +--> Backend genera QR
   +--> Usuario escanea QR con Google Authenticator

Login
   |
   +--> Verificación de correo y contraseña
   +--> Si MFA activa, se exige código TOTP
   +--> Si el código es válido, se emiten access y refresh tokens
```

---

## Seguridad Aplicada

### Protección de Credenciales
- **Argon2id** para hashing de contraseñas
- Nunca se almacena la contraseña en texto plano

### Protección de Llaves
- Llave pública almacenada en PEM
- Llave privada cifrada con clave derivada del password
- Derivación con **PBKDF2HMAC**
- Cifrado simétrico con **AES GCM**

### Protección de Sesión
- JWT access token
- JWT refresh token
- Endpoints protegidos por Bearer token
- Verificación de identidad del usuario autenticado

### Protección de Mensajes
- Confidencialidad con **AES GCM**
- Protección de clave AES con **RSA-OAEP**
- Autenticidad con firma **RSA-PSS**
- Validación de integridad por firma y blockchain

---
