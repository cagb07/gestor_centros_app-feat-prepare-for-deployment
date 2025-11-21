import streamlit as st
import pandas as pd
import database
import json
import base64
import streamlit.components.v1 as components
from typing import Any, NoReturn
try:
    import importlib
    module = importlib.import_module("streamlit_javascript")
    st_javascript = getattr(module, "st_javascript")
    if not callable(st_javascript):
        raise ImportError("streamlit_javascript.st_javascript no es callable")
except Exception:
    # Si la dependencia no está instalada, definimos un stub que lanza una excepción controlada
    ST_JAVASCRIPT_AVAILABLE = False
    def st_javascript(code: Any, key: Any = None, timeout: int = 5000) -> NoReturn:
        raise RuntimeError("streamlit-javascript no está instalado. Instala la dependencia para habilitar GPS via JS.")
else:
    ST_JAVASCRIPT_AVAILABLE = True
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

# Helper: modal HTML + postMessage listener (usa streamlit_javascript)
def show_geo_modal(label: str, field_key: str, timeout_ms: int = 15000):
        """Renderiza un modal HTML que solicita la ubicación y publica el resultado
        mediante postMessage. Retorna el JSON string recibido o None.
        """
        modal_id = f"geo_modal_{field_key}"
        import html as _html
        label_esc = _html.escape(label)
        # Usar plantilla sin f-string para evitar que las llaves de JS sean interpretadas
        modal_html = """
        <div id="__MODAL_ID__" style="font-family:Arial,Helvetica,sans-serif;padding:10px;border-radius:8px;background:#fff;">
            <h3>Obtener ubicación — __LABEL__</h3>
            <p>Presiona el botón para solicitar permisos de ubicación al navegador.</p>
            <button id="btn_get_geo" style="padding:10px 14px;border-radius:6px;background:#0b5fff;color:#fff;border:none;cursor:pointer">📍 Capturar ubicación</button>
            <button id="btn_close" style="padding:8px 12px;margin-left:8px;border-radius:6px;background:#ccc;color:#000;border:none;cursor:pointer">Cerrar</button>
            <div id="geo_result" style="margin-top:12px;color:#222"></div>
            <script>
                const btn = document.getElementById('btn_get_geo');
                const btnClose = document.getElementById('btn_close');
                const res = document.getElementById('geo_result');
                btn.addEventListener('click', ()=>{
                    res.innerText = 'Solicitando ubicación...';
                    navigator.geolocation.getCurrentPosition(
                        p => {
                            const payload = {source: 'streamlit-geo-modal', lat: p.coords.latitude, lng: p.coords.longitude};
                            window.parent.postMessage(payload, '*');
                            res.innerText = `Lat: ${p.coords.latitude.toFixed(6)}, Lng: ${p.coords.longitude.toFixed(6)}`;
                        },
                        e => {
                            const payload = {source: 'streamlit-geo-modal', error: e.message};
                            window.parent.postMessage(payload, '*');
                            res.innerText = 'Error: ' + e.message;
                        }, {enableHighAccuracy:true, timeout: 10000}
                    );
                });
                btnClose.addEventListener('click', ()=>{ res.innerText='Modal cerrado'; window.parent.postMessage({source:'streamlit-geo-modal', closed:true}, '*'); });
            </script>
        </div>
        """
        modal_html = modal_html.replace('__MODAL_ID__', modal_id).replace('__LABEL__', label_esc)
        try:
                components.html(modal_html, height=240, scrolling=False)
        except Exception:
                pass

        if not ST_JAVASCRIPT_AVAILABLE:
                return None

        js_listener = (
                "new Promise((resolve, reject) => {"
                "function handler(e){ try{ if(e.data && e.data.source === 'streamlit-geo-modal'){ window.removeEventListener('message', handler); resolve(JSON.stringify(e.data)); }}catch(err){} }"
                "window.addEventListener('message', handler);"
                f"setTimeout(()=>{{ window.removeEventListener('message', handler); reject('timeout'); }},{timeout_ms});"
                "})"
        )
        try:
                res = st_javascript(js_listener, key=f"js_geo_modal_listener_{field_key}")
                return res
        except Exception:
                return None

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

        # Normalizar claves del centro adjunto para evitar problemas de mayúsculas/minúsculas
        centro_dict = {str(k).upper(): v for k, v in st.session_state.centro_adjunto.items()}

        for form_label, csv_col in FORM_TO_CSV_MAP.items():
            # csv_col viene en mayúsculas en el mapeo
            if csv_col and str(csv_col).upper() in centro_dict:
                prefill_data[form_label] = centro_dict[str(csv_col).upper()]
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
            # Claves para session_state
            gps_session_key = f"{field_key}_gps"
            map_click_key = f"{field_key}_map_click"

            # Priorizar centro del mapa en este orden: GPS guardado, clic previo en mapa, centro por defecto
            default_center = [9.9333, -84.0833]  # Costa Rica
            stored_gps = st.session_state.get(gps_session_key)
            stored_map_click = st.session_state.get(map_click_key)

            try:
                # Elegir centro y crear mapa
                if stored_gps and isinstance(stored_gps, dict) and 'lat' in stored_gps and 'lng' in stored_gps:
                    center = [float(stored_gps['lat']), float(stored_gps['lng'])]
                elif stored_map_click and isinstance(stored_map_click, dict) and 'lat' in stored_map_click and 'lng' in stored_map_click:
                    center = [float(stored_map_click['lat']), float(stored_map_click['lng'])]
                else:
                    center = default_center

                m = folium.Map(location=center, zoom_start=12 if center != default_center else 7)

                # Si hay coordenadas guardadas por GPS, añadir marcador visible
                if stored_gps and isinstance(stored_gps, dict):
                    try:
                        folium.Marker(location=[float(stored_gps['lat']), float(stored_gps['lng'])],
                                      popup='Ubicación guardada (GPS)',
                                      icon=folium.Icon(color='red', icon='map-marker')).add_to(m)
                    except Exception:
                        pass

                # Si hay coordenadas por clic previo en el mapa, añadir marcador
                if stored_map_click and isinstance(stored_map_click, dict):
                    try:
                        folium.CircleMarker(location=[float(stored_map_click['lat']), float(stored_map_click['lng'])],
                                            radius=6, color='blue', fill=True, fill_opacity=0.7,
                                            popup='Ubicación seleccionada en mapa').add_to(m)
                    except Exception:
                        pass

                # Añadimos LatLngPopup para que al hacer clic se obtenga lat/lng
                folium.LatLngPopup().add_to(m)
                map_data = st_folium(m, key=field_key, width=700, height=400)

                # Procesar retorno de st_folium: persistir clics en session_state
                coords = None
                if map_data:
                    if isinstance(map_data, dict):
                        if map_data.get('last_clicked'):
                            coords = map_data['last_clicked']
                        elif map_data.get('last_object_clicked'):
                            coords = map_data['last_object_clicked']
                    elif isinstance(map_data, (list, tuple)) and len(map_data) >= 2:
                        try:
                            coords = {'lat': float(map_data[0]), 'lng': float(map_data[1])}
                        except Exception:
                            coords = None

                # Normalizar y guardar clic del mapa en session_state para mostrar marcador en reruns
                if coords and isinstance(coords, dict) and 'lat' in coords and 'lng' in coords:
                    try:
                        coords = {'lat': float(coords['lat']), 'lng': float(coords['lng'])}
                        st.session_state[map_click_key] = coords
                    except Exception:
                        pass

                # Elegir valor final para el formulario: GPS > mapa clic > None
                if stored_gps:
                    form_data[label] = stored_gps
                    st.write(f"✅ **Ubicación GPS capturada:** {stored_gps['lat']:.6f}, {stored_gps['lng']:.6f}")
                elif st.session_state.get(map_click_key):
                    mc = st.session_state.get(map_click_key)
                    form_data[label] = mc
                    st.write(f"📍 **Ubicación seleccionada en mapa:** {mc['lat']:.6f}, {mc['lng']:.6f}")
                else:
                    form_data[label] = None

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
                        # Si el dict contiene coordenadas lat/lng, insertamos un mapa interactivo (Leaflet)
                        try:
                                if 'lat' in val and 'lng' in val:
                                        # Crear un div único para el mapa
                                        map_div_id = f"map_print_{key.replace(' ', '_')}_{int(abs(hash(key)) % 100000)}"
                                        lat = float(val['lat'])
                                        lng = float(val['lng'])
                                        zoom_level = 15  # zoom cercano para visualización (aprox. "80%" más cercano)
                                        map_html = f'''
<div id="{map_div_id}" style="width:100%;height:400px;border:1px solid #ddd;margin-bottom:8px"></div>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    (function(){{
        try{{
            var map = L.map('{map_div_id}').setView([{lat}, {lng}], {zoom_level});
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom: 19}}).addTo(map);
            L.marker([{lat}, {lng}]).addTo(map).bindPopup('Ubicación: {lat:.6f}, {lng:.6f}');
        }}catch(e){{ console.error(e); }}
    }})();
</script>
'''
                                        display = map_html
                                else:
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

        # Campo de búsqueda para filtrar centros por nombre
        search_query = st.text_input("Buscar centro (por nombre)", key="operator_search_query")

        if 'CENTRO_EDUCATIVO' in df_centros.columns:
            lista_nombres_centros = sorted(df_centros['CENTRO_EDUCATIVO'].astype(str).unique().tolist())
            if search_query and search_query.strip():
                lower_q = search_query.strip().lower()
                lista_nombres_centros = [n for n in lista_nombres_centros if lower_q in n.lower()]
        else:
            lista_nombres_centros = []

        centro_para_adjuntar = st.selectbox(
            "Escriba o seleccione el nombre del centro que desea adjuntar:",
            options=lista_nombres_centros,
            index=0 if lista_nombres_centros else None,
            format_func=lambda x: x,
            key="operator_attach_selectbox"
        )

        if st.button("Adjuntar Centro Seleccionado", key="btn_adjuntar_operator"):
            if centro_para_adjuntar:
                try:
                    datos_centro_seleccionado = df_centros[df_centros['CENTRO_EDUCATIVO'] == centro_para_adjuntar].iloc[0]
                    st.session_state.centro_adjunto = datos_centro_seleccionado.to_dict()
                    st.success(f"¡{centro_para_adjuntar} adjuntado!")
                    st.info("Ahora vaya a la pestaña 'Llenar Formulario' para ver la información pre-llenada.")
                except Exception:
                    st.error("No se pudo adjuntar el centro seleccionado. Revisa el nombre o el CSV de centros.")
            else:
                st.warning("Por favor, selecciona un centro de la lista.")

        # Mostrar preview del centro seleccionado (si existe)
        if 'operator_attach_selectbox' in st.session_state and st.session_state.operator_attach_selectbox:
            try:
                preview = df_centros[df_centros['CENTRO_EDUCATIVO'] == st.session_state.operator_attach_selectbox]
                if not preview.empty:
                    st.subheader("Vista previa del centro seleccionado")
                    st.write(preview.iloc[0].to_dict())
            except Exception:
                pass

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
                st.divider()
                st.subheader("⚙️ Captura de Ubicación GPS")
                for field in form_structure:
                    if field.get("Tipo de Campo") == "Geolocalización":
                        label = field["Etiqueta del Campo"]
                        field_key = f"form_field_{label.replace(' ', '_')}"
                        gps_session_key = f"{field_key}_gps"

                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.write(f"**{label}**")
                        with col2:
                            if not ST_JAVASCRIPT_AVAILABLE:
                                st.info("El método 'Usar mi ubicación' no está disponible en este despliegue. Usa el mapa o introduce coordenadas manualmente abajo.")

                            if st.button(f"📍 Capturar", key=f"btn_gps_out_{field_key}", use_container_width=True):
                                # Intentar abrir modal con postMessage (más fiable en algunos navegadores)
                                if ST_JAVASCRIPT_AVAILABLE:
                                    modal_res = show_geo_modal(label, field_key)
                                    gps_res = None
                                    if modal_res:
                                        gps_payload = None
                                        # Depuración opcional
                                        if st.session_state.get('debug_geo'):
                                            st.write("Modal raw response:", modal_res)
                                        try:
                                            # modal_res puede ser JSON string, dict, o mensajes como 'timeout'
                                            if isinstance(modal_res, str):
                                                s = modal_res.strip()
                                                if not s:
                                                    st.warning("Respuesta vacía del modal.")
                                                elif s.lower() in ('timeout', 'null', 'none'):
                                                    st.warning(f"Modal terminó con estado: {s}")
                                                    gps_payload = {'error': s}
                                                else:
                                                    try:
                                                        gps_payload = json.loads(s)
                                                    except Exception:
                                                        # Intentar ast.literal_eval como fallback para dicts sin comillas
                                                        try:
                                                            import ast
                                                            gps_payload = ast.literal_eval(s)
                                                        except Exception:
                                                            # No se pudo parsear
                                                            st.warning(f"Respuesta del modal no es JSON: {s}")
                                                            gps_payload = None
                                            elif isinstance(modal_res, dict):
                                                gps_payload = modal_res
                                            else:
                                                gps_payload = modal_res
                                        except Exception as e:
                                            st.error(f"Error procesando respuesta del modal: {e}")

                                        if gps_payload:
                                            # Manejar errores enviados desde el modal
                                            if isinstance(gps_payload, dict) and gps_payload.get('error'):
                                                st.error(f"Error GPS: {gps_payload.get('error')}")
                                            elif isinstance(gps_payload, dict) and gps_payload.get('closed'):
                                                st.info("Modal cerrado por el usuario.")
                                            else:
                                                try:
                                                    lat = float(gps_payload.get('lat'))
                                                    lng = float(gps_payload.get('lng'))
                                                    gps_coords = {'lat': lat, 'lng': lng}
                                                    st.session_state[gps_session_key] = gps_coords
                                                    st.success(f"✅ Ubicación detectada: {gps_coords['lat']:.6f}, {gps_coords['lng']:.6f}")
                                                except Exception as e:
                                                    st.error(f"La respuesta del modal no contiene lat/lng válidos: {e}")
                                        else:
                                            st.warning("⚠️ No se obtuvo ubicación desde el modal. Verifica permisos del navegador o usa la entrada manual.")
                                    else:
                                        st.warning("⚠️ No se obtuvo ubicación desde el modal. Verifica permisos del navegador o usa la entrada manual.")
                                else:
                                    st.warning("El método 'Usar mi ubicación' no está disponible en este despliegue. Usa la entrada manual o el mapa.")

                            # Campo alternativo manual para ingresar coordenadas (útil si JS o permisos fallan)
                            manual_lat = st.text_input(f"Latitud manual — {label}", value="", key=f"manual_lat_{field_key}")
                            manual_lng = st.text_input(f"Longitud manual — {label}", value="", key=f"manual_lng_{field_key}")
                            if st.button(f"Guardar coordenadas manuales — {label}", key=f"btn_save_manual_{field_key}"):
                                try:
                                    if manual_lat and manual_lng:
                                        lat = float(manual_lat.strip())
                                        lng = float(manual_lng.strip())
                                        # Guardar tanto en la clave GPS como en el clic de mapa para visualizar marcador inmediatamente
                                        st.session_state[gps_session_key] = {'lat': lat, 'lng': lng}
                                        # También guardar como mapa click para mostrar marcador
                                        map_click_key = f"{field_key}_map_click"
                                        st.session_state[map_click_key] = {'lat': lat, 'lng': lng}
                                        st.success(f"Coordenadas guardadas manualmente: {lat:.6f}, {lng:.6f}")
                                        # Forzar rerun para que el mapa actualice y muestre el marcador
                                        st.rerun()
                                    else:
                                        st.warning("Ingresa latitud y longitud válidas antes de guardar.")
                                except Exception:
                                    st.error("Formato inválido. Usa números decimales para latitud y longitud, por ejemplo: 9.9333")
                        with col3:
                            if st.session_state.get(gps_session_key):
                                if st.button("🗑️ Limpiar", key=f"btn_clear_gps_{field_key}", use_container_width=True):
                                    # Eliminar tanto la ubicación GPS como cualquier clic persistido en el mapa
                                    try:
                                        if gps_session_key in st.session_state:
                                            del st.session_state[gps_session_key]
                                    except Exception:
                                        pass
                                    try:
                                        map_click_key = f"{field_key}_map_click"
                                        if map_click_key in st.session_state:
                                            del st.session_state[map_click_key]
                                    except Exception:
                                        pass
                                    st.success("Coordenadas eliminadas.")

                        # Mostrar coordenadas actuales si existen
                        if st.session_state.get(gps_session_key):
                            coords = st.session_state[gps_session_key]
                            st.info(f"Coordenadas guardadas: {coords['lat']:.6f}, {coords['lng']:.6f}")
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