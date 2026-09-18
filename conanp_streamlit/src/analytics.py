from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


GREEN = "#006B4F"
TEAL = "#0A8F7A"
GOLD = "#D7A62A"
INK = "#16352D"
GRID = "#E1EBE7"


def _style(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0, "xanchor": "left", "font": {"size": 18, "color": INK}},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, system-ui, sans-serif", "color": INK},
        margin={"l": 12, "r": 12, "t": 55, "b": 12},
        hoverlabel={"bgcolor": "white", "font_color": INK},
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def calculate_kpis(supervisions: pd.DataFrame, recorridos: pd.DataFrame | None = None) -> dict[str, float]:
    total_supervisions = len(supervisions)
    if "num_faltas" in supervisions:
        faults = int(supervisions["num_faltas"].sum())
    else:
        faults = int(supervisions.get("es_falta", pd.Series(dtype=bool)).sum())
    if recorridos is None:
        recorrido_count = int(supervisions.get("recorrido_id", pd.Series(dtype=object)).nunique())
        kilometres = float(supervisions.get("km_recorridos", pd.Series(dtype=float)).sum())
    else:
        recorrido_count = int(recorridos["recorrido_id"].nunique())
        kilometres = float(recorridos["km_recorridos"].sum())
    con_falta = int(supervisions.get("es_falta", pd.Series(dtype=bool)).sum())
    return {
        "faltas": faults,
        "recorridos": recorrido_count,
        "porcentaje_con_falta": (con_falta / total_supervisions * 100) if total_supervisions else 0.0,
        "kilometros": kilometres,
    }


def build_monthly_trend(
    supervisions: pd.DataFrame,
    recorridos: pd.DataFrame,
    start_date,
    end_date,
):
    """Genera una evolución diaria, mensual o anual según el periodo."""

    data = supervisions.copy()

    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()

    data["fecha"] = pd.to_datetime(
        data["fecha"],
        errors="coerce",
    )

    data["num_faltas"] = pd.to_numeric(
        data["num_faltas"],
        errors="coerce",
    ).fillna(0)

    data = data.dropna(
        subset=["fecha"]
    )

    number_of_months = (
        (end.year - start.year) * 12
        + end.month
        - start.month
        + 1
    )

    same_month = (
        start.year == end.year
        and start.month == end.month
    )

    # Un solo mes: agrupación por día.
    if same_month:
        chart_title = "Evolución diaria"
        x_axis_title = "Día"

        period_index = pd.date_range(
            start=start,
            end=end,
            freq="D",
            name="periodo",
        )

        data["periodo"] = (
            data["fecha"].dt.normalize()
        )

        labels = period_index.strftime(
            "%d/%m"
        ).tolist()

    # Entre 2 y 24 meses: agrupación mensual.
    elif number_of_months <= 24:
        frequency = "M"
        chart_title = "Evolución mensual"
        x_axis_title = "Mes"

        period_index = pd.period_range(
            start=start,
            end=end,
            freq="M",
            name="periodo",
        )

        data["periodo"] = (
            data["fecha"].dt.to_period("M")
        )

        month_names = [
            "Ene",
            "Feb",
            "Mar",
            "Abr",
            "May",
            "Jun",
            "Jul",
            "Ago",
            "Sep",
            "Oct",
            "Nov",
            "Dic",
        ]

        labels = [
            f"{month_names[period.month - 1]} "
            f"{period.year}"
            for period in period_index
        ]

    # Más de 24 meses: agrupación anual.
    else:
        frequency = "Y"
        chart_title = "Evolución anual"
        x_axis_title = "Año"

        period_index = pd.period_range(
            start=start,
            end=end,
            freq="Y",
            name="periodo",
        )

        data["periodo"] = (
            data["fecha"].dt.to_period("Y")
        )

        labels = [
            str(period.year)
            for period in period_index
        ]

    if data.empty:
        summary = pd.DataFrame(
            {
                "supervisiones": 0,
                "incidencias": 0,
            },
            index=period_index,
        )

    else:
        summary = (
            data.groupby("periodo")
            .agg(
                supervisiones=(
                    "supervision_id",
                    "nunique",
                ),
                incidencias=(
                    "num_faltas",
                    "sum",
                ),
            )
            .reindex(
                period_index,
                fill_value=0,
            )
        )

    summary = summary.reset_index()
    summary["etiqueta"] = labels

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=summary["etiqueta"],
            y=summary["supervisiones"],
            mode="lines+markers",
            name="Supervisiones",
            line={
                "color": "#00866A",
                "width": 3,
            },
            marker={
                "size": 8,
            },
            hovertemplate=(
                f"{x_axis_title}: %{{x}}<br>"
                "Supervisiones: %{y}"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=summary["etiqueta"],
            y=summary["incidencias"],
            mode="lines+markers",
            name="Incidencias",
            line={
                "color": "#D9A321",
                "width": 3,
            },
            marker={
                "size": 8,
            },
            hovertemplate=(
                f"{x_axis_title}: %{{x}}<br>"
                "Incidencias: %{y}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title=chart_title,
        hovermode="x unified",
        xaxis={
            "title": x_axis_title,
            "type": "category",
            "categoryorder": "array",
            "categoryarray": labels,
            "tickangle": -45,
        },
        yaxis={
            "title": "Registros",
            "rangemode": "tozero",
            "tickformat": ",d",
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        margin={
            "l": 40,
            "r": 20,
            "t": 70,
            "b": 70,
        },
    )

    return figure


def build_fault_type_chart(data: pd.DataFrame) -> go.Figure:
    if data.empty:
        counts = pd.DataFrame({"tipo_falta": [], "faltas": []})
    else:
        counts = data.groupby("tipo_falta", as_index=False)["cantidad"].sum().nlargest(8, "cantidad").sort_values("cantidad").rename(columns={"cantidad": "faltas"})
    fig = px.bar(counts, x="faltas", y="tipo_falta", orientation="h", color_discrete_sequence=[GREEN])
    fig.update_traces(hovertemplate="%{y}<br>%{x} faltas<extra></extra>")
    fig.update_xaxes(title="Faltas")
    fig.update_yaxes(title=None)
    return _style(fig, "Faltas por categoría")


def build_day_hour_heatmap(data: pd.DataFrame) -> go.Figure:
    order = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    faults = data.loc[data["es_falta"]]
    matrix = faults.pivot_table(index="dia_semana", columns="hora_num", values="num_faltas", aggfunc="sum", fill_value=0)
    matrix = matrix.reindex(index=order, columns=range(24), fill_value=0)
    fig = go.Figure(go.Heatmap(
        z=matrix.values, x=[f"{hour:02d}:00" for hour in matrix.columns], y=matrix.index,
        colorscale=[[0, "#EDF5F1"], [0.55, TEAL], [1, GREEN]],
        colorbar={"title": "Faltas"}, hovertemplate="%{y}, %{x}<br>%{z} faltas<extra></extra>",
    ))
    fig.update_xaxes(title="Hora", dtick=2)
    fig.update_yaxes(title=None)
    return _style(fig, "Concentración por día y hora")


def build_measure_chart(data: pd.DataFrame) -> go.Figure:
    measures = data.loc[data["es_falta"], "medida_tomada"].fillna("Sin registro").value_counts().head(6).rename_axis("medida").reset_index(name="registros")
    fig = px.pie(measures, values="registros", names="medida", hole=0.62, color_discrete_sequence=[GREEN, TEAL, GOLD, "#5BAA93", "#9BC5B7", "#B6A05B"])
    fig.update_traces(textposition="inside", textinfo="percent", hovertemplate="%{label}<br>%{value} (%{percent})<extra></extra>")
    fig.update_layout(showlegend=True, legend={"orientation": "h", "y": -0.08})
    return _style(fig, "Medidas tomadas")
