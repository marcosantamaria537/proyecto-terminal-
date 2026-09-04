from __future__ import annotations

import copy

import folium
import pandas as pd
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from src.data import normalize_name


POLYGON_KEYS = ["poligono", "nombre", "name", "zona", "anp", "subzona"]


def _prepare_geojson(geojson: dict) -> tuple[dict, str | None]:
    prepared = copy.deepcopy(geojson)
    selected_key = None
    for feature in prepared.get("features", []):
        properties = feature.get("properties") or {}
        normalized = {normalize_name(key): key for key in properties}
        source_key = next((normalized[key] for key in POLYGON_KEYS if key in normalized), None)
        if source_key:
            selected_key = source_key
            properties["__poligono_normalizado"] = normalize_name(properties.get(source_key, ""))
    return prepared, selected_key


def render_surveillance_map(data: pd.DataFrame, geojson: dict | None) -> None:
    coordinates = data.dropna(subset=["latitud", "longitud"])
    if not coordinates.empty:
        center = [float(coordinates["latitud"].median()), float(coordinates["longitud"].median())]
    else:
        center = [21.135, -86.76]
    map_object = folium.Map(location=center, zoom_start=10, tiles="CartoDB positron", control_scale=True)

    faults = data.loc[data["es_falta"]]
    if geojson:
        prepared, label_key = _prepare_geojson(geojson)
        polygon_counts = faults.groupby("poligono").size().rename("faltas").reset_index()
        polygon_counts["poligono_clave"] = polygon_counts["poligono"].map(normalize_name)
        folium.Choropleth(
            geo_data=prepared,
            data=polygon_counts,
            columns=["poligono_clave", "faltas"],
            key_on="feature.properties.__poligono_normalizado",
            fill_color="YlGn",
            fill_opacity=0.68,
            line_opacity=0.65,
            nan_fill_color="#DDE7E2",
            legend_name="Faltas registradas",
            name="Faltas por polígono",
        ).add_to(map_object)
        if label_key:
            folium.GeoJson(
                prepared,
                style_function=lambda _: {"fillOpacity": 0, "color": "#275A4C", "weight": 1},
                tooltip=folium.GeoJsonTooltip(fields=[label_key], aliases=["Polígono:"]),
            ).add_to(map_object)

    if not coordinates.empty:
        heat_points = faults.dropna(subset=["latitud", "longitud"])[["latitud", "longitud"]].values.tolist()
        if heat_points:
            HeatMap(heat_points, radius=17, blur=13, min_opacity=0.25, name="Concentración de faltas").add_to(map_object)
    elif not geojson:
        st.warning("Para mostrar el mapa se requieren coordenadas (LATITUD y LONGITUD) o un archivo GeoJSON de polígonos.")

    folium.LayerControl(collapsed=False).add_to(map_object)
    st_folium(map_object, use_container_width=True, height=560, returned_objects=[])

    counts = data.assign(faltas=data["es_falta"].astype(int)).groupby("poligono", as_index=False).agg(
        recorridos=("recorrido_id", "nunique"), faltas=("faltas", "sum")
    )
    counts["tasa_infraccion"] = (counts["faltas"] / counts["recorridos"] * 100).round(1)
    st.dataframe(counts.sort_values("faltas", ascending=False), width="stretch", hide_index=True)
