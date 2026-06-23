import streamlit as st
from supabase import create_client, Client

# REGISTRO DE SEGURIDAD INTERNA DE STREAMLIT (SECRETS)
# El sistema absorberá las llaves que configuraremos de forma oculta en su panel.
URL_SUPABASE = st.secrets["SUPABASE_URL"]
KEY_SUPABASE = st.secrets["SUPABASE_ANON_KEY"]

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# Configuración de interfaz móvil
st.set_page_config(page_title="Nutrición - JM de los Ríos", page_icon="🏥", layout="centered")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "medico_adjunto_id" not in st.session_state:
    st.session_state.medico_adjunto_id = None

# --- PANTALLA 1: LOGIN DE ADJUNTOS ---
if not st.session_state.autenticado:
    st.title("🏥 Servicio de Nutrición")
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
    st.title("📝 Registro de Consulta")
    st.write("Servicio de Nutrición Pediátrica - JM de los Ríos")
    
    if st.button("Cerrar Sesión 🔓"):
        st.session_state.autenticado = False
        st.session_state.medico_adjunto_id = None
        st.rerun()
        
    st.markdown("---")
    
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
    
    st.subheader("2. Detalles de la Consulta")
    
    tipo_consulta_opciones = {"Primera Vez (1)": "1", "Triaje (T)": "T", "Sucesiva (S)": "S"}
    tipo_consulta_sel = st.selectbox("Tipo de Consulta *", list(tipo_consulta_opciones.keys()))
    tipo_consulta = tipo_consulta_opciones[tipo_consulta_sel]
    
    ref_institucion = st.text_input("Referencia: Institución")
    ref_servicio = st.text_input("Referencia: Servicio")
    
    tipo_diag = st.selectbox("Diagnóstico *", ["Primera vez", "Sucesivo", "Asociado"])
    graffar = st.selectbox("Graffar *", ["I", "II", "III", "IV", "V"])
    
    try:
        req_residentes = supabase.table("medicos")\
            .select("id_medico, nombre_completo, tipo_residente")\
            .eq("rol", "Residente")\
            .eq("activo", True)\
            .execute()
        
        dict_residentes = {f"{r['nombre_completo']} ({r['tipo_residente']})": r['id_medico'] for r in req_residentes.data}
        residente_sel = st.selectbox("Médico Residente Evaluador *", list(dict_residentes.keys()))
        id_residente = dict_residentes[residente_sel]
    except:
        st.error("Error al cargar la lista de médicos residentes.")
        id_residente = None

    st.markdown("---")
    
    if st.button("🚀 Registrar Consulta en el Sistema", use_container_width=True):
        if cedula_rep and nombre_paciente and estado and ciudad and municipio and id_residente:
            try:
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
                
                supabase.table("consultas_nutricion").insert({
                    "id_paciente": id_nuevo_paciente,
                    "tipo_consulta": tipo_consulta,
                    "referencia_institucion": ref_institucion,
                    "referencia_servicio": ref_servicio,
                    "tipo_diagnostico": tipo_diag,
                    "graffar": graffar,
                    "medico_residente_id": id_residente,
                    "medico_adjunto_id": st.session_state.medico_adjunto_id
                }).execute()
                
                st.success("¡Consulta guardada con éxito en Supabase!")
                st.balloons()
            except Exception as e:
                st.error(f"Error al guardar los datos: {str(e)}")
        else:
            st.error("Por favor, rellene todos los campos obligatorios marcados con (*).")
