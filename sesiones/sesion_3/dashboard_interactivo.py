"""
================================================================================
 DASHBOARD INTERACTIVO DE GASTOS
================================================================================
Este archivo es la mitad "interactiva" del proyecto: los filtros que el
usuario puede mover (categoría, mes, monto, orden...) y los gráficos que
reaccionan a esos filtros.

La otra mitad, con las preguntas de negocio fijas (rankings, estadística
descriptiva, comparación contra presupuesto), vive en un archivo aparte
-> ver analisis_gastos.py.

El script está dividido en bloques, separados visualmente con st.divider(),
de lo más simple a lo más avanzado:

  0. Configuración de la página
  1. Texto y títulos
  2. Carga de datos
  3. Dashboard interactivo (filtros + gráficos + descarga de CSV)

Cómo correrlo:
    streamlit run sesiones/sesion_3/dashboard.py

Streamlit no es un script normal: cada vez que alguien interactúa con un
widget, Streamlit vuelve a ejecutar TODO el archivo de arriba hacia abajo.
Por eso el orden del código = el orden en que aparece en pantalla, y por eso
usamos @st.cache_data para no releer los CSV en cada interacción.

NOTA SOBRE POLARS: evitamos la indexación con corchetes (`df["Columna"]`).
En su lugar usamos siempre `.select(pl.col("Columna"))`, que es más
explícito y es la forma recomendada de trabajar con polars.
================================================================================
"""

import polars as pl
import streamlit as st
from config import DATA_PROCESSED

# ==============================================================================
# PASO 0: CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------------------------------
# Método: st.set_page_config()
# ==============================================================================
# DEBE ser el primer comando de Streamlit que se ejecuta en el script (antes
# de cualquier otro st.algo()). Configura el título de la pestaña del
# navegador, el ícono, y si el layout usa todo el ancho ("wide") o queda
# centrado ("centered").
st.set_page_config(
    page_title="Dashboard Interactivo de Gastos",
    page_icon="🎛️",
    layout="wide",
)

# A cambiarlo:
# st.set_page_config(
#     page_title="Dashboard Interactivo de Gastos",
#     page_icon="🎛️",
#     layout="wide",
# )

# ==============================================================================
# PASO 1: TEXTO Y TÍTULOS
# ------------------------------------------------------------------------------
# Métodos: st.title() / st.header() / st.subheader() / st.markdown()
# ==============================================================================
# Streamlit tiene varios niveles de texto, del más grande al más chico:
#   st.title()     -> título principal de la página (como un <h1>)
#   st.header()    -> encabezado de sección (como un <h2>)
#   st.subheader()  -> subtítulo (como un <h3>)
#   st.markdown()   -> texto libre en formato Markdown (admite **negrita**,
#                      *cursiva*, listas, etc.)
st.title("🎛️ Dashboard Interactivo de Gastos")
st.subheader("Mueve los filtros de la izquierda y todo lo demás se actualiza solo.")
st.markdown("Este dashboard fue construido con **Streamlit + Polars.**")

# st.title("")
# st.header("")
# st.subheader("")
# st.markdown("")


# ==============================================================================
# PASO 2: CARGA DE DATOS (con caché)
# ------------------------------------------------------------------------------
# Métodos: @st.cache_data / pl.read_csv()
# ==============================================================================
# @st.cache_data le dice a Streamlit: "guarda el resultado de esta función en
# memoria en lugar de volverla a ejecutar en cada interacción.
# Es clave para no releer los CSV cada vez que haya cambios en la página.
@st.cache_data
def cargar_datos():
    gastos = pl.read_csv(DATA_PROCESSED / "gastos.csv", try_parse_dates=True)
    presupuesto = pl.read_csv(DATA_PROCESSED / "presupuesto.csv")
    return gastos, presupuesto


GASTOS, PRESUPUESTO = cargar_datos()


st.divider()


# ==============================================================================
# PASO 3: DASHBOARD INTERACTIVO
# ==============================================================================
# A diferencia de analisis_gastos.py (donde las preguntas están fijas, por
# ejemplo "¿gasté más en Comida o en Casa?"), acá el usuario elige QUÉ mes,
# QUÉ categorías y QUÉ rango de monto quiere ver, con widgets en la barra
# lateral. Todo lo que sigue (KPIs, gráficos, tabla) se recalcula solo
# cada vez que cambia un filtro.
st.header("Filtros y resultados")

# ==============================================================================
# ARMAR EL SIDEBAR
# ==============================================================================
# ---- Widgets simples de una sola opción -------------------------------------
# Métodos: st.checkbox() / st.radio()
with st.sidebar:
    st.header("🔍 Filtros")

    # st.checkbox(): la opción más simple de todas. Devuelve True o False.
    solo_amor = st.checkbox("Mostrar solo gastos 'Amor' 💕", value=False)

    # st.radio(): elegir UNA sola opción entre pocas, mostradas todas a la vez.
    orden = st.radio(
        "Ordenar tabla por",
        options=["Fecha", "Monto"],
        horizontal=True,
    )

    # ---- Widgets de selección múltiple, armados a partir de los datos ------
    # Métodos: pl.col() / .select() / .unique() / .sort() / .to_series() /
    #          .to_list() / st.multiselect()
    categorias_disponibles = (
        GASTOS.select(pl.col("Categoría"))
        .unique()
        .sort("Categoría")
        .to_series()
        .to_list()
    )

    # st.multiselect(): elegir VARIAS opciones de una lista.
    # `default=categorias_disponibles` hace que arranque con TODAS
    # seleccionadas. Sin `default`, arranca vacío -> el filtro no muestra
    # nada hasta que el usuario elija algo a mano.
    categorias_seleccionadas = st.multiselect(
        "Categorías",
        options=categorias_disponibles,
        default=categorias_disponibles,
    )

    # Acá es donde se filtra por mes. Preguntas como "¿en qué categoría
    # gasté más ESTE mes?" se responden solas con este filtro, sin
    # necesidad de una pregunta de negocio fija aparte.
    meses_disponibles = (
        GASTOS.select(pl.col("Mes")).unique().sort("Mes").to_series().to_list()
    )
    meses_seleccionados = st.multiselect(
        "Mes",
        options=meses_disponibles,
        default=meses_disponibles,
    )

    # ---- Widgets numéricos ---------------------------------------------------
    # Métodos: pl.col().min() / .max() / .item() / st.slider()
    #
    # st.slider() SÍ sirve para números, porque interpola entre un mínimo y
    # un máximo. Para texto o categorías la herramienta correcta es
    # st.multiselect (como arriba), no un slider.
    monto_minimo = GASTOS.select(pl.col("Monto").min()).item()
    monto_maximo = GASTOS.select(pl.col("Monto").max()).item()

    rango_monto = st.slider(
        "Rango de monto (S/)",
        min_value=float(monto_minimo),
        max_value=float(monto_maximo),
        value=(float(monto_minimo), float(monto_maximo)),
    )

# ---- Aplicar los filtros con polars -----------------------------------------
# Métodos: .filter() / pl.col().is_in() / pl.col().is_between() / .sort()
gastos_filtrados = GASTOS.filter(
    pl.col("Categoría").is_in(categorias_seleccionadas)
    & pl.col("Mes").is_in(meses_seleccionados)
    & pl.col("Monto").is_between(rango_monto[0], rango_monto[1])
)

if solo_amor:
    gastos_filtrados = gastos_filtrados.filter(pl.col("Amor") == 1)

gastos_filtrados = gastos_filtrados.sort(orden)

# ---- Layout en columnas y métricas (KPIs) -----------------------------------
# Métodos: st.columns() / st.metric() / pl.col().sum() / .item() / .height
col1, col2 = st.columns(2)

total_gastado = gastos_filtrados.select(pl.col("Monto").sum()).item() or 0.0
total_presupuesto = PRESUPUESTO.select(pl.col("Presupuesto").sum()).item() or 0.0
diferencia = total_presupuesto - total_gastado
n_transacciones = gastos_filtrados.height  # .height es un atributo, no un método

with col1:
    st.metric("Total gastado", f"S/ {total_gastado:,.2f}")
with col2:
    st.metric("N° de transacciones", n_transacciones)

# ---- Gráfico de barras: gasto por categoría (según filtros) ----------------
# Métodos: .group_by() / .agg() / .sort() / st.bar_chart()
st.subheader("Gasto por categoría (según filtros)")

gasto_por_categoria_filtrado = (
    gastos_filtrados.group_by("Categoría")
    .agg(pl.col("Monto").sum().alias("Monto"))
    .sort("Monto", descending=True)
)
st.bar_chart(gasto_por_categoria_filtrado, x="Categoría", y="Monto")

# ---- Tabla detallada ---------------------------------------------------------
# Métodos: st.dataframe() con column_config
st.subheader("Transacciones filtradas")

st.dataframe(
    gastos_filtrados,
    width="stretch",
    column_config={
        "Monto": st.column_config.NumberColumn("Monto", format="S/ %.2f"),
        "Amor": st.column_config.CheckboxColumn("¿Amor?"),
    },
    hide_index=True,
)

# ---- Evolución mensual (gráfico de líneas) -----------------------------------
# Métodos: .group_by() / .agg() / .sort() / st.line_chart()
col1, col2 = st.columns(2)
col1.subheader("Evolución mensual")

gasto_por_mes_filtrado = (
    gastos_filtrados.group_by("Mes")
    .agg(pl.col("Monto").sum().alias("Monto"))
    .sort("Mes")
)
col1.line_chart(gasto_por_mes_filtrado, x="Mes", y="Monto")


col2.subheader("Evolución mensual por categoría")

evolucion_categoria = (
    gastos_filtrados
    .group_by(["Mes", "Categoría"])
    .agg(pl.col("Monto").sum().alias("Monto"))
    .sort(["Mes", "Categoría"])
    .pivot(
        values="Monto",
        index="Mes",
        on="Categoría",
        aggregate_function="sum",
    )
    .sort("Mes")
    .fill_null(0)
)

col2.line_chart(evolucion_categoria, x="Mes", height=400)

# ---- Descargar CSV filtrado ---------------------------------------------------
# Métodos: .write_csv() / st.download_button()
#
# .write_csv() genera el CSV como texto; lo codificamos a bytes porque
# st.download_button() los necesita en ese formato.
csv_bytes = gastos_filtrados.write_csv().encode("utf-8")
st.download_button(
    "⬇️ Descargar CSV filtrado",
    data=csv_bytes,
    file_name="gastos_filtrados.csv",
    mime="text/csv",
)

