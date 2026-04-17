import { useMemo, useState } from "react";
import {
  crearGrupo,
  enviarMensaje,
  enviarMensajeGrupal,
  habilitarMfa,
  loginConMfa,
  loginUsuario,
  obtenerBlockchain,
  obtenerLlavePublica,
  recuperarMensajes,
  refrescarSesion,
  registrarUsuario,
  verificarApi,
  verificarBlockchain,
  verificarMfa
} from "./servicios/api";

const secciones = [
  { id: "auth", titulo: "Autenticacion" },
  { id: "mfa", titulo: "MFA" },
  { id: "mensajes", titulo: "Mensajes" },
  { id: "grupos", titulo: "Grupos" },
  { id: "blockchain", titulo: "Blockchain" },
  { id: "sesion", titulo: "Sesion" }
];


// Convierte texto a json
function formatearJson(data) {
  return JSON.stringify(data, null, 2);
}


// Componente principal del frontend
export default function App() {
  const [seccionActiva, setSeccionActiva] = useState("auth");
  const [mensajeSistema, setMensajeSistema] = useState({ texto: "", tipo: "" });

  const [sesion, setSesion] = useState({
    accessToken: localStorage.getItem("accessToken") || "",
    refreshToken: localStorage.getItem("refreshToken") || "",
    userId: localStorage.getItem("userId") || "",
    email: localStorage.getItem("email") || "",
    displayName: localStorage.getItem("displayName") || "",
    mfaActiva: localStorage.getItem("mfaActiva") || "false"
  });

  const [registro, setRegistro] = useState({
    displayName: "",
    email: "",
    password: ""
  });

  const [login, setLogin] = useState({
    email: "",
    password: ""
  });

  const [loginMfaData, setLoginMfaData] = useState({
    email: "",
    password: "",
    codigoTotp: ""
  });

  const [mfaData, setMfaData] = useState({
    userId: localStorage.getItem("userId") || "",
    email: localStorage.getItem("email") || "",
    codigoTotp: ""
  });

  const [mfaResultado, setMfaResultado] = useState({
    otpauthUrl: "",
    qrBase64: ""
  });

  const [mensajeData, setMensajeData] = useState({
    senderId: localStorage.getItem("userId") || "",
    senderPassword: "",
    destId: "",
    plaintext: ""
  });

  const [recuperarData, setRecuperarData] = useState({
    userId: localStorage.getItem("userId") || "",
    password: ""
  });

  const [salidaMensajes, setSalidaMensajes] = useState("");

  const [grupoData, setGrupoData] = useState({
    nombre: "",
    creadoPor: localStorage.getItem("userId") || "",
    miembrosIds: ""
  });

  const [mensajeGrupalData, setMensajeGrupalData] = useState({
    groupId: "",
    senderId: localStorage.getItem("userId") || "",
    senderPassword: "",
    plaintext: ""
  });

  const [llavePublicaData, setLlavePublicaData] = useState({
    userId: "",
    salida: ""
  });

  const [blockchainSalida, setBlockchainSalida] = useState("");
  const [verificacionSalida, setVerificacionSalida] = useState("");
  const [refreshInput, setRefreshInput] = useState(localStorage.getItem("refreshToken") || "");

  const estadoSesion = useMemo(() => {
    return {
      autenticado: Boolean(sesion.accessToken),
      mfaActiva: sesion.mfaActiva === "true"
    };
  }, [sesion]);

  function mostrarMensaje(texto, tipo) {
    setMensajeSistema({ texto, tipo });
  }

  function guardarSesion(nuevaSesion) {
    const sesionActualizada = {
      accessToken: nuevaSesion.accessToken ?? sesion.accessToken,
      refreshToken: nuevaSesion.refreshToken ?? sesion.refreshToken,
      userId: nuevaSesion.userId ?? sesion.userId,
      email: nuevaSesion.email ?? sesion.email,
      displayName: nuevaSesion.displayName ?? sesion.displayName,
      mfaActiva:
        typeof nuevaSesion.mfaActiva !== "undefined"
          ? String(nuevaSesion.mfaActiva)
          : sesion.mfaActiva
    };

    setSesion(sesionActualizada);

    localStorage.setItem("accessToken", sesionActualizada.accessToken);
    localStorage.setItem("refreshToken", sesionActualizada.refreshToken);
    localStorage.setItem("userId", sesionActualizada.userId);
    localStorage.setItem("email", sesionActualizada.email);
    localStorage.setItem("displayName", sesionActualizada.displayName);
    localStorage.setItem("mfaActiva", sesionActualizada.mfaActiva);

    setMfaData((prev) => ({
      ...prev,
      userId: sesionActualizada.userId,
      email: sesionActualizada.email
    }));

    setMensajeData((prev) => ({
      ...prev,
      senderId: sesionActualizada.userId
    }));

    setRecuperarData((prev) => ({
      ...prev,
      userId: sesionActualizada.userId
    }));

    setGrupoData((prev) => ({
      ...prev,
      creadoPor: sesionActualizada.userId
    }));

    setMensajeGrupalData((prev) => ({
      ...prev,
      senderId: sesionActualizada.userId
    }));

    setRefreshInput(sesionActualizada.refreshToken);
  }

  function cerrarSesionLocal() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("userId");
    localStorage.removeItem("email");
    localStorage.removeItem("displayName");
    localStorage.removeItem("mfaActiva");

    setSesion({
      accessToken: "",
      refreshToken: "",
      userId: "",
      email: "",
      displayName: "",
      mfaActiva: "false"
    });

    setRefreshInput("");
    mostrarMensaje("Sesion local cerrada", "advertencia");
  }

  async function manejarVerificarApi() {
    try {
      const data = await verificarApi();
      mostrarMensaje(`API correcta: ${data.baseDatos}`, "exito");
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarRegistro(event) {
    event.preventDefault();

    try {
      const data = await registrarUsuario(registro);
      mostrarMensaje("Usuario registrado correctamente", "exito");
      setMfaData((prev) => ({ ...prev, userId: data.id, email: data.email }));
      setLogin((prev) => ({ ...prev, email: data.email }));
      setRegistro({
        displayName: "",
        email: "",
        password: ""
      });
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarLogin(event) {
    event.preventDefault();

    try {
      const data = await loginUsuario(login);

      guardarSesion({
        userId: data.userId,
        email: data.email,
        displayName: data.displayName,
        mfaActiva: data.mfaActiva
      });

      if (data.requiereMfa) {
        mostrarMensaje(data.mensaje, "advertencia");
        setLoginMfaData((prev) => ({
          ...prev,
          email: login.email,
          password: login.password
        }));
        setLogin({
          email: "",
          password: ""
        });
        return;
      }

      guardarSesion(data);
      mostrarMensaje("Login exitoso", "exito");
      setLogin({
        email: "",
        password: ""
      });
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarLoginMfa(event) {
    event.preventDefault();

    try {
      const data = await loginConMfa(loginMfaData);
      guardarSesion({
        ...data,
        mfaActiva: true
      });
      mostrarMensaje("Login con MFA exitoso", "exito");
      setLoginMfaData({
        email: "",
        password: "",
        codigoTotp: ""
      });
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarHabilitarMfa(event) {
    event.preventDefault();

    try {
      const data = await habilitarMfa(
        { userId: mfaData.userId },
        sesion.accessToken
      );

      setMfaResultado({
        otpauthUrl: data.otpauthUrl,
        qrBase64: data.qrBase64
      });

      guardarSesion({
        userId: data.userId,
        email: data.email,
        mfaActiva: data.mfaActiva
      });

      mostrarMensaje("MFA activada correctamente", "exito");
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarVerificarMfa(event) {
    event.preventDefault();

    try {
      const data = await verificarMfa({
        email: mfaData.email,
        codigoTotp: mfaData.codigoTotp
      });

      mostrarMensaje(data.mensaje, data.codigoValido ? "exito" : "advertencia");
      setMfaData((prev) => ({
        ...prev,
        codigoTotp: ""
      }));
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarEnviarMensaje(event) {
    event.preventDefault();

    try {
      const data = await enviarMensaje(
        mensajeData.destId,
        {
          senderId: mensajeData.senderId,
          senderPassword: mensajeData.senderPassword,
          plaintext: mensajeData.plaintext
        },
        sesion.accessToken
      );

      mostrarMensaje(`Mensaje individual enviado: ${data.messageId}`, "exito");
      setMensajeData((prev) => ({
        ...prev,
        senderPassword: "",
        destId: "",
        plaintext: ""
      }));
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarRecuperarMensajes(event) {
    event.preventDefault();

    try {
      const data = await recuperarMensajes(
        recuperarData.userId,
        recuperarData.password,
        sesion.accessToken
      );

      setSalidaMensajes(formatearJson(data));
      mostrarMensaje("Mensajes recuperados correctamente", "exito");
      setRecuperarData((prev) => ({
        ...prev,
        password: ""
      }));
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarCrearGrupo(event) {
    event.preventDefault();

    try {
      const miembrosIds = grupoData.miembrosIds
        .split(",")
        .map((valor) => valor.trim())
        .filter((valor) => valor.length > 0);

      const data = await crearGrupo(
        {
          nombre: grupoData.nombre,
          creadoPor: grupoData.creadoPor,
          miembrosIds
        },
        sesion.accessToken
      );

      setMensajeGrupalData((prev) => ({ ...prev, groupId: data.groupId }));
      mostrarMensaje(`Grupo creado correctamente: ${data.groupId}`, "exito");
      setGrupoData((prev) => ({
        ...prev,
        nombre: "",
        miembrosIds: ""
      }));
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarEnviarMensajeGrupal(event) {
    event.preventDefault();

    try {
      const data = await enviarMensajeGrupal(
        mensajeGrupalData.groupId,
        {
          senderId: mensajeGrupalData.senderId,
          senderPassword: mensajeGrupalData.senderPassword,
          plaintext: mensajeGrupalData.plaintext
        },
        sesion.accessToken
      );

      mostrarMensaje(`Mensaje grupal enviado: ${data.messageId}`, "exito");
      setMensajeGrupalData((prev) => ({
        ...prev,
        senderPassword: "",
        plaintext: ""
      }));
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarObtenerLlavePublica(event) {
    event.preventDefault();

    try {
      const data = await obtenerLlavePublica(llavePublicaData.userId, sesion.accessToken);
      setLlavePublicaData({
        userId: "",
        salida: formatearJson(data)
      });
      mostrarMensaje("Llave publica obtenida correctamente", "exito");
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarCargarBlockchain() {
    try {
      const data = await obtenerBlockchain();
      setBlockchainSalida(formatearJson(data));
      mostrarMensaje("Blockchain cargada correctamente", "exito");
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarVerificarBlockchain() {
    try {
      const data = await verificarBlockchain();
      setVerificacionSalida(formatearJson(data));
      mostrarMensaje(data.detalle, data.esValida ? "exito" : "advertencia");
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  async function manejarRefresh(event) {
    event.preventDefault();

    try {
      const data = await refrescarSesion({ refreshToken: refreshInput });
      guardarSesion(data);
      mostrarMensaje("Sesion refrescada correctamente", "exito");
      setRefreshInput("");
    } catch (error) {
      mostrarMensaje(error.message, "error");
    }
  }

  return (
    <div className="appContenedor">
      <aside className="barraLateral">
        <div className="marcaPanel">
          <div className="logoCirculo">S</div>
          <div>
            <h1>Sistema Mensajeria Segura</h1>
          </div>
        </div>

        <div className="panelSesion">
          <div className="estadoItem">
            <span>Usuario</span>
            <strong>{sesion.userId || "-"}</strong>
          </div>
          <div className="estadoItem">
            <span>Email</span>
            <strong>{sesion.email || "-"}</strong>
          </div>
          <div className="estadoItem">
            <span>MFA</span>
            <strong>{estadoSesion.mfaActiva ? "Activa" : "No activa"}</strong>
          </div>
          <div className="estadoItem">
            <span>Sesion</span>
            <strong>{estadoSesion.autenticado ? "Autenticada" : "No autenticada"}</strong>
          </div>
        </div>

        <div className="menuSecciones">
          {secciones.map((seccion) => (
            <button
              key={seccion.id}
              className={`botonSeccion ${seccionActiva === seccion.id ? "activo" : ""}`}
              onClick={() => setSeccionActiva(seccion.id)}
            >
              {seccion.titulo}
            </button>
          ))}
        </div>

        <button className="botonSecundario anchoCompleto" onClick={manejarVerificarApi}>
          Verificar API
        </button>
      </aside>

      <main className="contenidoApp">
        <header className="cabeceraApp">
          <div>
            <h2>Panel de demostracion</h2>
            <p>Flujo completo de registro, mfa, mensajeria y blockchain</p>
          </div>
        </header>

        {mensajeSistema.texto && (
          <div className={`mensajeSistema ${mensajeSistema.tipo}`}>
            {mensajeSistema.texto}
          </div>
        )}

        {seccionActiva === "auth" && (
          <section className="gridPaneles">
            <div className="tarjetaPanel">
              <h3>Registro</h3>
              <form className="formularioPanel" onSubmit={manejarRegistro}>
                <input
                  value={registro.displayName}
                  onChange={(e) => setRegistro({ ...registro, displayName: e.target.value })}
                  placeholder="Nombre visible"
                />
                <input
                  type="email"
                  value={registro.email}
                  onChange={(e) => setRegistro({ ...registro, email: e.target.value })}
                  placeholder="Correo"
                />
                <input
                  type="password"
                  value={registro.password}
                  onChange={(e) => setRegistro({ ...registro, password: e.target.value })}
                  placeholder="Contrasena"
                />
                <button className="botonPrimario" type="submit">Registrar usuario</button>
              </form>
            </div>

            <div className="tarjetaPanel">
              <h3>Login</h3>
              <form className="formularioPanel" onSubmit={manejarLogin}>
                <input
                  type="email"
                  value={login.email}
                  onChange={(e) => setLogin({ ...login, email: e.target.value })}
                  placeholder="Correo"
                />
                <input
                  type="password"
                  value={login.password}
                  onChange={(e) => setLogin({ ...login, password: e.target.value })}
                  placeholder="Contrasena"
                />
                <button className="botonPrimario" type="submit">Iniciar sesion</button>
              </form>

              <div className="separadorPanel"></div>

              <h3>Login con MFA</h3>
              <form className="formularioPanel" onSubmit={manejarLoginMfa}>
                <input
                  type="email"
                  value={loginMfaData.email}
                  onChange={(e) => setLoginMfaData({ ...loginMfaData, email: e.target.value })}
                  placeholder="Correo"
                />
                <input
                  type="password"
                  value={loginMfaData.password}
                  onChange={(e) => setLoginMfaData({ ...loginMfaData, password: e.target.value })}
                  placeholder="Contrasena"
                />
                <input
                  value={loginMfaData.codigoTotp}
                  onChange={(e) => setLoginMfaData({ ...loginMfaData, codigoTotp: e.target.value })}
                  placeholder="Codigo TOTP"
                  maxLength={6}
                />
                <button className="botonPrimario" type="submit">Completar login MFA</button>
              </form>
            </div>
          </section>
        )}

        {seccionActiva === "mfa" && (
          <section className="gridPaneles">
            <div className="tarjetaPanel">
              <h3>Activar MFA</h3>
              <form className="formularioPanel" onSubmit={manejarHabilitarMfa}>
                <input
                  value={mfaData.userId}
                  onChange={(e) => setMfaData({ ...mfaData, userId: e.target.value })}
                  placeholder="User ID"
                />
                <button className="botonPrimario" type="submit">Generar QR</button>
              </form>

              <label className="labelSeccion">otpauth URL</label>
              <textarea readOnly rows={6} value={mfaResultado.otpauthUrl}></textarea>
            </div>

            <div className="tarjetaPanel">
              <h3>QR TOTP</h3>
              <div className="panelQr">
                {mfaResultado.qrBase64 ? (
                  <img src={mfaResultado.qrBase64} alt="QR TOTP" className="imagenQr" />
                ) : (
                  <span>El QR aparecera aqui</span>
                )}
              </div>

              <div className="separadorPanel"></div>

              <h3>Verificar codigo TOTP</h3>
              <form className="formularioPanel" onSubmit={manejarVerificarMfa}>
                <input
                  type="email"
                  value={mfaData.email}
                  onChange={(e) => setMfaData({ ...mfaData, email: e.target.value })}
                  placeholder="Correo"
                />
                <input
                  value={mfaData.codigoTotp}
                  onChange={(e) => setMfaData({ ...mfaData, codigoTotp: e.target.value })}
                  placeholder="Codigo TOTP"
                  maxLength={6}
                />
                <button className="botonPrimario" type="submit">Verificar codigo</button>
              </form>
            </div>
          </section>
        )}

        {seccionActiva === "mensajes" && (
          <section className="gridPaneles">
            <div className="tarjetaPanel">
              <h3>Enviar mensaje individual</h3>
              <form className="formularioPanel" onSubmit={manejarEnviarMensaje}>
                <input
                  value={mensajeData.senderId}
                  onChange={(e) => setMensajeData({ ...mensajeData, senderId: e.target.value })}
                  placeholder="Sender ID"
                />
                <input
                  type="password"
                  value={mensajeData.senderPassword}
                  onChange={(e) => setMensajeData({ ...mensajeData, senderPassword: e.target.value })}
                  placeholder="Password del remitente"
                />
                <input
                  value={mensajeData.destId}
                  onChange={(e) => setMensajeData({ ...mensajeData, destId: e.target.value })}
                  placeholder="Destinatario ID"
                />
                <textarea
                  rows={6}
                  value={mensajeData.plaintext}
                  onChange={(e) => setMensajeData({ ...mensajeData, plaintext: e.target.value })}
                  placeholder="Mensaje a cifrar y firmar"
                ></textarea>
                <button className="botonPrimario" type="submit">Enviar mensaje</button>
              </form>
            </div>

            <div className="tarjetaPanel">
              <h3>Recuperar mensajes</h3>
              <form className="formularioPanel" onSubmit={manejarRecuperarMensajes}>
                <input
                  value={recuperarData.userId}
                  onChange={(e) => setRecuperarData({ ...recuperarData, userId: e.target.value })}
                  placeholder="User ID"
                />
                <input
                  type="password"
                  value={recuperarData.password}
                  onChange={(e) => setRecuperarData({ ...recuperarData, password: e.target.value })}
                  placeholder="Password del usuario"
                />
                <button className="botonPrimario" type="submit">Recuperar mensajes</button>
              </form>

              <label className="labelSeccion">Salida</label>
              <pre className="panelSalida">{salidaMensajes}</pre>

              <div className="separadorPanel"></div>

              <h3>Obtener llave publica</h3>
              <form className="formularioPanel" onSubmit={manejarObtenerLlavePublica}>
                <input
                  value={llavePublicaData.userId}
                  onChange={(e) => setLlavePublicaData({ ...llavePublicaData, userId: e.target.value })}
                  placeholder="User ID"
                />
                <button className="botonSecundario" type="submit">Cargar llave publica</button>
              </form>
              <pre className="panelSalida">{llavePublicaData.salida}</pre>
            </div>
          </section>
        )}

        {seccionActiva === "grupos" && (
          <section className="gridPaneles">
            <div className="tarjetaPanel">
              <h3>Crear grupo</h3>
              <form className="formularioPanel" onSubmit={manejarCrearGrupo}>
                <input
                  value={grupoData.nombre}
                  onChange={(e) => setGrupoData({ ...grupoData, nombre: e.target.value })}
                  placeholder="Nombre del grupo"
                />
                <input
                  value={grupoData.creadoPor}
                  onChange={(e) => setGrupoData({ ...grupoData, creadoPor: e.target.value })}
                  placeholder="Creado por"
                />
                <textarea
                  rows={5}
                  value={grupoData.miembrosIds}
                  onChange={(e) => setGrupoData({ ...grupoData, miembrosIds: e.target.value })}
                  placeholder="Miembros separados por coma"
                ></textarea>
                <button className="botonPrimario" type="submit">Crear grupo</button>
              </form>
            </div>

            <div className="tarjetaPanel">
              <h3>Enviar mensaje grupal</h3>
              <form className="formularioPanel" onSubmit={manejarEnviarMensajeGrupal}>
                <input
                  value={mensajeGrupalData.groupId}
                  onChange={(e) => setMensajeGrupalData({ ...mensajeGrupalData, groupId: e.target.value })}
                  placeholder="Group ID"
                />
                <input
                  value={mensajeGrupalData.senderId}
                  onChange={(e) => setMensajeGrupalData({ ...mensajeGrupalData, senderId: e.target.value })}
                  placeholder="Sender ID"
                />
                <input
                  type="password"
                  value={mensajeGrupalData.senderPassword}
                  onChange={(e) => setMensajeGrupalData({ ...mensajeGrupalData, senderPassword: e.target.value })}
                  placeholder="Password del remitente"
                />
                <textarea
                  rows={6}
                  value={mensajeGrupalData.plaintext}
                  onChange={(e) => setMensajeGrupalData({ ...mensajeGrupalData, plaintext: e.target.value })}
                  placeholder="Mensaje grupal"
                ></textarea>
                <button className="botonPrimario" type="submit">Enviar mensaje grupal</button>
              </form>
            </div>
          </section>
        )}

        {seccionActiva === "blockchain" && (
          <section className="gridPaneles">
            <div className="tarjetaPanel">
              <h3>Cadena completa</h3>
              <button className="botonPrimario" onClick={manejarCargarBlockchain}>
                Cargar blockchain
              </button>
              <pre className="panelSalida">{blockchainSalida}</pre>
            </div>

            <div className="tarjetaPanel">
              <h3>Verificar integridad</h3>
              <button className="botonPrimario" onClick={manejarVerificarBlockchain}>
                Verificar blockchain
              </button>
              <pre className="panelSalida">{verificacionSalida}</pre>
            </div>
          </section>
        )}

        {seccionActiva === "sesion" && (
          <section className="gridPaneles">
            <div className="tarjetaPanel">
              <h3>Refrescar sesion</h3>
              <form className="formularioPanel" onSubmit={manejarRefresh}>
                <textarea
                  rows={7}
                  value={refreshInput}
                  onChange={(e) => setRefreshInput(e.target.value)}
                  placeholder="Refresh token"
                ></textarea>
                <button className="botonPrimario" type="submit">Refrescar token</button>
              </form>
            </div>

            <div className="tarjetaPanel">
              <h3>Tokens actuales</h3>
              <label className="labelSeccion">Access token</label>
              <textarea readOnly rows={8} value={sesion.accessToken}></textarea>
              <label className="labelSeccion">Refresh token</label>
              <textarea readOnly rows={8} value={sesion.refreshToken}></textarea>
              <button className="botonPeligro" onClick={cerrarSesionLocal}>
                Cerrar sesion local
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}