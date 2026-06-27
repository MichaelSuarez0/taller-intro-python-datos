import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Plotly Express Demo",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Plotly Express — Demo Interactiva")
st.markdown("Explora los tipos de gráficos más usados con datos de ejemplo.")

# ── Sidebar: seleccionar gráfico ─────────────────────────────────────────────
chart_type = st.sidebar.selectbox(
    "Tipo de gráfico",
    [
        "Scatter (dispersión)",
        "Line (líneas)",
        "Bar (barras)",
        "Histogram (histograma)",
        "Box (caja)",
        "Pie (pastel)",
        "Heatmap (mapa de calor)",
        "Sunburst",
        "3D Scatter",
    ],
)

# ── Datos ────────────────────────────────────────────────────────────────────
np.random.seed(42)
df_gapminder = px.data.gapminder().query("year == 2007")
df_iris = px.data.iris()
df_tips = px.data.tips()

# ── Gráficos ─────────────────────────────────────────────────────────────────

if chart_type == "Scatter (dispersión)":
    st.subheader("Scatter — GDP per cápita vs Esperanza de vida (2007)")
    st.markdown("Cada punto es un país. El tamaño = población, el color = continente.")

    fig = px.scatter(
        df_gapminder,
        x="gdpPercap",
        y="lifeExp",
        size="pop",
        color="continent",
        hover_name="country",
        log_x=True,
        size_max=60,
        labels={"gdpPercap": "GDP per cápita (log)", "lifeExp": "Esperanza de vida"},
        title="Gapminder 2007",
    )
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Line (líneas)":
    st.subheader("Line — Evolución de la esperanza de vida")
    continent = st.multiselect(
        "Continentes",
        options=px.data.gapminder()["continent"].unique(),
        default=["Americas", "Europe"],
    )
    df_line = px.data.gapminder().query("continent in @continent")
    fig = px.line(
        df_line,
        x="year",
        y="lifeExp",
        color="country",
        line_group="country",
        hover_name="country",
        labels={"lifeExp": "Esperanza de vida", "year": "Año"},
        title="Esperanza de vida por país",
    )
    fig.update_traces(opacity=0.7)
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Bar (barras)":
    st.subheader("Bar — PIB promedio por continente (2007)")
    df_bar = (
        df_gapminder.groupby("continent", as_index=False)["gdpPercap"]
        .mean()
        .sort_values("gdpPercap", ascending=False)
    )
    fig = px.bar(
        df_bar,
        x="continent",
        y="gdpPercap",
        color="continent",
        text_auto=".2s",
        labels={"gdpPercap": "GDP per cápita promedio", "continent": "Continente"},
        title="GDP promedio por continente",
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Histogram (histograma)":
    st.subheader("Histogram — Distribución de propinas")
    nbins = st.slider("Número de bins", 5, 50, 20)
    fig = px.histogram(
        df_tips,
        x="tip",
        nbins=nbins,
        color="sex",
        marginal="rug",  # pequeño rug plot arriba
        hover_data=df_tips.columns,
        labels={"tip": "Propina ($)", "sex": "Género"},
        title="Distribución de propinas",
    )
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Box (caja)":
    st.subheader("Box — Propina por día y género")
    fig = px.box(
        df_tips,
        x="day",
        y="tip",
        color="sex",
        notched=True,
        points="outliers",
        labels={"tip": "Propina ($)", "day": "Día", "sex": "Género"},
        title="Distribución de propinas por día",
    )
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Pie (pastel)":
    st.subheader("Pie — Proporción de esperanza de vida por continente")
    df_pie = df_gapminder.groupby("continent", as_index=False)["pop"].sum()
    fig = px.pie(
        df_pie,
        names="continent",
        values="pop",
        hole=0.4,  # donut chart
        title="Población mundial por continente (2007)",
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Heatmap (mapa de calor)":
    st.subheader("Heatmap — Correlación en el dataset Iris")
    corr = df_iris.drop(columns="species").corr().round(2)
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Matriz de correlación — Iris",
    )
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "Sunburst":
    st.subheader("Sunburst — Propinas por día y hora")
    df_sun = df_tips.groupby(["day", "time", "sex"], as_index=False)["tip"].sum()
    fig = px.sunburst(
        df_sun,
        path=["day", "time", "sex"],
        values="tip",
        title="Propinas: día → turno → género",
    )
    st.plotly_chart(fig, use_container_width=True)

elif chart_type == "3D Scatter":
    st.subheader("3D Scatter — Dataset Iris")
    fig = px.scatter_3d(
        df_iris,
        x="sepal_length",
        y="sepal_width",
        z="petal_length",
        color="species",
        symbol="species",
        opacity=0.8,
        labels={
            "sepal_length": "Largo sépalo",
            "sepal_width": "Ancho sépalo",
            "petal_length": "Largo pétalo",
        },
        title="Iris en 3D",
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption("Datos: Gapminder, Iris y Tips — integrados en `plotly.express.data`")
