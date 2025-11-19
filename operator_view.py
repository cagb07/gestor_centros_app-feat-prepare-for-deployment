import streamlit as st
import pandas as pd
import database
import json
from streamlit_folium import st_folium
from streamlit_drawable_canvas import st_canvas

# --- LÓGICA DE PRE-LLENADO ---
# Mapeo de columnas CSV a etiquetas de formulario ESPERADAS
CSV_TO_FORM_MAP = {
    "CENTRO_EDUCATIVO": "Nombre del Centro",
    "PROVINCIA": "Provincia",
    "CANTON": "Cantón",
    "DISTRITO": "Distrito",
    "DIRECCION": "Dirección",
    "CODSABER": "Código Saber"
}

def _render_form_from_structure(structure):
    """Función interna para dibujar el formulario dinámico."""
    form_data = {}
    
    # --- LÓGICA DE PRE-LLENADO ---
    prefill_data = {}
    if "centro_adjunto" in st.session_state and st.session_state.centro_adjunto:
        # Invertir el mapa para buscar fácilmente por la etiqueta del formulario
        FORM_TO_CSV_MAP = {v: k for k, v in CSV_TO_FORM_MAP.items()}
        
        for form_label, csv_col in FORM_TO_CSV_MAP.items():
            if csv_col in st.session_state.centro_adjunto:
                prefill_data[form_label] = st.session_state.centro_adjunto[csv_col]
    # --- FIN LÓGICA PRE-LLENADO ---

    for field in structure:
        label = field["Etiqueta del Campo"]
        field_type = field["Tipo de Campo"]
        required = field["Requerido"]
        
        field_key = f"form_field_{label.replace(' ', '_')}" # Clave única
        
        # Obtener el valor por defecto del diccionario prefill_data
        default_value = prefill_data.get(label, None)
        
        # Add a visual indicator for required fields
        display_label = f"{label}*" if required else label

        if field_type == "Texto":
            form_data[label] = st.text_input(display_label, value=default_value, key=field_key)
        elif field_type == "Área de Texto":
            form_data[label] = st.text_area(display_label, value=default_value, key=field_key)
        elif field_type == "Fecha":
            form_data[label] = st.date_input(display_label, key=field_key)
        
        elif field_type == "Tabla Dinámica":
            st.subheader(display_label)
            df_editor = pd.DataFrame([{"Columna 1": "", "Columna 2": ""}])
            form_data[label] = st.data_editor(
                df_editor, 
                num_rows="dynamic", 
                key=field_key
            ).to_dict('records')
            
        elif field_type == "Geolocalización":
            st.subheader(display_label)
            map_center = [9.9333, -84.0833] # Centrar en Costa Rica
            map_data = st_folium(center=map_center, zoom=7, key=field_key, width=700, height=400)
            
            coords = None
            if map_data.get("last_clicked"):
                coords = map_data["last_clicked"]
                st.write(f"Coordenadas: {coords['lat']:.6f}, {coords['lng']:.6f}")
            form_data[label] = coords
            
        elif field_type == "Firma":
            st.subheader(display_label)
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=3,
                stroke_color="#000000",
                background_color="#FFFFFF",
                width=700,
                height=200,
                drawing_mode="freedraw",
                key=field_key
            )
            if canvas_result.image_data is not None:
                form_data[label] = canvas_result.image_data.tolist() 
            else:
                form_data[label] = None
        
        elif field_type == "Carga de Imagen":
            st.subheader(display_label)
            uploaded_file = st.file_uploader(display_label, type=["png", "jpg", "jpeg"], key=field_key)
            if uploaded_file:
                form_data[label] = uploaded_file.name
            else:
                form_data[label] = None
                
    return form_data

def _validate_form(form_data, structure):
    """Checks if all required fields are filled."""
    for field in structure:
        if field["Requerido"]:
            label = field["Etiqueta del Campo"]
            if form_data[label] is None or (isinstance(form_data[label], str) and not form_data[label].strip()):
                return False, f"El campo '{label}' es requerido."
    return True, ""


def show_ui(df_centros):
    st.title(f"Panel de Operador")
    
    tab_buscador, tab_fill_form, tab_my_submissions = st.tabs([
        "🔎 Buscador de Centros",
        "📝 Llenar Formulario",
        "📋 Mis Envíos"
    ])
    
    # --- 1. BUSCADOR DE CENTROS (CON LÓGICA DE ADJUNTAR) ---
    with tab_buscador:
        st.header("Consulta de Centros Educativos")
        st.info("Estos son los datos originales del archivo CSV.")
        st.dataframe(df_centros, use_container_width=True)
        
        st.divider()
        st.subheader("📎 Adjuntar Centro a un Formulario")
        st.write("Seleccione un centro de la lista para pre-llenar sus datos en un nuevo formulario.")

        lista_nombres_centros = sorted(df_centros['CENTRO_EDUCATIVO'].unique().tolist())

        centro_para_adjuntar = st.selectbox(
            "Escriba o seleccione el nombre del centro que desea adjuntar:",
            options=lista_nombres_centros,
            index=None,
            placeholder="Seleccione un centro...",
            key="operator_attach_selectbox"
        )

        if st.button("Adjuntar Centro Seleccionado", key="btn_adjuntar_operator"):
            if centro_para_adjuntar:
                datos_centro_seleccionado = df_centros[
                    df_centros['CENTRO_EDUCATIVO'] == centro_para_adjuntar
                ].iloc[0]
                
                st.session_state.centro_adjunto = datos_centro_seleccionado.to_dict()
                
                st.success(f"¡{centro_para_adjuntar} adjuntado!")
                st.info("Ahora vaya a la pestaña 'Llenar Formulario' para ver la información pre-llenada.")
            else:
                st.warning("Por favor, seleccione un centro de la lista.")

    # --- 2. LLENAR FORMULARIO ---
    with tab_fill_form:
        st.header("Llenar Nuevo Formulario")
        
        # Mostrar si hay un centro adjunto
        if "centro_adjunto" in st.session_state and st.session_state.centro_adjunto:
            centro_nombre = st.session_state.centro_adjunto['CENTRO_EDUCATIVO']
            st.success(f"**Centro Adjunto:** {centro_nombre}")
            st.write("La información se pre-llenará en los campos del formulario que coincidan.")
            
            if st.button("Quitar centro adjunto"):
                st.session_state.centro_adjunto = None
                st.rerun()
            st.divider()
        
        try:
            # Paso 1: Seleccionar Área
            areas_list = database.get_all_areas()
            area_options = {area['id']: area['name'] for area in areas_list}

            if not area_options:
                st.warning("No hay formularios disponibles. Contacte al administrador.")
                # No usamos st.stop() aquí; mostramos el aviso y evitamos renderizar
                # el selector de área para que el resto de la IU siga accesible.
                selected_area_id = None
            else:
                selected_area_id = st.selectbox(
                    "1. Seleccione el Área:",
                    options=area_options.keys(),
                    format_func=lambda x: area_options[x]
                )
            
            # Paso 2: Seleccionar Plantilla
            if not selected_area_id:
                st.info("Seleccione un área para ver los formularios disponibles.")
                template_options = {}
                selected_template_id = None
            else:
                template_list = database.get_templates_by_area(selected_area_id)
                template_options = {t['id']: t['name'] for t in template_list}

                if not template_options:
                    st.info("No hay formularios en esta área.")
                    selected_template_id = None
                else:
                    selected_template_id = st.selectbox(
                        "2. Seleccione el Formulario:",
                        options=template_options.keys(),
                        format_func=lambda x: template_options[x]
                    )
            
            # Paso 3: Renderizar el formulario
            st.divider()
            
            if not selected_template_id:
                st.info("Seleccione un formulario válido para llenarlo.")
                form_structure = None
            else:
                form_structure = database.get_template_structure(selected_template_id)
                if not form_structure:
                    st.error("No se pudo cargar la estructura de este formulario.")
                    form_structure = None
                
            with st.form("dynamic_form"):
                st.subheader(template_options[selected_template_id])
                
                # Renderizar todos los campos
                form_data = _render_form_from_structure(form_structure)
                
                submitted = st.form_submit_button("✅ Enviar Formulario")
            
            if submitted:
                is_valid, error_message = _validate_form(form_data, form_structure)
                if is_valid:
                    try:
                        database.save_submission(
                            selected_template_id,
                            st.session_state["user_id"],
                            form_data
                        )
                        st.success("¡Formulario enviado con éxito!")
                        st.balloons()
                        # Limpiar el centro adjunto después de un envío exitoso
                        if "centro_adjunto" in st.session_state:
                             st.session_state.centro_adjunto = None
                    except Exception as e:
                        st.error(f"Error al guardar el envío: {e}")
                else:
                    st.error(error_message)

        except Exception as e:
            st.error(f"Error cargando formularios: {e}")

    # --- 3. MIS ENVÍOS ---
    with tab_my_submissions:
        st.header("Historial de Mis Envíos")
        try:
            my_submissions_df = database.get_submissions_by_user(st.session_state["user_id"])
            if my_submissions_df.empty:
                st.info("Aún no has enviado ningún formulario.")
            else:
                st.dataframe(my_submissions_df.drop(columns=['data']), use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar tus envíos: {e}")