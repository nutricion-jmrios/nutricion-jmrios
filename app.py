import streamlit as st
from supabase import create_client, Client

# REGISTRO DE SEGURIDAD INTERNA DE STREAMLIT (SECRETS)
URL_SUPABASE = st.secrets["SUPABASE_URL"]
KEY_SUPABASE = st.secrets["SUPABASE_ANON_KEY"]

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# Configuración de interfaz móvil
st.set_page_config(page_title="Nutrición - JM de los Ríos", page_icon="🏥", layout="centered")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "medico_adjunto_id" not in st.session_state:
    st.session_state.medico_adjunto_id = None
if "medico_adjunto_nombre" not in st.session_state:
    st.session_state.medico_adjunto_nombre = ""

# --- PANTALLA 1: LOGIN DE ADJUNTOS ---
if not st.session_state.autenticado:
    # Título con logo alineado a la izquierda (Proporción 1 a 5)
    col_tit1, col_tit2 = st.columns([1, 5])
    with col_tit1:
        st.image("logo_servicionutricion.jpg", width=60)

    st.subheader("Control de Acceso (Solo Adjuntos)")
    
    alias = st.text_input("Alias de Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar Sesión", use_container_width=True):
        if alias and password:
            try:
                respuesta = supabase.table("medicos")\
                    .select("id_medico, nombre_completo")\
                    .eq("alias", alias)\
                    .eq("password_hash", password)\
                    .eq("rol", "Adjunto")\
                    .eq("activo", True)\
                    .execute()
                
                if len(respuesta.data) > 0:
                    st.session_state.autenticado = True
                    st.session_state.medico_adjunto_id = respuesta.data[0]["id_medico"]
                    st.session_state.medico_adjunto_nombre = respuesta.data[0]["nombre_completo"]
                    st.success(f"Bienvenido/a {respuesta.data[0]['nombre_completo']}")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas o usuario no autorizado.")
            except Exception as e:
                st.error("Error de conexión con la base de datos. Intente de nuevo.")
        else:
            st.warning("Por favor, llene todos los campos.")

# --- PANTALLA 2: EL CUADERNO DIARIO DE CONSULTAS ---
else:
    # SECCIÓN DE LOGOS SUPERIORES
    col_logo1, col_logo2 = st.columns(2)
    with col_logo1:
        # Busca el archivo logo_hospital.png en tu repositorio
        st.image("logo_hospital.jpg", width=100, caption="Hosp. J.M. de los Ríos")
    with col_logo2:
        # Busca el archivo logo_servicio.png en tu repositorio
        st.image("logo_servicionutricion.jpg", width=100, caption="Servicio de Nutrición")

    st.title("📝 Registro de Consulta")
    
    if st.button("Cerrar Sesión 🔓"):
        st.session_state.autenticado = False
        st.session_state.medico_adjunto_id = None
        st.session_state.medico_adjunto_nombre = ""
        st.rerun()
        
    st.markdown("---")
    
    # 1. DATOS DEL PACIENTE
    st.subheader("1. Datos del Paciente")
    num_historia = st.text_input("Número de Historia Clínica (Opcional)")
    cedula_rep = st.text_input("Cédula del Representante *")
    nombre_paciente = st.text_input("Nombre Completo del Niño/a *")
    sexo = st.selectbox("Sexo *", ["M", "F"])
    fecha_nac = st.date_input("Fecha de Nacimiento *")
    
    lista_estados = [
        "Amazonas", "Anzoátegui", "Apure", "Aragua", "Barinas", "Bolívar", 
        "Carabobo", "Cojedes", "Delta Amacuro", "Distrito Capital", "Falcón", 
        "Guárico", "La Guaira", "Lara", "Mérida", "Miranda", "Monagas", 
        "Nueva Esparta", "Portuguesa", "Sucre", "Táchira", "Trujillo", 
        "Yaracuy", "Zulia"
    ]
    estado = st.selectbox("Estado (Venezuela) *", lista_estados)
    ciudad = st.text_input("Ciudad *")
    municipio = st.text_input("Municipio *")
    zona_res = st.text_area("Zona Residencial / Dirección Exacta")
    
    st.markdown("---")
    
    # 2. DETALLES DE LA CONSULTA
    st.subheader("2. Detalles de la Consulta")
    
    tipo_consulta_opciones = {"Primera Vez (1)": "1", "Triaje (T)": "T", "Sucesiva (S)": "S"}
    tipo_consulta_sel = st.selectbox("Tipo de Consulta *", list(tipo_consulta_opciones.keys()))
    tipo_consulta = tipo_consulta_opciones[tipo_consulta_sel]
    
    ref_institucion = st.text_input("Referencia: Institución")
    ref_servicio = st.text_input("Referencia: Servicio")
    
    tipo_diag = st.selectbox("Diagnóstico *", ["Primera vez", "Sucesivo", "Asociado"])
    graffar = st.selectbox("Graffar *", ["I", "II", "III", "IV", "V"])
    
    st.markdown("---")
    
    # 3. PERSONAL MÉDICO RESPONSABLE
    st.subheader("3. Personal Médico Responsable")
    
    # Lógica flexible para Residentes Externos
    residente_externo = st.checkbox("¿El residente evaluador es de OTRA especialidad o servicio?")
    
    id_residente = None
    nota_residente_externo = None
    
    if residente_externo:
        # Campo libre si viene de otra especialidad
        nota_residente_externo = st.text_input("Escriba Nombre, Rango y Especialidad del Residente *", 
                                               placeholder="Ej: Dr. Carlos Gómez (R2 - Cirugía Pediátrica)")
    else:
        # Cargar lista oficial desde Supabase si es del servicio
        try:
            req_residentes = supabase.table("medicos")\
                .select("id_medico, nombre_completo, tipo_residente")\
                .eq("rol", "Residente")\
                .eq("activo", True)\
                .execute()
            
            dict_residentes = {f"{r['nombre_completo']} ({r['tipo_residente']})": r['id_medico'] for r in req_residentes.data}
            residente_sel = st.selectbox("Médico Residente Evaluador (Del Servicio) *", list(dict_residentes.keys()))
            id_residente = dict_residentes[residente_sel]
        except:
            st.error("Error al cargar la lista de médicos residentes del servicio.")

    # Campo visual del Médico Adjunto (No editable, lo toma del Login automáticamente)
    st.text_input("Médico Adjunto Supervisor (Usted)", value=st.session_state.medico_adjunto_nombre, disabled=True)

    st.markdown("---")
    
    # ENVÍO DE DATOS
    if st.button("🚀 Registrar Consulta en el Sistema", use_container_width=True):
        # Validar si cumple las condiciones obligatorias de llenado
        validacion_residente = (residente_externo and nota_residente_externo) or (not residente_externo and id_residente)
        
        if cedula_rep and nombre_paciente and estado and ciudad and municipio and validacion_residente:
            try:
                # Si el residente es externo, lo guardamos en la dirección/observaciones o lo manejaremos en la consulta
                referencia_final_servicio = ref_servicio
                if residente_externo:
                    referencia_final_servicio = f"{ref_servicio} | Presentado por: {nota_residente_externo}".strip(" | ")

                # Paso 1: Insertar el paciente
                res_paciente = supabase.table("pacientes").insert({
                    "numero_historia": num_historia if num_historia else None,
                    "cedula_representante": cedula_rep,
                    "nombre_completo": nombre_paciente,
                    "sexo": sexo,
                    "fecha_nacimiento": str(fecha_nac),
                    "estado": estado,
                    "ciudad": ciudad,
                    "municipio": municipio,
                    "zona_residencial": zona_res
                }).execute()
                
                id_nuevo_paciente = res_paciente.data[0]["id_paciente"]
                
                # Paso 2: Insertar la consulta
                supabase.table("consultas_nutricion").insert({
                    "id_paciente": id_nuevo_paciente,
                    "tipo_consulta": tipo_consulta,
                    "referencia_institucion": ref_institucion,
                    "referencia_servicio": referencia_final_servicio,
                    "tipo_diagnostico": tipo_diag,
                    "graffar": graffar,
                    "medico_residente_id": id_residente, # Queda NULL si es externo, lo cual es correcto
                    "medico_adjunto_id": st.session_state.medico_adjunto_id
                }).execute()
                
                st.success("¡Consulta guardada con éxito en Supabase!")
                st.balloons()
            except Exception as e:
                st.error(f"Error al guardar los datos: {str(e)}")
        else:
            st.error("Por favor, rellene todos los campos obligatorios marcados con (*).")
