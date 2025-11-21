import pytest
import streamlit as st
from operator_view import _render_form_from_structure

# NOTA: Este test es un esqueleto, ya que la funcionalidad depende de interacción UI y session_state.
# Se recomienda usar Selenium o Playwright para pruebas end-to-end reales.

def test_render_form_with_gps_and_map(monkeypatch):
    # Simula una estructura de formulario con campo de geolocalización
    structure = [
        {"Tipo de Campo": "Geolocalización", "Etiqueta del Campo": "Ubicación"}
    ]
    # Simula coordenadas por mapa
    coords = {"lat": 10.123456, "lng": -84.654321}
    # Simula coordenadas por GPS
    gps_coords = {"lat": 11.111111, "lng": -85.555555}

    # Simula session_state vacío
    st.session_state.clear()
    # Simula que el usuario hace clic en el mapa
    monkeypatch.setitem(st.session_state, 'form_field_Ubicación_coords', coords)
    # Sin GPS: debe priorizar mapa
    form_data = _render_form_from_structure(structure)
    assert form_data["Ubicación"] == coords

    # Ahora simula que el usuario captura por GPS
    gps_key = 'form_field_Ubicación_gps'
    monkeypatch.setitem(st.session_state, gps_key, gps_coords)
    form_data = _render_form_from_structure(structure)
    assert form_data["Ubicación"] == gps_coords

    # Simula limpiar GPS
    del st.session_state[gps_key]
    form_data = _render_form_from_structure(structure)
    assert form_data["Ubicación"] == coords

    # Simula sin ninguna coordenada
    st.session_state.clear()
    form_data = _render_form_from_structure(structure)
    assert form_data["Ubicación"] is None
