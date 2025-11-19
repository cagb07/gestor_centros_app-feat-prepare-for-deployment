import streamlit as st
import pandas as pd
import database
import json

def show_ui(df_centros):
    st.title(f"Panel de Administrador")
    
    tab_list = [
        "📊 Dashboard",
        "🔎 Buscador de Centros",
        "🛠️ Creador de Formularios",
        "🗂️ Gestión de Áreas",
        "👤 Gestión de Usuarios",
        "📋 Revisión de Envíos"
    ]
    
    tab_dashboard, tab_buscador, tab_creator, tab_areas, tab_users, tab_review = st.tabs(tab_list)

    # --- 1. DASHBOARD ---
    with tab_dashboard:
        st.header("Dashboard de Operaciones")
        
        try:
            total_envios = database.get_total_submission_count()
            envios_area = database.get_submission_count_by_area()
            envios_usuario = database.get_submission_count_by_user()
            
            st.metric("Total de Formularios Enviados", total_envios)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Envíos por Área")
                if not envios_area.empty:
                    st.bar_chart(envios_area.set_index("area_name"))
                else:
                    st.info("Aún no hay envíos.")
            
            with col2:
                st.subheader("Actividad por Usuario")
                if not envios_usuario.empty:
                    st.dataframe(envios_usuario, use_container_width=True)
                else:
                    st.info("Aún no hay envíos.")
                    
        except Exception as e:
            st.error(f"Error cargando el dashboard: {e}")

    # --- 2. BUSCADOR DE CENTROS (CON LÓGICA DE ADJUNTAR) ---
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
            key="admin_attach_selectbox"
        )

        if st.button("Adjuntar Centro Seleccionado", key="btn_adjuntar_admin"):
            if centro_para_adjuntar:
                datos_centro_seleccionado = df_centros[
                    df_centros['CENTRO_EDUCATIVO'] == centro_para_adjuntar
                ].iloc[0]
                
                st.session_state.centro_adjunto = datos_centro_seleccionado.to_dict()
                
                st.success(f"¡{centro_para_adjuntar} adjuntado!")
                st.info("Los datos se pre-llenarán en la pestaña 'Llenar Formulario' (vista de Operador).")
            else:
                st.warning("Por favor, seleccione un centro de la lista.")

    # --- 3. CREADOR DE FORMULARIOS ---
    with tab_creator:
        st.header("Creador de Plantillas de Formularios")
        
        with st.form("new_template_form"):
            st.subheader("Detalles de la Plantilla")
            
            area_options = {}  # Initialize to an empty dictionary
            try:
                areas_list = database.get_all_areas()
                area_options = {area['id']: area['name'] for area in areas_list}
                if not area_options:
                    st.warning("No hay áreas creadas. Vaya a 'Gestión de Áreas' primero.")
                    # No usar st.stop() aquí para evitar abortar el render de otras pestañas.
                    # El formulario de creación de plantillas requiere áreas; mostramos
                    # un aviso y omitimos el constructor de campos.
                    area_options = {}
            except Exception as e:
                st.error(f"Error cargando áreas: {e}")
                area_options = {}
            
            template_name = st.text_input("Nombre de la Plantilla", placeholder="Ej: Reporte de Visita Técnica")
            if area_options:
                template_area_id = st.selectbox(
                    "Asignar al Área:", 
                    options=area_options.keys(), 
                    format_func=lambda x: area_options[x]
                )
            else:
                st.info("No hay áreas disponibles. Cree un área primero en 'Gestión de Áreas'.")
                template_area_id = None
            
            st.subheader("Constructor de Campos")
            st.write("Defina los campos que tendrá este formulario.")
            
            field_types = ["Texto", "Área de Texto", "Fecha", "Tabla Dinámica", "Geolocalización", "Firma", "Carga de Imagen"]
            
            if 'template_fields' not in st.session_state:
                st.session_state.template_fields = pd.DataFrame(
                    [
                        {"Etiqueta del Campo": "Nombre del Visitante", "Tipo de Campo": "Texto", "Requerido": True},
                        {"Etiqueta del Campo": "Nombre del Centro", "Tipo de Campo": "Texto", "Requerido": False},
                        {"Etiqueta del Campo": "Provincia", "Tipo de Campo": "Texto", "Requerido": False},
                    ]
                )
            
            st.session_state.template_fields = st.data_editor(
                st.session_state.template_fields,
                num_rows="dynamic",
                column_config={
                    "Etiqueta del Campo": st.column_config.TextColumn(required=True),
                    "Tipo de Campo": st.column_config.SelectboxColumn(options=field_types, required=True),
                    "Requerido": st.column_config.CheckboxColumn(default=False)
                },
                use_container_width=True,
                height=300
            )
            
            submitted = st.form_submit_button("Guardar Plantilla")
            
            if submitted:
                if not template_name or st.session_state.template_fields.empty:
                    st.error("El nombre y al menos un campo son requeridos.")
                elif not template_area_id:
                    st.error("Debe seleccionar un área válida antes de guardar la plantilla.")
                else:
                    structure = st.session_state.template_fields.to_dict('records')
                    try:
                        database.save_form_template(
                            template_name,
                            structure,
                            st.session_state["user_id"],
                            template_area_id
                        )
                        st.success(f"¡Plantilla '{template_name}' guardada!")
                        del st.session_state.template_fields
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

    # --- 4. GESTIÓN DE ÁREAS ---
    with tab_areas:
        st.header("Gestión de Áreas de Formularios")
        
        with st.form("new_area_form", clear_on_submit=True):
            st.subheader("Crear Nueva Área")
            area_name = st.text_input("Nombre del Área")
            area_desc = st.text_area("Descripción")
            if st.form_submit_button("Crear Área"):
                if area_name and area_name.strip():
                    success, message = database.create_area(area_name.strip(), area_desc)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("El nombre es requerido.")
        
        st.divider()
        st.subheader("Áreas Existentes")
        try:
            areas_df = pd.DataFrame(database.get_all_areas())
            st.dataframe(areas_df.drop(columns=["description"]), use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar áreas: {e}")

    # --- 5. GESTIÓN DE USUARIOS ---
    with tab_users:
        st.header("Gestión de Usuarios")
        
        with st.form("new_user_form", clear_on_submit=True):
            st.subheader("Crear Nuevo Usuario")
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Nombre Completo")
                username = st.text_input("Nombre de Usuario (para login)")
            with col2:
                role = st.selectbox("Rol", ["operador", "admin"])
                password = st.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Crear Usuario"):
                if all([full_name, username, role, password]):
                    if len(password) < 8:
                        st.error("La contraseña debe tener al menos 8 caracteres.")
                    else:
                        success, message = database.create_user(username, password, role, full_name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.error("Todos los campos son requeridos.")
        
        st.divider()
        st.subheader("Usuarios Existentes")
        users_df = pd.DataFrame()
        try:
            users_df = database.get_all_users()
            st.dataframe(users_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar usuarios: {e}")
        
        st.subheader("Cambiar Contraseña de Usuario")
        try:
            if not users_df.empty:
                users_list = users_df.to_dict('records')
                user_options = {u['id']: f"{u['full_name']} ({u['username']})" for u in users_list}
                selected_user_id = st.selectbox("Seleccione el usuario:", options=list(user_options.keys()), format_func=lambda x: user_options[x])
                colp1, colp2 = st.columns(2)
                with colp1:
                    new_password = st.text_input("Nueva contraseña", type="password")
                with colp2:
                    new_password_confirm = st.text_input("Confirmar contraseña", type="password")

                if st.button("Cambiar Contraseña"):
                    if not new_password or not new_password_confirm:
                        st.error("Ambos campos de contraseña son requeridos.")
                    elif new_password != new_password_confirm:
                        st.error("Las contraseñas no coinciden.")
                    elif len(new_password) < 8:
                        st.error("La contraseña debe tener al menos 8 caracteres.")
                    else:
                        success, message = database.change_user_password(selected_user_id, new_password)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            else:
                st.info("No hay usuarios para modificar.")
        except Exception as e:
            st.error(f"Error al intentar cambiar contraseña: {e}")

    # --- 6. REVISIÓN DE ENVÍOS ---
    with tab_review:
        st.header("Revisión de Todos los Envíos")
        try:
            all_submissions_df = database.get_all_submissions_with_details()
            if all_submissions_df.empty:
                st.info("Aún no se han realizado envíos de formularios.")
            else:
                st.dataframe(all_submissions_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar envíos: {e}")