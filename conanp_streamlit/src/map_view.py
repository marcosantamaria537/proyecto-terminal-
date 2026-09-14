from __future__ import annotations

import copy
from typing import Iterator

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.data import normalize_name


POLYGON_KEYS = [
    "sector",
    "poligono",
    "nombre",
    "name",
    "zona",
    "anp",
    "subzona",
]


def _prepare_geojson(
    geojson: dict,
) -> tuple[dict, str | None]:
    """Prepara el GeoJSON para relacionarlo con PostgreSQL."""

    prepared = copy.deepcopy(geojson)
    selected_key = None

    for feature in prepared.get("features", []):
        properties = feature.setdefault("properties", {})

        normalized_keys = {
            normalize_name(str(key)): key
            for key in properties
        }

        source_key = next(
            (
                normalized_keys[key]
                for key in POLYGON_KEYS
                if key in normalized_keys
            ),
            None,
        )

        if source_key:
            selected_key = source_key
            properties["__poligono_normalizado"] = normalize_name(
                str(properties.get(source_key, ""))
            )

    return prepared, selected_key


def _iterate_coordinates(
    coordinates: list,
) -> Iterator[tuple[float, float]]:
    """Obtiene todos los puntos de Polygon y MultiPolygon."""

    if (
        isinstance(coordinates, list)
        and len(coordinates) >= 2
        and isinstance(coordinates[0], (int, float))
        and isinstance(coordinates[1], (int, float))
    ):
        yield float(coordinates[0]), float(coordinates[1])
        return

    if isinstance(coordinates, list):
        for item in coordinates:
            yield from _iterate_coordinates(item)


def _fit_geojson_bounds(
    map_object: folium.Map,
    geojson: dict,
) -> None:
    """Ajusta la vista para mostrar todos los polígonos."""

    points: list[tuple[float, float]] = []

    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        points.extend(_iterate_coordinates(coordinates))

    if not points:
        return

    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]

    map_object.fit_bounds(
        [
            [min(latitudes), min(longitudes)],
            [max(latitudes), max(longitudes)],
        ]
    )


def render_surveillance_map(
    data: pd.DataFrame,
    geojson: dict | None,
) -> None:
    """Construye el mapa coroplético de supervisiones."""

    coordinates = data.dropna(
        subset=["latitud", "longitud"]
    )

    if not coordinates.empty:
        center = [
            float(coordinates["latitud"].median()),
            float(coordinates["longitud"].median()),
        ]
    else:
        center = [21.135, -86.76]

    map_object = folium.Map(
        location=center,
        zoom_start=10,
        tiles="CartoDB positron",
        control_scale=True,
    )

    faults = data.loc[data["es_falta"]].copy()

    if geojson:
        prepared, label_key = _prepare_geojson(geojson)

        # Capa base para garantizar que los polígonos sean visibles.
        folium.GeoJson(
            prepared,
            name="Zonas marinas",
            style_function=lambda _: {
                "fillColor": "#70C5E8",
                "fillOpacity": 0.48,
                "color": "#174A5B",
                "weight": 2,
            },
        ).add_to(map_object)

        polygon_counts = (
            faults.groupby(
                "poligono",
                as_index=False,
            )["num_faltas"]
            .sum()
            .rename(
                columns={"num_faltas": "faltas"}
            )
        )

        polygon_counts["poligono_clave"] = (
            polygon_counts["poligono"]
            .astype(str)
            .map(normalize_name)
        )

        # Solo genera la capa coroplética cuando existen faltas.
        if not polygon_counts.empty:
            folium.Choropleth(
                geo_data=prepared,
                data=polygon_counts,
                columns=[
                    "poligono_clave",
                    "faltas",
                ],
                key_on=(
                    "feature.properties."
                    "__poligono_normalizado"
                ),
                fill_color="YlOrRd",
                fill_opacity=0.72,
                line_opacity=0.85,
                line_weight=2,
                nan_fill_color="#70C5E8",
                nan_fill_opacity=0.48,
                legend_name="Faltas registradas",
                name="Faltas por polígono",
            ).add_to(map_object)

        if label_key:
            folium.GeoJson(
                prepared,
                name="Información de las zonas",
                style_function=lambda _: {
                    "fillOpacity": 0,
                    "color": "#174A5B",
                    "weight": 2,
                },
                highlight_function=lambda _: {
                    "fillOpacity": 0.25,
                    "color": "#FF8C00",
                    "weight": 4,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=[
                        "sector",
                        "zona",
                        "distancia_min_m",
                        "distancia_max_m",
                    ],
                    aliases=[
                        "Sector:",
                        "Zona:",
                        "Distancia inicial (m):",
                        "Distancia final (m):",
                    ],
                    localize=True,
                    sticky=True,
                ),
            ).add_to(map_object)

        _fit_geojson_bounds(
            map_object,
            prepared,
        )

    else:
        st.warning(
            "No se encontró el archivo GeoJSON de los "
            "polígonos marinos."
        )

    folium.LayerControl(
        collapsed=False,
    ).add_to(map_object)

    st_folium(
        map_object,
        use_container_width=True,
        height=560,
        returned_objects=[],
    )

    counts = data.groupby(
        "poligono",
        as_index=False,
    ).agg(
        supervisiones=(
            "supervision_id",
            "nunique",
        ),
        supervisiones_con_falta=(
            "es_falta",
            "sum",
        ),
        faltas=(
            "num_faltas",
            "sum",
        ),
    )

    counts["porcentaje_con_falta"] = (
        counts["supervisiones_con_falta"]
        / counts["supervisiones"]
        * 100
    ).round(1)

    st.dataframe(
        counts.sort_values(
            "faltas",
            ascending=False,
        ),
        width="stretch",
        hide_index=True,
    )