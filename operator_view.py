import streamlit as st
import pandas as pd
import database
import json
import base64
import streamlit.components.v1 as components
try:
    from streamlit_javascript import st_javascript
except Exception:
    # Si la dependencia no está instalada, definimos un stub que lanza una excepción controlada
    def st_javascript(code, key=None, timeout=5000):
        raise RuntimeError("streamlit-javascript no está instalado. Instala la dependencia para habilitar GPS via JS.")
try:
    import folium
except Exception:
    folium = None

try:
    from streamlit_folium import st_folium
except Exception:
    def st_folium(*args, **kwargs):
        raise RuntimeError("La dependencia 'streamlit_folium' no está instalada. Instálala para usar mapas.")

try:
    from streamlit_drawable_canvas import st_canvas
except Exception:
    def st_canvas(*args, **kwargs):
        raise RuntimeError("La dependencia 'streamlit_drawable_canvas' no está instalada. Instálala para usar firmas/canvas.")

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
            try:
                m = folium.Map(location=map_center, zoom_start=7)
                # Añadimos LatLngPopup para que al hacer clic se obtenga lat/lng
                folium.LatLngPopup().add_to(m)
                map_data = st_folium(m, key=field_key, width=700, height=400)

                coords = None
                # st_folium puede devolver 'last_clicked' con {'lat','lng'}
                if map_data:
                    if map_data.get('last_clicked'):
                        coords = map_data['last_clicked']
                    elif map_data.get('last_object_clicked'):
                        coords = map_data['last_object_clicked']
                    # some versions may return a tuple
                    elif isinstance(map_data, tuple) and len(map_data) >= 2:
                        try:
                            coords = {'lat': float(map_data[0]), 'lng': float(map_data[1])}
                        except Exception:
                            coords = None

                if coords:
                    st.write(f"Coordenadas: {coords['lat']:.6f}, {coords['lng']:.6f}")
                else:
                    st.info("Haga clic en el mapa para seleccionar coordenadas.")

                # Nota: no creamos botones dentro de st.form; la UI para solicitar
                # la ubicación via GPS se renderiza fuera del formulario en show_ui.
                # Aquí simplemente intentamos leer coordenadas registradas en
                # session_state (por acción del botón GPS) y usamos coords por clic.
                gps_session_key = f"{field_key}_gps"
                stored = st.session_state.get(gps_session_key, None)
                if stored:
                    form_data[label] = stored
                else:
                    # fallback: asignar coords (posible obtenido por clic en el mapa)
                    form_data[label] = coords
            except Exception as e:
                st.error(f"Error cargando componente de mapa: {e}")
                form_data[label] = None
            
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
            uploaded_files = st.file_uploader(display_label, type=["png", "jpg", "jpeg"], key=field_key, accept_multiple_files=True)
            images_list = []
            if uploaded_files:
                for uf in uploaded_files:
                    try:
                        raw = uf.read()
                        encoded = base64.b64encode(raw).decode('utf-8')
                        images_list.append({"filename": uf.name, "content_base64": encoded, "type": uf.type})
                    except Exception:
                        images_list.append({"filename": getattr(uf, 'name', 'unknown'), "content_base64": None, "type": getattr(uf, 'type', None)})
                form_data[label] = images_list
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


def _build_print_html(form_data, title="Formulario"):
    """Construye un HTML sencillo con los datos del formulario para impresión."""
    parts = [f"<h1>{title}</h1>", "<style>body{font-family:Arial,Helvetica,sans-serif;padding:20px}table{width:100%;border-collapse:collapse}td,th{border:1px solid #ddd;padding:8px;vertical-align:top}th{background:#f4f4f4;text-align:left}</style>"]
    parts.append("<table>")
    for key, val in form_data.items():
        parts.append("<tr>")
        parts.append(f"<th>{key}</th>")
        # Manejar distintos tipos de valor
        if val is None:
            display = "<em>(vacío)</em>"
        elif isinstance(val, list):
            # Si es lista de imágenes (diccionarios con base64)
            if val and isinstance(val[0], dict) and 'content_base64' in val[0]:
                imgs = []
                for im in val:
                    if im.get('content_base64'):
                        mime = im.get('type') or 'image/png'
                        imgs.append(f"<div style='margin-bottom:8px'><strong>{im.get('filename')}</strong><br><img src=\"data:{mime};base64,{im.get('content_base64')}\" style='max-width:400px;max-height:300px;'/></div>")
                    else:
                        imgs.append(f"<div><strong>{im.get('filename')}</strong> (no disponible)</div>")
                display = "".join(imgs)
            else:
                # tabla o lista de filas -> representar en JSON legible
                try:
                    display = "<pre>" + json.dumps(val, ensure_ascii=False, indent=2) + "</pre>"
                except Exception:
                    display = str(val)
        elif isinstance(val, dict):
            try:
                display = "<pre>" + json.dumps(val, ensure_ascii=False, indent=2) + "</pre>"
            except Exception:
                display = str(val)
        else:
            display = str(val)

        parts.append(f"<td>{display}</td>")
        parts.append("</tr>")
    parts.append("</table>")
    # Script para lanzar el diálogo de impresión al cargar el iframe
    parts.append("<script>window.onload=function(){setTimeout(function(){window.print();},300);}</script>")
    return "".join(parts)


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
            
            if form_structure:
                with st.form("dynamic_form"):
                    st.subheader(template_options[selected_template_id])
                    
                    # Renderizar todos los campos
                    form_data = _render_form_from_structure(form_structure)
                    
                    submitted = st.form_submit_button("✅ Enviar Formulario")
                # Fuera del formulario: botones específicos para campos Geolocalización
                # Iteramos la estructura para añadir botones GPS por cada campo geolocalización
                for field in form_structure:
                    if field.get("Tipo de Campo") == "Geolocalización":
                        label = field["Etiqueta del Campo"]
                        field_key = f"form_field_{label.replace(' ', '_')}"
                        gps_session_key = f"{field_key}_gps"
                        if st.button(f"Usar mi ubicación (GPS) — {label}", key=f"btn_gps_out_{field_key}"):
                            js_code = (
                                "new Promise((resolve, reject) => {"
                                "navigator.geolocation.getCurrentPosition("
                                "p => resolve(JSON.stringify({lat: p.coords.latitude, lng: p.coords.longitude})) ,"
                                "e => reject(e.message), {enableHighAccuracy:true});"
                                "})"
                            )
                            try:
                                gps_res = st_javascript(js_code, key=f"js_geo_out_{field_key}")
                            except RuntimeError as re:
                                st.error(str(re))
                                gps_res = None

                            if gps_res:
                                try:
                                    gps_coords = json.loads(gps_res)
                                    st.session_state[gps_session_key] = gps_coords
                                    st.success(f"Ubicación detectada: {gps_coords['lat']:.6f}, {gps_coords['lng']:.6f}")
                                except Exception as e:
                                    st.error(f"Error parseando coordenadas: {e}")
                            else:
                                st.info("No se obtuvo ubicación via JS. Usa el mapa o revisa permisos del navegador.")
            else:
                submitted = False
                form_data = {}
            # Botón para previsualizar / imprimir (fuera del form para que no interfiera con el submit)
            if form_structure and form_data:
                if st.button("🖨️ Previsualizar / Imprimir formulario", key="btn_preview_print"):
                    try:
                        printable = _build_print_html(form_data, template_options.get(selected_template_id, "Formulario"))
                        components.html(printable, height=700, scrolling=True)
                    except Exception as e:
                        st.error(f"Error generando vista imprimible: {e}")
            
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