from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from src.analytics import (
    build_day_hour_heatmap,
    build_fault_type_chart,
    build_measure_chart,
    build_monthly_trend,
    calculate_kpis,
)
from src.data import (
    DataLoadError,
    filter_events,
    generate_demo_data,
    load_geojson_bytes,
    load_tabular_bytes,
    quality_summary,
)
from src.map_view import render_surveillance_map


ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Vigilancia CONANP",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_styles() -> None:
    st.markdown(f"<style>{(ROOT / 'assets' / 'styles.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def require_optional_password() -> None:
    """Enable a simple access gate only when APP_PASSWORD exists in secrets."""
    try:
        expected = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        expected = ""
    if not expected:
        return
    if st.session_state.get("authenticated"):
        return
    st.title("Acceso al tablero")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar", type="primary", width="stretch"):
        if password == expected:
            st.session_state.authenticated = True
            st.rerun()
        st.error("La contraseña no es correcta.")
    st.stop()


@st.cache_data(show_spinner=False)
def cached_tabular_load(file_bytes: bytes, filename: str) -> pd.DataFrame:
    return load_tabular_bytes(file_bytes, filename)


@st.cache_data(show_spinner=False)
def cached_geojson_load(file_bytes: bytes, filename: str) -> dict:
    return load_geojson_bytes(file_bytes, filename)


apply_styles()
require_optional_password()

with st.sidebar:
    st.markdown("### Fuente de información")
    data_file = st.file_uploader(
        "Registros de vigilancia",
        type=["xlsx", "xls", "csv", "db", "sqlite", "sqlite3"],
        help="Puedes cargar un Excel con varias hojas, un CSV o la bodega SQLite.",
    )
    polygon_file = st.file_uploader(
        "Polígonos geográficos",
        type=["geojson", "json", "zip"],
        help="GeoJSON o ZIP que contenga un archivo .geojson/.json.",
    )

    if data_file:
        try:
            events = cached_tabular_load(data_file.getvalue(), data_file.name)
            using_demo = False
        except DataLoadError as exc:
            st.error(str(exc))
            st.stop()
    else:
        events = generate_demo_data()
        using_demo = True

    polygons = None
    if polygon_file:
        try:
            polygons = cached_geojson_load(polygon_file.getvalue(), polygon_file.name)
        except DataLoadError as exc:
            st.warning(str(exc))

    st.divider()
    st.markdown("### Filtros")
    min_date = events["fecha"].min().date()
    max_date = events["fecha"].max().date()
    selected_dates = st.date_input(
        "Periodo",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = selected_dates if isinstance(selected_dates, date) else min_date

    polygon_options = sorted(events["poligono"].dropna().astype(str).unique())
    selected_polygons = st.multiselect("Polígono", polygon_options, placeholder="Todos")

    fault_options = sorted(events.loc[events["es_falta"], "tipo_falta"].dropna().astype(str).unique())
    selected_faults = st.multiselect("Tipo de falta", fault_options, placeholder="Todos")

    st.caption("Los filtros se aplican a todos los indicadores y visualizaciones.")

filtered = filter_events(
    events,
    start_date=start_date,
    end_date=end_date,
    polygons=selected_polygons,
    fault_types=selected_faults,
)

header_left, header_right = st.columns([5, 1])
with header_left:
    st.markdown('<p class="eyebrow">MONITOREO Y VIGILANCIA</p>', unsafe_allow_html=True)
    st.title("Tablero de recorridos y faltas")
    st.caption("Área de Protección de Flora y Fauna Costa Occidental de Isla Mujeres, Punta Cancún y Punta Nizuc")
with header_right:
    st.markdown('<div class="brand-mark">CONANP</div>', unsafe_allow_html=True)

if using_demo:
    st.info("Vista de demostración con datos sintéticos. Carga los archivos institucionales desde el panel lateral para analizar los registros reales.")

kpis = calculate_kpis(filtered)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Faltas registradas", f"{kpis['faltas']:,}")
m2.metric("Recorridos", f"{kpis['recorridos']:,}")
m3.metric("Tasa de infracción", f"{kpis['tasa']:.1f}%")
m4.metric("Kilómetros recorridos", f"{kpis['kilometros']:,.1f}")

if filtered.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

overview_tab, spatial_tab, records_tab, quality_tab = st.tabs(
    ["Resumen", "Análisis espacial", "Registros", "Calidad de datos"]
)

with overview_tab:
    left, right = st.columns([1.6, 1])
    with left:
        st.plotly_chart(build_monthly_trend(filtered), width="stretch")
    with right:
        st.plotly_chart(build_fault_type_chart(filtered), width="stretch")

    left, right = st.columns([1.35, 1])
    with left:
        st.plotly_chart(build_day_hour_heatmap(filtered), width="stretch")
    with right:
        st.plotly_chart(build_measure_chart(filtered), width="stretch")

with spatial_tab:
    render_surveillance_map(filtered, polygons)

with records_tab:
    safe_columns = [
        "fecha",
        "hora",
        "tipo_falta",
        "poligono",
        "subzona",
        "subpoligono",
        "medida_tomada",
        "embarcacion_anonima",
        "km_recorridos",
    ]
    visible = filtered[[column for column in safe_columns if column in filtered.columns]].copy()
    visible = visible.sort_values("fecha", ascending=False)
    st.dataframe(visible, width="stretch", hide_index=True, height=470)
    st.download_button(
        "Descargar selección en CSV",
        data=visible.to_csv(index=False).encode("utf-8-sig"),
        file_name="registros_conanp_filtrados.csv",
        mime="text/csv",
    )
    st.caption("La embarcación se presenta mediante un identificador anónimo; el nombre original no se muestra ni se exporta.")

with quality_tab:
    quality = quality_summary(events)
    q1, q2, q3 = st.columns(3)
    q1.metric("Registros cargados", f"{quality['registros']:,}")
    q2.metric("Fechas válidas", f"{quality['fechas_validas_pct']:.1f}%")
    q3.metric("Polígonos identificados", f"{quality['poligonos_identificados_pct']:.1f}%")
    st.markdown("#### Campos con valores faltantes")
    st.dataframe(quality["faltantes"], width="stretch", hide_index=True)
    with st.expander("Procedencia de los datos"):
        st.dataframe(
            events.groupby("tabla_origen", dropna=False).size().rename("registros").reset_index(),
            width="stretch",
            hide_index=True,
        )

st.caption("Dashboard descriptivo para apoyar la planeación de recorridos.")
