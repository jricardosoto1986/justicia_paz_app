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
        ssl_verify_cert=True
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

# --- Generador de PDF Auto de Inicio ---
def generar_pdf_auto_inicio(num_expediente, solicitante_nombre, solicitante_cedula, solicitante_tel, solicitante_dir, 
                            requerido_nombre, requerido_dir, materia, hechos, pretension):
    pdf = FPDF()
    pdf.add_page()
    
    if os.path.exists("assets/logo_tsj.png"):
        pdf.image("assets/logo_tsj.png", x=10, y=8, w=22)
    if os.path.exists("assets/logo_paz_comunal.png"):
        pdf.image("assets/logo_paz_comunal.png", x=175, y=8, w=22)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, limpiar_texto("REPÚBLICA BOLIVARIANA DE VENEZUELA"), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto("JURISDICCIÓN ESPECIAL DE LA JUSTICIA DE PAZ COMUNAL"), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto("CIRCUITO COMUNAL SANTA LAGUNA DEL VALLE DE LOS LAURELES"), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto("SAN JUAN DE LOS MORROS - ESTADO GUÁRICO"), 0, 1, "C")
    pdf.ln(6)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, limpiar_texto("AUTO DE INICIO DE PROCEDIMIENTO Y FIJACIÓN DE AUDIENCIA INICIAL"), 0, 1, "C")
    pdf.set_font("Arial", "", 9)
    
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 5, limpiar_texto(f"Lugar y Fecha: San Juan de los Morros, {fecha_hoy}"), 0, 1, "R")
    pdf.cell(0, 5, limpiar_texto(f"EXPEDIENTE N°: {num_expediente}"), 0, 1, "R")
    pdf.ln(4)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, limpiar_texto("1. IDENTIFICACIÓN DE LAS PARTES Y DATOS DE NOTIFICACIÓN:"), 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    
    sol_info = (
        f"* PARTE SOLICITANTE: {solicitante_nombre}, C.I. N° {solicitante_cedula}.\n"
        f"  - Teléfono: {solicitante_tel if solicitante_tel else 'No registrado'}\n"
        f"  - Domicilio: {solicitante_dir}"
    )
    pdf.multi_cell(0, 5, limpiar_texto(sol_info))
    pdf.ln(2)
    
    req_info = (
        f"* PARTE REQUERIDA (CITADO): {requerido_nombre}.\n"
        f"  - Domicilio / Ubicación para citación: {requerido_dir}"
    )
    pdf.multi_cell(0, 5, limpiar_texto(req_info))
    pdf.ln(3)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, limpiar_texto(f"2. MATERIA DEL CONFLICTO: {materia.upper()}"), 0, 1, "L")
    pdf.cell(0, 6, limpiar_texto("3. DESCRIPCIÓN DETALLADA DE LOS HECHOS:"), 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, limpiar_texto(hechos if hechos else "No especificado."))
    pdf.ln(3)
    
    if pretension:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, limpiar_texto("4. PRETENSIÓN / PROPUESTA DE ARREGLO:"), 0, 1, "L")
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, limpiar_texto(pretension))
        pdf.ln(3)
        
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, limpiar_texto("5. ORDEN DE SUSTANCIACIÓN Y FIJACIÓN DE AUDIENCIA INICIAL:"), 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    
    orden_texto = (
        "Vista la solicitud presentada, este Despacho de Paz Comunal ADMITE la presente causa "
        "y ORDENA la apertura del expediente formal. En cumplimiento del lapso legal establecido, "
        "se FIJA la celebración de la AUDIENCIA INICIAL DE CONCILIACIÓN dentro de los ocho (8) días "
        "hábiles siguientes en la Sede de la Oficina de Justicia de Paz Comunal."
    )
    pdf.multi_cell(0, 5, limpiar_texto(orden_texto))
    pdf.ln(16)
    
    col_width = 90
    pdf.cell(col_width, 5, "_______________________________________", 0, 0, "C")
    pdf.cell(col_width, 5, "_______________________________________", 0, 1, "C")
    pdf.cell(col_width, 5, limpiar_texto(solicitante_nombre), 0, 0, "C")
    pdf.cell(col_width, 5, limpiar_texto("Juez(a) de Paz Comunal"), 0, 1, "C")
    pdf.cell(col_width, 5, limpiar_texto("Firma del Solicitante"), 0, 0, "C")
    pdf.cell(col_width, 5, limpiar_texto("Firma y Sello del Despacho"), 0, 1, "C")
    
    return bytes(pdf.output())

# --- Generador de Boleta de Citación ---
def generar_boleta_citacion(num_expediente, requerido_nombre, requerido_dir, solicitante_nombre):
    pdf = FPDF()
    pdf.add_page()
    
    if os.path.exists("assets/logo_tsj.png"):
        pdf.image("assets/logo_tsj.png", x=10, y=8, w=22)
    if os.path.exists("assets/logo_paz_comunal.png"):
        pdf.image("assets/logo_paz_comunal.png", x=175, y=8, w=22)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, limpiar_texto("REPÚBLICA BOLIVARIANA DE VENEZUELA"), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto("JURISDICCIÓN ESPECIAL DE LA JUSTICIA DE PAZ COMUNAL"), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto("CIRCUITO COMUNAL SANTA LAGUNA DEL VALLE DE LOS LAURELES"), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto("SAN JUAN DE LOS MORROS - ESTADO GUÁRICO"), 0, 1, "C")
    pdf.ln(8)
    
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 7, limpiar_texto("BOLETA DE CITACIÓN FORMAL"), 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    
    fecha_emision = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 5, limpiar_texto(f"Lugar y Fecha de Emisión: San Juan de los Morros, {fecha_emision}"), 0, 1, "R")
    pdf.cell(0, 5, limpiar_texto(f"EXPEDIENTE N°: {num_expediente}"), 0, 1, "R")
    pdf.ln(6)
    
    pdf.set_font("Arial", "", 10)
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
    pdf.multi_cell(0, 6, limpiar_texto(texto_citacion))
    pdf.ln(25)
    
    col_width = 90
    pdf.cell(col_width, 5, "_______________________________________", 0, 0, "C")
    pdf.cell(col_width, 5, "_______________________________________", 0, 1, "C")
    pdf.cell(col_width, 5, limpiar_texto("Juez(a) de Paz Comunal"), 0, 0, "C")
    pdf.cell(col_width, 5, limpiar_texto("Firma / Huella de Recepción del Citado"), 0, 1, "C")
    pdf.cell(col_width, 5, limpiar_texto("Firma y Sello del Despacho"), 0, 0, "C")
    pdf.cell(col_width, 5, limpiar_texto("Fecha de Notificación: ___/___/202_"), 0, 1, "C")
    
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
c1, c2, c3 = st.columns([1, 4, 1])
with c1:
    if os.path.exists("assets/logo_tsj.png"):
        st.image("assets/logo_tsj.png", width=90)
with c2:
    st.markdown("<h2 style='text-align: center;'>⚖️ Justicia de Paz Comunal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Circuito Comunal Santa Laguna del Valle de los Laureles - San Juan de los Morros</p>", unsafe_allow_html=True)
with c3:
    if os.path.exists("assets/logo_paz_comunal.png"):
        st.image("assets/logo_paz_comunal.png", width=90)

st.markdown("---")

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
menu = st.tabs(["📝 Registrar Solicitud", "🔍 Consultar Mis Expedientes", "👨‍⚖️ Módulo del Juez de Paz"])

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
                    
                    # Registrar o actualizar usuario ciudadano
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

# TAB 3: MÓDULO DEL JUEZ DE PAZ
with menu[2]:
    st.subheader("👨‍⚖️ Panel de Gestión del Juez de Paz")
    
    usuario_actual = st.session_state['usuario_logueado']
    if not usuario_actual or usuario_actual['rol'] != 'juez':
        st.warning("🔒 Esta sección está reservada exclusivamente para los Jueces de Paz Comunal. Inicie sesión con su cuenta de Juez en la barra lateral.")
    else:
        col_f1, col_f2 = st.columns(2)
        cc_filtro = col_f1.selectbox("Filtrar por Consejo Comunal:", CONSEJOS_COMUNALES)
        est_filtro = col_f2.selectbox("Filtrar por Estado del Caso:", ["Todos", "Recibido", "Citado", "En Audiencia", "Conciliado", "Archivado"])
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            sql = """
                SELECT e.id, e.numero_expediente, e.materia, e.sintesis_hechos, e.pretension, 
                       e.estado_caso, e.fecha_ingreso,
                       CONCAT(p1.nombres, ' ', p1.apellidos) as solicitante, p1.cedula as ced_sol, 
                       p1.telefono as tel_sol, p1.direccion_habitacion as dir_sol, p1.consejo_comunal,
                       CONCAT(p2.nombres, ' ', p2.apellidos) as requerido, p2.direccion_habitacion as dir_req
                FROM expedientes e
                JOIN personas p1 ON e.solicitante_id = p1.id
                JOIN personas p2 ON e.requerido_id = p2.id
                WHERE 1=1
            """
            params = []
            
            if cc_filtro != "Todos":
                sql += " AND p1.consejo_comunal = %s"
                params.append(cc_filtro)
                
            if est_filtro != "Todos":
                sql += " AND e.estado_caso = %s"
                params.append(est_filtro)
                
            sql += " ORDER BY e.fecha_ingreso DESC"
            
            cursor.execute(sql, tuple(params))
            expedientes_juez = cursor.fetchall()
            conn.close()
            
            st.metric("Total de Expedientes Filtrados", len(expedientes_juez))
            st.markdown("---")
            
            for exp in expedientes_juez:
                with st.expander(f"📁 Expediente {exp['numero_expediente']} - {exp['solicitante']} vs {exp['requerido']} [{exp['estado_caso']}]"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Datos del Solicitante:**")
                        st.write(f"- Cédula: {exp['ced_sol']}")
                        st.write(f"- Teléfono: {exp['tel_sol']}")
                        st.write(f"- Consejo Comunal: {exp['consejo_comunal']}")
                    with c2:
                        st.markdown("**Datos del Requerido:**")
                        st.write(f"- Nombre: {exp['requerido']}")
                        st.write(f"- Dirección Citación: {exp['dir_req']}")
                    
                    st.markdown("**Hechos y Pretensión:**")
                    st.info(f"**Hechos:** {exp['sintesis_hechos']}")
                    st.warning(f"**Pretensión:** {exp['pretension']}")
                    
                    col_st1, col_st2 = st.columns([2, 1])
                    nuevo_estado = col_st1.selectbox(
                        "Cambiar Estado del Caso:",
                        ["Recibido", "Citado", "En Audiencia", "Conciliado", "Archivado"],
                        index=["Recibido", "Citado", "En Audiencia", "Conciliado", "Archivado"].index(exp['estado_caso']),
                        key=f"st_sel_{exp['id']}"
                    )
                    
                    if col_st2.button("💾 Actualizar Estado", key=f"btn_st_{exp['id']}"):
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("UPDATE expedientes SET estado_caso = %s WHERE id = %s", (nuevo_estado, exp['id']))
                            conn.commit()
                            conn.close()
                            st.success("¡Estatus actualizado correctamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar estado: {e}")
                    
                    col_d1, col_d2 = st.columns(2)
                    
                    pdf_juez = generar_pdf_auto_inicio(
                        exp['numero_expediente'], exp['solicitante'], exp['ced_sol'],
                        exp['tel_sol'], exp['dir_sol'], exp['requerido'],
                        exp['dir_req'], exp['materia'], exp['sintesis_hechos'], exp['pretension']
                    )
                    col_d1.download_button(
                        label="📄 Descargar Auto de Inicio (PDF)",
                        data=pdf_juez,
                        file_name=f"Auto_Inicio_{exp['numero_expediente']}.pdf",
                        mime="application/pdf",
                        key=f"dl_juez_{exp['id']}"
                    )
                    
                    pdf_boleta = generar_boleta_citacion(
                        exp['numero_expediente'], exp['requerido'], exp['dir_req'], exp['solicitante']
                    )
                    col_d2.download_button(
                        label="📨 Descargar Boleta de Citación (PDF)",
                        data=pdf_boleta,
                        file_name=f"Boleta_Citacion_{exp['numero_expediente']}.pdf",
                        mime="application/pdf",
                        key=f"dl_bol_{exp['id']}"
                    )

        except Exception as e:
            st.error(f"Error cargando módulo de juez: {e}")
