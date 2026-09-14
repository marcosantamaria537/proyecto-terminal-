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
from src.data import load_geojson_bytes, quality_summary
from src.map_view import render_surveillance_map
from src.postgres_data import DatabaseLoadError, load_postgres_data


ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Vigilancia CONANP",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_styles() -> None:
    styles = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)


def require_optional_password() -> None:
    try:
        expected = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        expected = ""
    if not expected or st.session_state.get("authenticated"):
        return
    st.title("Acceso al tablero")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar", type="primary", use_container_width=True):
        if password == expected:
            st.session_state.authenticated = True
            st.rerun()
        st.error("La contraseña no es correcta.")
    st.stop()


@st.cache_data(show_spinner=False)
def cached_geojson_load(file_bytes: bytes, filename: str) -> dict:
    return load_geojson_bytes(file_bytes, filename)


def filter_period_and_polygon(
    data: pd.DataFrame,
    start_date: date,
    end_date: date,
    polygons: list[str],
) -> pd.DataFrame:
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    mask = data["fecha"].between(start, end)
    if polygons:
        mask &= data["poligono"].astype(str).isin(polygons)
    return data.loc[mask].copy()


apply_styles()
require_optional_password()

try:
    connection = st.connection("postgresql", type="sql")
    supervisions, recorridos, fault_details = load_postgres_data(connection)
except DatabaseLoadError as exc:
    st.error(str(exc))
    st.info(
        "Comprueba el archivo .streamlit/secrets.toml y confirma que primero hayas "
        "ejecutado cargar_postgres.py."
    )
    st.stop()

with st.sidebar:
    st.markdown("### Fuente de información")
    st.success("PostgreSQL conectado")
    st.caption("Base: registro_recorridos · Esquema: dw")

    polygon_file = st.file_uploader(
        "Polígonos geográficos",
        type=["geojson", "json", "zip"],
        help="GeoJSON o ZIP que contenga un archivo .geojson/.json.",
    )
    polygons_geojson = None
    if polygon_file:
        try:
            polygons_geojson = cached_geojson_load(
                polygon_file.getvalue(), polygon_file.name
            )
        except Exception as exc:
            st.warning(f"No fue posible leer los polígonos: {exc}")

    st.divider()
    st.markdown("### Filtros")
    all_dates = pd.concat(
        [supervisions["fecha"], recorridos["fecha"]], ignore_index=True
    ).dropna()
    min_date = all_dates.min().date()
    max_date = all_dates.max().date()
    selected_dates = st.date_input(
        "Periodo",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = (
            selected_dates if isinstance(selected_dates, date) else min_date
        )

    polygon_options = sorted(
        set(supervisions["poligono"].dropna().astype(str))
        | set(recorridos["poligono"].dropna().astype(str))
    )
    selected_polygons = st.multiselect(
        "Polígono", polygon_options, placeholder="Todos"
    )
    fault_options = sorted(
        fault_details["tipo_falta"].dropna().astype(str).unique()
    )
    selected_faults = st.multiselect(
        "Tipo de falta", fault_options, placeholder="Todos"
    )
    st.caption("El periodo y el polígono se aplican a supervisiones y recorridos.")

filtered_supervisions = filter_period_and_polygon(
    supervisions, start_date, end_date, selected_polygons
)
filtered_recorridos = filter_period_and_polygon(
    recorridos, start_date, end_date, selected_polygons
)
filtered_fault_details = filter_period_and_polygon(
    fault_details, start_date, end_date, selected_polygons
)

if selected_faults:
    filtered_fault_details = filtered_fault_details[
        filtered_fault_details["tipo_falta"].isin(selected_faults)
    ]
    selected_ids = filtered_fault_details["supervision_id"].unique()
    filtered_supervisions = filtered_supervisions[
        filtered_supervisions["supervision_id"].isin(selected_ids)
    ]

header_left, header_right = st.columns([5, 1])
with header_left:
    st.markdown(
        '<p class="eyebrow">MONITOREO Y VIGILANCIA</p>', unsafe_allow_html=True
    )
    st.title("Tablero de recorridos y faltas")
    st.caption(
        "Parque Nacional Costa Occidental de Isla Mujeres, Punta Cancún y Punta Nizuc"
    )
with header_right:
    st.markdown('<div class="brand-mark">CONANP</div>', unsafe_allow_html=True)

kpis = calculate_kpis(filtered_supervisions, filtered_recorridos)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Faltas registradas", f"{kpis['faltas']:,}")
m2.metric("Recorridos", f"{kpis['recorridos']:,}")
m3.metric("Supervisiones con falta", f"{kpis['porcentaje_con_falta']:.1f}%")
m4.metric("Kilómetros recorridos", f"{kpis['kilometros']:,.1f}")

if filtered_supervisions.empty and filtered_recorridos.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

overview_tab, spatial_tab, records_tab, quality_tab = st.tabs(
    ["Resumen", "Análisis espacial", "Registros", "Calidad de datos"]
)

with overview_tab:
    left, right = st.columns([1.6, 1])
    with left:
        st.plotly_chart(
            build_monthly_trend(filtered_supervisions, filtered_recorridos),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            build_fault_type_chart(filtered_fault_details), use_container_width=True
        )
    left, right = st.columns([1.35, 1])
    with left:
        st.plotly_chart(
            build_day_hour_heatmap(filtered_supervisions), use_container_width=True
        )
    with right:
        st.plotly_chart(
            build_measure_chart(filtered_supervisions), use_container_width=True
        )

with spatial_tab:
    render_surveillance_map(filtered_supervisions, polygons_geojson)

with records_tab:
    st.markdown("#### Supervisiones")
    supervision_columns = [
        "fecha", "hora", "tipos_falta", "poligono", "subzona",
        "subpoligono", "medida_tomada", "embarcacion_anonima",
        "num_faltas", "fuente",
    ]
    visible_supervisions = filtered_supervisions[
        [c for c in supervision_columns if c in filtered_supervisions.columns]
    ].sort_values("fecha", ascending=False)
    st.dataframe(
        visible_supervisions, use_container_width=True, hide_index=True, height=360
    )
    st.download_button(
        "Descargar supervisiones en CSV",
        data=visible_supervisions.to_csv(index=False).encode("utf-8-sig"),
        file_name="supervisiones_conanp_filtradas.csv",
        mime="text/csv",
    )

    st.markdown("#### Recorridos")
    recorrido_columns = [
        "fecha", "hora_inicio", "hora_fin", "poligono", "subzona",
        "subpoligono", "tipo_actividad", "vehiculo", "km_recorridos",
    ]
    visible_recorridos = filtered_recorridos[
        [c for c in recorrido_columns if c in filtered_recorridos.columns]
    ].sort_values("fecha", ascending=False)
    st.dataframe(
        visible_recorridos, use_container_width=True, hide_index=True, height=320
    )

with quality_tab:
    quality = quality_summary(supervisions)
    q1, q2, q3 = st.columns(3)
    q1.metric("Supervisiones cargadas", f"{quality['registros']:,}")
    q2.metric("Fechas válidas", f"{quality['fechas_validas_pct']:.1f}%")
    q3.metric(
        "Polígonos identificados", f"{quality['poligonos_identificados_pct']:.1f}%"
    )
    st.markdown("#### Campos con valores faltantes")
    st.dataframe(quality["faltantes"], use_container_width=True, hide_index=True)
    st.markdown("#### Controles del modelo")
    controls = connection.query(
        "SELECT * FROM dw.vw_control_calidad ORDER BY control", ttl=0
    )
    st.dataframe(controls, use_container_width=True, hide_index=True)

st.caption(
    "Dashboard descriptivo para apoyar la supervisión ambiental. Los recorridos y "
    "las supervisiones se muestran por separado porque no tienen una llave común."
)

