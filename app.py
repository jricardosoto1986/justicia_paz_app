import os
import streamlit as st
import mysql.connector
from datetime import datetime
from fpdf import FPDF

# --- Configuración de Página ---
st.set_page_config(
    page_title="Justicia de Paz Comunal",
    page_icon="⚖️",
    layout="wide"
)

CONSEJOS_COMUNALES = [
    "Todos",
    "Consejo Comunal Santa Laguna",
    "Consejo Comunal Valle de los Laureles",
    "Consejo Comunal La Esperanza",
    "Consejo Comunal El Carmen",
    "Consejo Comunal San José",
    "Consejo Comunal Los Centauros",
    "Consejo Comunal Bolivariano"
]

# --- Conexión a Base de Datos (TiDB Cloud) ---
def get_db_connection():
    conn = mysql.connector.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        database=st.secrets["DB_NAME"],
        port=int(st.secrets["DB_PORT"]),
        ssl_disabled=False,
        ssl_verify_cert=False
    )
    cursor = conn.cursor()
    cursor.execute("USE justicia_paz_db;")
    cursor.close()
    return conn

# --- Funciones de Autenticación ---
def autenticar_usuario(username, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password_hash = %s", (username, password))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception:
        return None

def registrar_o_actualizar_usuario(cursor, cedula, nombre_completo, password):
    cursor.execute("SELECT id FROM usuarios WHERE username = %s", (cedula,))
    res = cursor.fetchone()
    if not res:
        cursor.execute(
            "INSERT INTO usuarios (username, password_hash, rol, nombre_completo, cedula) VALUES (%s, %s, 'ciudadano', %s, %s)",
            (cedula, password, nombre_completo, cedula)
        )
    else:
        cursor.execute(
            "UPDATE usuarios SET password_hash = %s, nombre_completo = %s WHERE username = %s",
            (password, nombre_completo, cedula)
        )

# --- Sanitización de Texto para FPDF ---
def limpiar_texto(texto):
    if not texto:
        return ""
    texto = str(texto).replace("•", "*").replace("°", ".").replace("º", ".")
    return texto.encode("latin-1", "replace").decode("latin-1")

# --- Generador de PDF Auto de Inicio (Con los 3 Logos y Márgenes Legales) ---
def generar_pdf_auto_inicio(num_expediente, solicitante_nombre, solicitante_cedula, solicitante_tel, solicitante_dir, 
                            requerido_nombre, requerido_dir, materia, hechos, pretension):
    pdf = FPDF(orientation='P', unit='mm', format='Letter')
    pdf.set_margins(20, 20, 20) # Márgenes legales estándar en Venezuela (Izquierda 20mm, Superior 20mm, Derecha 20mm)
    pdf.add_page()
    
    # Distribución simétrica de los 3 logos en el encabezado oficial
    # Izquierda: TSJ | Centro: Coordinación Nacional | Derecha: Paz Comunal
    if os.path.exists("assets/logo_tsj.png"):
        pdf.image("assets/logo_tsj.png", x=20, y=10, w=22)
    if os.path.exists("assets/logo_coordinacion_nacional.png"):
        pdf.image("assets/logo_coordinacion_nacional.png", x=96, y=10, w=22)
    if os.path.exists("assets/logo_paz_comunal.png"):
        pdf.image("assets/logo_paz_comunal.png", x=172, y=10, w=22)

    pdf.ln(12) # Espacio para los logos
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 4, limpiar_texto("REPÚBLICA BOLIVARIANA DE VENEZUELA"), 0, 1, "C")
    pdf.cell(0, 4, limpiar_texto("JURISDICCIÓN ESPECIAL DE LA JUSTICIA DE PAZ COMUNAL"), 0, 1, "C")
    pdf.cell(0, 4, limpiar_texto("CIRCUITO COMUNAL SANTA LAGUNA DEL VALLE DE LOS LAURELES"), 0, 1, "C")
    pdf.cell(0, 4, limpiar_texto("SAN JUAN DE LOS MORROS - ESTADO GUÁRICO"), 0, 1, "C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, limpiar_texto("AUTO DE INICIO DE PROCEDIMIENTO Y FIJACIÓN DE AUDIENCIA INICIAL"), 0, 1, "C")
    pdf.set_font("Arial", "", 9)
    
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 5, limpiar_texto(f"San Juan de los Morros, {fecha_hoy}"), 0, 1, "R")
    pdf.cell(0, 5, limpiar_texto(f"EXPEDIENTE N°: {num_expediente}"), 0, 1, "R")
    pdf.ln(3)
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, limpiar_texto("1. IDENTIFICACIÓN DE LAS PARTES Y DATOS DE NOTIFICACIÓN:"), 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    
    sol_info = (
        f"• PARTE SOLICITANTE: {solicitante_nombre}, C.I. N° {solicitante_cedula}.\n"
        f"  - Teléfono: {solicitante_tel if solicitante_tel else 'No registrado'}\n"
        f"  - Domicilio: {solicitante_dir}"
    )
    pdf.multi_cell(0, 4, limpiar_texto(sol_info))
    pdf.ln(1)
    
    req_info = (
        f"• PARTE REQUERIDA (CITADO): {requerido_nombre}.\n"
        f"  - Domicilio / Ubicación para citación: {requerido_dir}"
    )
    pdf.multi_cell(0, 4, limpiar_texto(req_info))
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, limpiar_texto(f"2. MATERIA DEL CONFLICTO: {materia.upper()}"), 0, 1, "L")
    pdf.cell(0, 5, limpiar_texto("3. DESCRIPCIÓN DETALLADA DE LOS HECHOS:"), 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 4, limpiar_texto(hechos if hechos else "No especificado."))
    pdf.ln(2)
    
    if pretension:
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 5, limpiar_texto("4. PRETENSIÓN / PROPUESTA DE ARREGLO:"), 0, 1, "L")
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 4, limpiar_texto(pretension))
        pdf.ln(2)
        
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, limpiar_texto("5. ORDEN DE SUSTANCIACIÓN Y FIJACIÓN DE AUDIENCIA INICIAL:"), 0, 1, "L")
    pdf.set_font("Arial", "", 9)
    
    orden_texto = (
        "Vista la solicitud presentada, este Despacho de Paz Comunal ADMITE la presente causa "
        "y ORDENA la apertura del expediente formal. En cumplimiento del lapso legal establecido, "
        "se FIJA la celebración de la AUDIENCIA INICIAL DE CONCILIACIÓN dentro de los ocho (8) días "
        "hábiles siguientes en la Sede de la Oficina de Justicia de Paz Comunal."
    )
    pdf.multi_cell(0, 4, limpiar_texto(orden_texto))
    pdf.ln(12)
    
    # Firmas con margen respetado (Ancho total útil = 176mm aprox)
    col_width = 85
    pdf.cell(col_width, 4, "_______________________________________", 0, 0, "C")
    pdf.cell(col_width, 4, "_______________________________________", 0, 1, "C")
    pdf.cell(col_width, 4, limpiar_texto(solicitante_nombre), 0, 0, "C")
    pdf.cell(col_width, 4, limpiar_texto("Juez(a) de Paz Comunal"), 0, 1, "C")
    pdf.cell(col_width, 4, limpiar_texto("Firma del Solicitante"), 0, 0, "C")
    pdf.cell(col_width, 4, limpiar_texto("Firma y Sello del Despacho"), 0, 1, "C")
    
    return bytes(pdf.output())

# --- Generador de Boleta de Citación (Con los 3 Logos y Márgenes Legales) ---
def generar_boleta_citacion(num_expediente, requerido_nombre, requerido_dir, solicitante_nombre):
    pdf = FPDF(orientation='P', unit='mm', format='Letter')
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    
    if os.path.exists("assets/logo_tsj.png"):
        pdf.image("assets/logo_tsj.png", x=20, y=10, w=22)
    if os.path.exists("assets/logo_coordinacion_nacional.png"):
        pdf.image("assets/logo_coordinacion_nacional.png", x=96, y=10, w=22)
    if os.path.exists("assets/logo_paz_comunal.png"):
        pdf.image("assets/logo_paz_comunal.png", x=172, y=10, w=22)

    pdf.ln(12)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 4, limpiar_texto("REPÚBLICA BOLIVARIANA DE VENEZUELA"), 0, 1, "C")
    pdf.cell(0, 4, limpiar_texto("JURISDICCIÓN ESPECIAL DE LA JUSTICIA DE PAZ COMUNAL"), 0, 1, "C")
    pdf.cell(0, 4, limpiar_texto("CIRCUITO COMUNAL SANTA LAGUNA DEL VALLE DE LOS LAURELES"), 0, 1, "C")
    pdf.cell(0, 4, limpiar_texto("SAN JUAN DE LOS MORROS - ESTADO GUÁRICO"), 0, 1, "C")
    pdf.ln(6)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, limpiar_texto("BOLETA DE CITACIÓN FORMAL"), 0, 1, "C")
    pdf.set_font("Arial", "", 9)
    
    fecha_emision = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 5, limpiar_texto(f"San Juan de los Morros, {fecha_emision}"), 0, 1, "R")
    pdf.cell(0, 5, limpiar_texto(f"EXPEDIENTE N°: {num_expediente}"), 0, 1, "R")
    pdf.ln(4)
    
    pdf.set_font("Arial", "", 9)
    texto_citacion = (
        f"CIUDADANO(A): {requerido_nombre}\n"
        f"DOMICILIO / UBICACIÓN: {requerido_dir}\n\n"
        f"Por medio de la presente se le CITA PARA QUE COMPAREZCA ante esta Jurisdicción de Paz Comunal, "
        f"a los fines de celebrar la AUDIENCIA INICIAL DE CONCILIACIÓN respecto a la solicitud presentada "
        f"por el/la ciudadano(a) {solicitante_nombre}.\n\n"
        f"DATOS DE LA AUDIENCIA (A ser completados por el Despacho):\n"
        f"  * FECHA DE LA AUDIENCIA: _____________________________________\n"
        f"  * HORA: _____________________________________________________\n"
        f"  * LUGAR / SEDE: _____________________________________________\n\n"
        f"Se le exhorta a acudir de manera puntual con su Cédula de Identidad laminada. "
        f"La incomparecencia injustificada dará lugar a las medidas previstas en la Ley Orgánica de la Jurisdicción Especial de la Justicia de Paz Comunal."
    )
    pdf.multi_cell(0, 5, limpiar_texto(texto_citacion))
    pdf.ln(18)
    
    col_width = 85
    pdf.cell(col_width, 4, "_______________________________________", 0, 0, "C")
    pdf.cell(col_width, 4, "_______________________________________", 0, 1, "C")
    pdf.cell(col_width, 4, limpiar_texto("Juez(a) de Paz Comunal"), 0, 0, "C")
    pdf.cell(col_width, 4, limpiar_texto("Firma / Huella de Recepción del Citado"), 0, 1, "C")
    pdf.cell(col_width, 4, limpiar_texto("Firma y Sello del Despacho"), 0, 0, "C")
    pdf.cell(col_width, 4, limpiar_texto("Fecha de Notificación: ___/___/202_"), 0, 1, "C")
    
    return bytes(pdf.output())

def guardar_o_buscar_persona(cursor, nac, cedula, nombres, apellidos, telf, direccion, consejo):
    cursor.execute("SELECT id FROM personas WHERE cedula = %s", (cedula,))
    res = cursor.fetchone()
    if res:
        cursor.execute(
            "UPDATE personas SET telefono=%s, direccion_habitacion=%s, consejo_comunal=%s WHERE id=%s",
            (telf, direccion, consejo, res[0])
        )
        return res[0]
    else:
        cursor.execute(
            "INSERT INTO personas (nacionalidad, cedula, nombres, apellidos, telefono, direccion_habitacion, consejo_comunal) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (nac, cedula, nombres, apellidos, telf, direccion, consejo)
        )
        return cursor.lastrowid

# ==================== ENCABEZADO Y LOGIN EN SIDEBAR ====================
col1, col2, col3 = st.columns([1, 4, 1])

with col2:
    # Contenedor para alinear los 3 logos en una sola fila centrada
    l_col1, l_col2, l_col3 = st.columns(3)
    with l_col1:
        if os.path.exists("assets/logo_tsj.png"):
            st.image("assets/logo_tsj.png", width=80)
    with l_col2:
        if os.path.exists("assets/logo_coordinacion_nacional.png"):
            st.image("assets/logo_coordinacion_nacional.png", width=80)
    with l_col3:
        if os.path.exists("assets/logo_paz_comunal.png"):
            st.image("assets/logo_paz_comunal.png", width=80)
            
    # Línea divisoria muy compacta
    st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)
    
    # Títulos institucionales compactos (sin espacios muertos)
    st.markdown("<p style='text-align: center; color: #555; font-size: 14px; font-weight: bold; margin: 0px; line-height: 1.2;'>REPÚBLICA BOLIVARIANA DE VENEZUELA</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555; font-size: 13px; font-weight: bold; margin: 2px 0px; line-height: 1.2;'>CIRCUITO COMUNAL SANTA LAGUNA DEL VALLE DE LOS LAURELES</p>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; font-weight: bold; margin: 5px 0px 0px 0px; line-height: 1.2;'>Sistema de Gestión - Justicia de Paz Comunal</h4>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 15px 0px;'>", unsafe_allow_html=True)

if 'usuario_logueado' not in st.session_state:
    st.session_state['usuario_logueado'] = None

with st.sidebar:
    st.header("🔐 Control de Acceso")
    if st.session_state['usuario_logueado'] is None:
        st.info("Ingrese con su usuario (Cédula para ciudadanos o usuario asignado para jueces).")
        user_input = st.text_input("Usuario / Cédula")
        pass_input = st.text_input("Contraseña", type="password")
        if st.button("Iniciar Sesión"):
            usuario = autenticar_usuario(user_input, pass_input)
            if usuario:
                st.session_state['usuario_logueado'] = usuario
                st.success(f"Bienvenido(a) {usuario['nombre_completo']}")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    else:
        u = st.session_state['usuario_logueado']
        st.write(f"👤 **{u['nombre_completo']}**")
        st.caption(f"Rol: {u['rol'].upper()}")
        if st.button("Cerrar Sesión"):
            st.session_state['usuario_logueado'] = None
            st.rerun()

# ==================== PESTAÑAS PRINCIPALES ====================
menu = st.tabs([
    "📝 Registrar Solicitud", 
    "🔍 Consultar Mis Expedientes", 
    "👨‍⚖️ Módulo del Juez de Paz",
    "📚 Marco Legal y Competencias"
])

# TAB 1: REGISTRAR SOLICITUD
with menu[0]:
    st.subheader("Nueva Solicitud de Conciliación")
    
    if 'ultimo_expediente' in st.session_state:
        datos_exito = st.session_state['ultimo_expediente']
        st.success(f"🎉 ¡Solicitud Registrada Exitosamente! Número de Expediente: **{datos_exito['num_exp']}**")
        
        pdf_bytes = generar_pdf_auto_inicio(
            datos_exito['num_exp'], datos_exito['solicitante_nombre'], datos_exito['ced_sol'],
            datos_exito['tel_sol'], datos_exito['dir_sol'], datos_exito['requerido_nombre'],
            datos_exito['dir_req'], datos_exito['materia'], datos_exito['hechos'], datos_exito['pretension']
        )
        
        st.download_button(
            label="📄 Descargar Auto de Inicio (PDF)",
            data=pdf_bytes,
            file_name=f"Auto_Inicio_{datos_exito['num_exp']}.pdf",
            mime="application/pdf"
        )
        
        if st.button("➕ Registrar otra solicitud"):
            del st.session_state['ultimo_expediente']
            st.rerun()
        
        st.markdown("---")

    with st.form("form_solicitud", clear_on_submit=True):
        st.markdown("##### 1. Datos del Solicitante")
        col1, col2 = st.columns([1, 3])
        nac_sol = col1.selectbox("Nac.", ["V", "E"])
        ced_sol = col2.text_input("Cédula de Identidad *")
        
        col3, col4 = st.columns(2)
        nom_sol = col3.text_input("Nombres *")
        ape_sol = col4.text_input("Apellidos *")
        
        col5, col6 = st.columns(2)
        tel_sol = col5.text_input("Teléfono Celular *")
        cc_sol = col6.selectbox("Consejo Comunal *", CONSEJOS_COMUNALES[1:])
        
        dir_sol = st.text_area("Dirección de Habitación *", height=2)
        
        st.markdown("##### Credencial de Acceso para Consultas")
        pass_ciudadano = st.text_input("Contraseña para consultar sus expedientes en el futuro *", type="password")
        
        st.markdown("---")
        st.markdown("##### 2. Datos de la Parte Requerida (Citado)")
        col7, col8 = st.columns(2)
        nom_req = col7.text_input("Nombres del Requerido *")
        ape_req = col8.text_input("Apellidos del Requerido *")
        dir_req = st.text_area("Dirección donde vive o se ubica para la citación *", height=2)
        
        st.markdown("---")
        st.markdown("##### 3. Descripción de la Controversia")
        materia = st.selectbox("Materia del Conflicto *", [
            "Convivencia Vecinal (Ruidos, basura, acuerdos)",
            "Familiar / Manutención",
            "Arrendamiento y Propiedad",
            "Linderos y Bienes",
            "Cosas o Daños",
            "Otro Conflicto Comunitario"
        ])
        hechos = st.text_area("Síntesis de los hechos (Narración detallada) *", height=3)
        pretension = st.text_area("Pretensión o propuesta de arreglo *", height=2)
        
        btn_enviar = st.form_submit_button("📤 Enviar Solicitud al Juez de Paz", use_container_width=True)
        
        if btn_enviar:
            if not ced_sol or not nom_sol or not ape_sol or not dir_sol or not nom_req or not hechos or not pass_ciudadano:
                st.error("Por favor complete todos los campos obligatorios (*) y asigne su contraseña.")
            else:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    id_sol = guardar_o_buscar_persona(cursor, nac_sol, ced_sol, nom_sol, ape_sol, tel_sol, dir_sol, cc_sol)
                    id_req = guardar_o_buscar_persona(cursor, "V", f"SD-{datetime.now().microsecond}", nom_req, ape_req, "", dir_req, "")
                    
                    registrar_o_actualizar_usuario(cursor, ced_sol, f"{nom_sol} {ape_sol}", pass_ciudadano)
                    
                    anio = datetime.now().year
                    cursor.execute("SELECT COUNT(*) FROM expedientes WHERE YEAR(fecha_ingreso) = %s", (anio,))
                    total = cursor.fetchone()[0] + 1
                    num_exp = f"JPC-{anio}-{total:04d}"
                    
                    cursor.execute(
                        "INSERT INTO expedientes (numero_expediente, circuito_id, solicitante_id, requerido_id, materia, sintesis_hechos, pretension) VALUES (%s, 1, %s, %s, %s, %s, %s)",
                        (num_exp, id_sol, id_req, materia, hechos, pretension)
                    )
                    conn.commit()
                    conn.close()
                    
                    st.session_state['ultimo_expediente'] = {
                        'num_exp': num_exp,
                        'solicitante_nombre': f"{nom_sol} {ape_sol}",
                        'ced_sol': ced_sol,
                        'tel_sol': tel_sol,
                        'dir_sol': dir_sol,
                        'requerido_nombre': f"{nom_req} {ape_req}",
                        'dir_req': dir_req,
                        'materia': materia,
                        'hechos': hechos,
                        'pretension': pretension
                    }
                    st.rerun()

                except Exception as e:
                    st.error(f"Error procesando la solicitud: {e}")

# TAB 2: CONSULTAR (CIUDADANO AUTENTICADO)
with menu[1]:
    st.subheader("🔍 Mis Expedientes Registrados")
    
    usuario_actual = st.session_state['usuario_logueado']
    if not usuario_actual or usuario_actual['rol'] != 'ciudadano':
        st.warning("🔒 Para consultar sus expedientes de forma segura y privada, por favor inicie sesión en la barra lateral con su Cédula y la contraseña que asignó al registrar su solicitud.")
    else:
        cedula_usuario = usuario_actual['cedula']
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT e.id, e.numero_expediente, e.materia, e.sintesis_hechos, e.pretension, e.estado_caso, e.fecha_ingreso,
                       CONCAT(p1.nombres, ' ', p1.apellidos) as solicitante, p1.cedula, p1.telefono as tel_sol, p1.direccion_habitacion as dir_sol,
                       CONCAT(p2.nombres, ' ', p2.apellidos) as requerido, p2.direccion_habitacion as dir_req
                FROM expedientes e
                JOIN personas p1 ON e.solicitante_id = p1.id
                JOIN personas p2 ON e.requerido_id = p2.id
                WHERE p1.cedula = %s
                ORDER BY e.fecha_ingreso DESC
            """
            cursor.execute(query, (cedula_usuario,))
            casos = cursor.fetchall()
            conn.close()
            
            if casos:
                st.success(f"Mostrando expedientes asociados a la Cédula: **{cedula_usuario}**")
                for caso in casos:
                    with st.expander(f"📌 Expediente: {caso['numero_expediente']} | Estado: {caso['estado_caso']}"):
                        st.write(f"**Materia:** {caso['materia']}")
                        st.write(f"**Requerido:** {caso['requerido']}")
                        st.write(f"**Fecha de Ingreso:** {caso['fecha_ingreso']}")
                        st.write(f"**Hechos:** {caso['sintesis_hechos']}")
                        st.write(f"**Pretensión:** {caso['pretension']}")
                        
                        pdf_data = generar_pdf_auto_inicio(
                            caso['numero_expediente'], caso['solicitante'], caso['cedula'],
                            caso['tel_sol'], caso['dir_sol'], caso['requerido'],
                            caso['dir_req'], caso['materia'], caso['sintesis_hechos'], caso['pretension']
                        )
                        st.download_button(
                            label="📄 Descargar Auto de Inicio",
                            data=pdf_data,
                            file_name=f"Auto_Inicio_{caso['numero_expediente']}.pdf",
                            mime="application/pdf",
                            key=f"dl_ciud_{caso['id']}"
                        )
            else:
                st.info("No se encontraron solicitudes registradas con su número de cédula.")
        except Exception as e:
            st.error(f"Error consultando la base de datos: {e}")

# TAB 3: MÓDULO DEL JUEZ DE PAZ / GESTIÓN DE EXPEDIENTES
with menu[2]:
    st.subheader("⚖️ Módulo de Gestión y Decisión del Juez de Paz Comunal")
    st.info("Visualización integral de expedientes, registro de actuaciones y actualización de estatus con marca de tiempo oficial.")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Cambiamos fecha_creacion por id para ordenar por el registro más reciente
        cursor.execute("SELECT * FROM expedientes ORDER BY id DESC")
        expedientes = cursor.fetchall()
        conn.close()
    except Exception as e:
        st.error(f"Error al conectar con la base de datos para cargar expedientes: {e}")
        expedientes = []
        
    if not expedientes:
        st.warning("No hay expedientes registrados en el sistema actualmente.")
    else:
        st.write(f"Total de expedientes en el sistema: **{len(expedientes)}**")
        
# Buscador rápido o filtro por estado
        filtro_estado = st.selectbox("Filtrar expedientes por estatus:", ["Todos", "Pendiente", "En Mediación", "Conciliado", "Remitido"])
        
        for exp in expedientes:
            # Claves seguras para evitar KeyErrors si las columnas de la BD tienen nombres distintos
            exp_id = exp.get('id', 'S/N')
            solicitante = exp.get('solicitante') or exp.get('nombre_solicitante') or exp.get('nombres_solicitante') or 'No especificado'
            solicitado = exp.get('solicitado') or exp.get('nombre_solicitado') or exp.get('nombres_solicitado') or 'No especificado'
            estado = exp.get('estado_caso') or exp.get('estado') or 'Pendiente'
            motivo = exp.get('motivo') or exp.get('descripcion') or 'Sin motivo'
            fecha_creacion = exp.get('fecha_creacion') or exp.get('fecha') or 'No registrada'
            
            if filtro_estado != "Todos" and estado != filtro_estado:
                continue
                
            # Color distintivo según el estado
            badge_color = "orange" if estado == "Pendiente" else "blue" if estado == "En Mediación" else "green"
            
            with st.expander(f"📁 Expediente #{exp_id} - Solicitante: {solicitante} vs {solicitado} [{estado}]"):
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown(f"**Motivo / Conflicto:** {motivo}")
                    st.markdown(f"**Fecha de Recepción:** {fecha_creacion}")
                    
                with col_info2:
                    st.markdown(f"**Estatus Actual:** :{badge_color}[{estado}]")
                    fecha_act = exp.get('fecha_actualizacion_estatus', 'Pendiente de actualización')
                    st.markdown(f"**Última Modificación:** {fecha_act}")
                
                st.markdown("---")
                st.markdown("#### 🛠️ Acciones del Despacho y Actualización")
                
                col_st1, col_st2 = st.columns([2, 1])
                
                with col_st1:
                    opciones_estado = ["Pendiente", "En Mediación", "Conciliado", "Remitido"]
                    idx_actual = opciones_estado.index(estado) if estado in opciones_estado else 0
                    
                    nuevo_estado = st.selectbox(
                        "Cambiar Estatus del Caso",
                        opciones_estado,
                        index=idx_actual,
                        key=f"sel_st_{exp_id}"
                    )
                
                with col_st2:
                    st.write("") # Espaciado vertical
                    st.write("")
                    if st.button("💾 Guardar Estatus", key=f"btn_st_{exp_id}", use_container_width=True):
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE expedientes SET estado_caso = %s, fecha_actualizacion_estatus = NOW() WHERE id = %s",
                                (nuevo_estado, exp_id)
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"¡Estatus actualizado a '{nuevo_estado}' con sello de tiempo oficial!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar el estatus: {e}")
                
            # Color distintivo según el estado
            badge_color = "orange" if exp['estado_caso'] == "Pendiente" else "blue" if exp['estado_caso'] == "En Mediación" else "green"
            
                with st.expander(f"📁 Expediente #{exp_id} - Solicitante: {solicitante} vs {solicitado} [{estado}]"):
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown(f"**Motivo / Conflicto:** {exp['motivo']}")
                    st.markdown(f"**Fecha de Recepción:** {exp['fecha_creacion']}")
                    
                with col_info2:
                    st.markdown(f"**Estatus Actual:** :{badge_color}[{exp['estado_caso']}]")
                    # Mostramos la fecha del último cambio de estatus registrado
                    fecha_act = exp.get('fecha_actualizacion_estatus', 'Pendiente de actualización')
                    st.markdown(f"**Última Modificación:** {fecha_act}")
                
                st.markdown("---")
                st.markdown("#### 🛠️ Acciones del Despacho y Actualización")
                
                col_st1, col_st2 = st.columns([2, 1])
                
                with col_st1:
                    nuevo_estado = st.selectbox(
                        "Cambiar Estatus del Caso",
                        ["Pendiente", "En Mediación", "Conciliado", "Remitido"],
                        index=["Pendiente", "En Mediación", "Conciliado", "Remitido"].index(exp['estado_caso']) if exp['estado_caso'] in ["Pendiente", "En Mediación", "Conciliado", "Remitido"] else 0,
                        key=f"sel_st_{exp['id']}"
                    )
                
                with col_st2:
                    st.write("") # Espaciado vertical para alinear el botón
                    st.write("")
                    if st.button("💾 Guardar Estatus", key=f"btn_st_{exp['id']}", use_container_width=True):
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            # Actualiza el estatus y registra automáticamente la fecha y hora exacta
                            cursor.execute(
                                "UPDATE expedientes SET estado_caso = %s, fecha_actualizacion_estatus = NOW() WHERE id = %s",
                                (nuevo_estado, exp['id'])
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"¡Estatus actualizado a '{nuevo_estado}' con sello de tiempo oficial!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar el estatus: {e}")

# TAB 4: MARCO LEGAL Y COMPETENCIAS
with menu[3]:
    st.subheader("📚 Marco Legal, Institucional y Competencias")
    
    st.markdown("### 👨‍⚖️ Competencias del Juez de Paz Comunal")
    st.info("Extracto oficial conforme a la normativa vigente que rige la actuación de la Jurisdicción Especial.")
    
    # Visualizador destacado del Artículo 8
    with st.expander("📖 Ver Artículo 8: Competencias del Juez o Jueza de Paz Comunal (Ley Orgánica Vigente)", expanded=True):
        st.markdown("""
        **Artículo 8.** El Juez o Jueza de Paz Comunal tiene competencia para:
        1. **Conocer y resolver** mediante la conciliación, la mediación o el fallo en equidad, los conflictos comunitarios, vecinales y familiares que le sean sometidos a su consideración.
        2. **Conocer de los hechos, actos u omisiones** que alteren la convivencia comunitaria o atenten contra la tranquilidad, la paz y las buenas costumbres en el ámbito local.
        3. **Dictar las medidas preventivas y de protección** que correspondan dentro del marco de su competencia para garantizar la paz y la armonía social.
        4. **Articular** con los órganos del Poder Público y las organizaciones del Poder Popular la resolución de los problemas colectivos de la comunidad.
        5. **Ejercer funciones pedagógicas y preventivas** orientadas a fomentar la cultura de paz, el diálogo, la solidaridad y la resolución pacífica de los conflictos.
        6. Las demás que le señalen la Constitución de la República Bolivariana de Venezuela, las leyes y los reglamentos aplicables.
        """)
    
    st.markdown("---")
    st.markdown("### 📥 Repositorio Documental y Normativo (PDF)")
    st.write("Seleccione la categoría de su interés para descargar de forma directa los textos legales oficiales respaldados en el sistema:")
    
    # Categoría 1: Justicia de Paz y Poder Popular
    st.markdown("#### 🏛️ 1. Justicia de Paz Comunal y Poder Popular")
    c1, c2 = st.columns(2)
    with c1:
        ruta = "docs/Ley Orgánica de la Justicia de Paz Comunal Vigente.pdf"
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                st.download_button("📄 Ley Orgánica de Justicia de Paz Comunal", f, file_name="Ley_Organica_Justicia_Paz_Comunal.pdf", mime="application/pdf", key="d1")
        ruta_comunas = "docs/Ley-Organica-de-las-Comunas.pdf"
        if os.path.exists(ruta_comunas):
            with open(ruta_comunas, "rb") as f:
                st.download_button("📄 Ley Orgánica de las Comunas", f, file_name="Ley_Organica_Comunas.pdf", mime="application/pdf", key="d2")
        ruta_consejos = "docs/Ley Orgánica de Reforma de la Ley de los Consejos Comunales Vigente.pdf"
        if os.path.exists(ruta_consejos):
            with open(ruta_consejos, "rb") as f:
                st.download_button("📄 Ley de los Consejos Comunales (Reforma)", f, file_name="Ley_Consejos_Comunales.pdf", mime="application/pdf", key="d3")
    with c2:
        ruta_pp = "docs/Ley-Organica-del-Poder-Popular.pdf"
        if os.path.exists(ruta_pp):
            with open(ruta_pp, "rb") as f:
                st.download_button("📄 Ley Orgánica del Poder Popular", f, file_name="Ley_Poder_Popular.pdf", mime="application/pdf", key="d4")
        ruta_seco = "docs/Ley-Organica-del-Sistema-Economico-Comunal.pdf"
        if os.path.exists(ruta_seco):
            with open(ruta_seco, "rb") as f:
                st.download_button("📄 Sistema Económico Comunal", f, file_name="Sistema_Economico_Comunal.pdf", mime="application/pdf", key="d5")
        ruta_gestion = "docs/Ley-Organica-de-Gestion-comunitaria.pdf"
        if os.path.exists(ruta_gestion):
            with open(ruta_gestion, "rb") as f:
                st.download_button("📄 Ley de Gestión Comunitaria", f, file_name="Gestion_Comunitaria.pdf", mime="application/pdf", key="d6")

    # Categoría 2: Planificación, Contraloría y Gobierno
    st.markdown("#### 📊 2. Planificación, Contraloría Social y Gobierno")
    c3, c4 = st.columns(2)
    with c3:
        ruta_plan = "docs/Ley-Organica-de-Planificacion-Publica-y-Popular.pdf"
        if os.path.exists(ruta_plan):
            with open(ruta_plan, "rb") as f:
                st.download_button("📄 Planificación Pública y Popular", f, file_name="Planificacion_Publica.pdf", mime="application/pdf", key="d7")
        ruta_contra = "docs/Ley-Organica-de-Contraloria-Social.pdf"
        if os.path.exists(ruta_contra):
            with open(ruta_contra, "rb") as f:
                st.download_button("📄 Ley Orgánica de Contraloría Social", f, file_name="Contraloria_Social.pdf", mime="application/pdf", key="d8")
    with c4:
        ruta_cfg = "docs/Ley-Organica-del-Consejo-Federal-de-Gobierno-y-su-Reglamento.pdf"
        if os.path.exists(ruta_cfg):
            with open(ruta_cfg, "rb") as f:
                st.download_button("📄 Consejo Federal de Gobierno", f, file_name="Consejo_Federal_Gobierno.pdf", mime="application/pdf", key="d9")
        ruta_reg_eco = "docs/Reglamento-Parcial-de-la-Ley-Organica-de-la-economia-comunal.pdf"
        if os.path.exists(ruta_reg_eco):
            with open(ruta_reg_eco, "rb") as f:
                st.download_button("📄 Regl. Parcial Economía Comunal", f, file_name="Reglamento_Economia_Comunal.pdf", mime="application/pdf", key="d10")

    # Categoría 3: Constitucional, Derechos Humanos, Protección y Civil
    st.markdown("#### ⚖️ 3. Marco Constitucional, Derechos Humanos y Sustantivo")
    c5, c6 = st.columns(2)
    with c5:
        ruta_crbv = "docs/Constitución de la República Bolivariana de Venezuela.pdf"
        if os.path.exists(ruta_crbv):
            with open(ruta_crbv, "rb") as f:
                st.download_button("📄 Constitución de la RBV (CRBV)", f, file_name="Constitucion_CRBV.pdf", mime="application/pdf", key="d11")
        ruta_dudh = "docs/Declaracion-Universal-de-Derechos-Humanos.pdf"
        if os.path.exists(ruta_dudh):
            with open(ruta_dudh, "rb") as f:
                st.download_button("📄 Declaración Universal de DDHH", f, file_name="Declaracion_Universal_DDHH.pdf", mime="application/pdf", key="d12")
        ruta_lopnna = "docs/Ley Orgánica de Protección al Niño, Niña y Adolescentes.pdf"
        if os.path.exists(ruta_lopnna):
            with open(ruta_lopnna, "rb") as f:
                st.download_button("📄 LOPNNA", f, file_name="LOPNNA.pdf", mime="application/pdf", key="d13")
    with c6:
        ruta_vcm = "docs/Ley Orgánica sobre el Derecho de las Mujeres a una Vida Libre de Violencia Vigente.pdf"
        if os.path.exists(ruta_vcm):
            with open(ruta_vcm, "rb") as f:
                st.download_button("📄 Ley Sobre la Violencia de Género", f, file_name="Ley_Violencia_Genero.pdf", mime="application/pdf", key="d14")
        ruta_cc = "docs/codigo_civil_venezuela.pdf"
        if os.path.exists(ruta_cc):
            with open(ruta_cc, "rb") as f:
                st.download_button("📄 Código Civil Venezolano", f, file_name="Codigo_Civil.pdf", mime="application/pdf", key="d15")
        ruta_cpc = "docs/Codigo-Procedimiento-Civil.pdf"
        if os.path.exists(ruta_cpc):
            with open(ruta_cpc, "rb") as f:
                st.download_button("📄 Código de Procedimiento Civil", f, file_name="Codigo_Procedimiento_Civil.pdf", mime="application/pdf", key="d16")

    st.markdown("---")
    st.markdown("### 🌐 Enlaces Externos de Interés Institucional")
    st.markdown("""
    * [Tribunal Supremo de Justicia (TSJ)](http://www.tsj.gob.ve)
    * [Ministerio del Poder Popular para Relaciones Interiores, Justicia y Paz](http://www.mpprijp.gob.ve)
    * [Ministerio del Poder Popular para las Comunas y los Movimientos Sociales](http://www.mincomunas.gob.ve)
    """)
