const baseUrl = "";


// Construye headers comunes para peticiones
function construirHeaders(token, incluirJson = true) {
  const headers = {};

  if (incluirJson) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return headers;
}


// Ejecuta una peticion http al backend
async function ejecutarPeticion(url, metodo = "GET", body = null, token = "") {
  const respuesta = await fetch(`${baseUrl}${url}`, {
    method: metodo,
    headers: construirHeaders(token, body !== null),
    body: body ? JSON.stringify(body) : null
  });

  const data = await respuesta.json().catch(() => ({}));

  if (!respuesta.ok) {
    throw new Error(data.detail || "Ocurrio un error en la peticion");
  }

  return data;
}


// Registra un usuario nuevo
export function registrarUsuario(payload) {
  return ejecutarPeticion("/auth/register", "POST", payload);
}


// Ejecuta login normal
export function loginUsuario(payload) {
  return ejecutarPeticion("/auth/login", "POST", payload);
}


// Habilita mfa para el usuario
export function habilitarMfa(payload, token) {
  return ejecutarPeticion("/auth/mfa/enable", "POST", payload, token);
}


// Verifica un codigo totp
export function verificarMfa(payload) {
  return ejecutarPeticion("/auth/mfa/verify", "POST", payload);
}


// Ejecuta login con mfa
export function loginConMfa(payload) {
  return ejecutarPeticion("/auth/mfa/login", "POST", payload);
}


// Refresca la sesion
export function refrescarSesion(payload) {
  return ejecutarPeticion("/auth/refresh", "POST", payload);
}


// Obtiene la llave publica de un usuario
export function obtenerLlavePublica(userId, token) {
  return ejecutarPeticion(`/users/${userId}/key`, "GET", null, token);
}


// Envia un mensaje individual
export function enviarMensaje(destId, payload, token) {
  return ejecutarPeticion(`/messages/${destId}`, "POST", payload, token);
}


// Recupera mensajes del usuario
export function recuperarMensajes(userId, password, token) {
  return ejecutarPeticion(`/messages/${userId}?password=${encodeURIComponent(password)}`, "GET", null, token);
}


// Crea un grupo
export function crearGrupo(payload, token) {
  return ejecutarPeticion("/groups", "POST", payload, token);
}


// Envia un mensaje grupal
export function enviarMensajeGrupal(groupId, payload, token) {
  return ejecutarPeticion(`/groups/${groupId}/messages`, "POST", payload, token);
}


// Obtiene la cadena blockchain
export function obtenerBlockchain() {
  return ejecutarPeticion("/blockchain", "GET");
}


// Verifica integridad blockchain
export function verificarBlockchain() {
  return ejecutarPeticion("/blockchain/verify", "GET");
}


// Verifica salud del backend
export function verificarApi() {
  return ejecutarPeticion("/salud/db", "GET");
}