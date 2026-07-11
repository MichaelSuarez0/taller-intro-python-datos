"""
================================================================================
 DASHBOARD DE GASTOS — TODO EN UNA SOLA PÁGINA
================================================================================
El script está dividido en grandes bloques, separados visualmente con
st.divider(), de lo más simple a lo más avanzado:

  0. Configuración de la página
  1. Texto y títulos
  2. Carga de datos
  3. Estadística descriptiva (KPI cards: media, moda, desviación)
  4. Preguntas de negocio (rankings, join contra presupuesto)
  5. Dashboard interactivo (filtros + gráficos + descarga de CSV)

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
    page_title="Dashboard de Gastos",
    page_icon="💸",
    layout="wide",
)

# A cambiarlo:
# st.set_page_config(
#     page_title="Dashboard de Gastos",
#     page_icon="💸",
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
st.title("💸 Dashboard de Gastos")
st.subheader("Explora tus gastos por categoría y mes, y compara contra tu presupuesto.")
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
# PASO 3: ESTADÍSTICA DESCRIPTIVA (KPI cards: media, moda, desviación)
# ------------------------------------------------------------------------------
# Métodos (polars): pl.col().mean() / .mode() / .std()
# Métodos (streamlit): st.columns() / st.metric()
# ==============================================================================
# .mean()  -> promedio
# .mode()  -> el valor que más se repite (puede haber empates, por eso
#             usamos .first() para quedarnos con uno solo)
# .std()   -> desviación estándar: qué tan dispersos están los montos
#             respecto al promedio
st.header("📐 Estadística descriptiva")

col1, col2, col3 = st.columns(3)

promedio_gasto = GASTOS.select(pl.col("Monto").mean()).item()
moda_categoria = GASTOS.select(pl.col("Categoría").mode().first()).item()
desviacion_gasto = GASTOS.select(pl.col("Monto").std()).item()

with col1:
    st.metric("Gasto promedio por transferencia", f"S/ {promedio_gasto:,.2f}")
with col2:
    st.metric("Categoría más frecuente", moda_categoria)
with col3:
    st.metric("Desviación estándar", f"S/ +/-{desviacion_gasto:,.2f}")

st.divider()


# ==============================================================================
# PASO 4: PREGUNTAS DE NEGOCIO
# ==============================================================================
# Nota: las preguntas que dependen de UN MES en particular (por ejemplo,
# "¿en qué categoría gasté más ESTE mes?") no van acá. Esas se responden
# con los filtros del Dashboard interactivo del paso 5 (filtrando por mes).
st.header("❓ Preguntas de negocio")

# ---- 1. ¿En qué categoría gasté más dinero? (ranking) ----------------------
# Métodos: .group_by() / .agg() / .sort() / st.dataframe() / st.bar_chart()

st.subheader("1. ¿En qué categoría gasté más dinero?")

monto_por_categoria = (
    GASTOS.group_by("Categoría")
    .agg(pl.col("Monto").sum().alias("Monto"))
    .sort("Monto", descending=True)
)

col_izq, col_der = st.columns(2)
with col_izq:
    st.dataframe(monto_por_categoria, width="stretch")
with col_der:
    st.bar_chart(monto_por_categoria, x="Categoría", y="Monto")

st.divider()

# ---- 2. ¿En qué mes gasté más dinero? (ranking) ----------------------------
# Métodos: .group_by() / .agg() / .sort()
#
# Igual que la pregunta 1, pero agrupando por "Mes" en vez de "Categoría".
st.subheader("2. ¿En qué mes gasté más dinero?")

monto_por_mes = (
    GASTOS.group_by("Mes")
    .agg(pl.col("Monto").sum().alias("Monto"))
    .sort("Monto", descending=True)
)

col_izq, col_der = st.columns(2)
with col_izq:
    st.dataframe(monto_por_mes, width="stretch")
with col_der:
    st.bar_chart(monto_por_mes, x="Mes", y="Monto")

st.divider()

# ---- 3. ¿Qué % de mis gastos son "por amor" vs normales? -------------------
# Métodos: .group_by() / .agg() / .with_columns() / .iter_rows()
#
# Primero sumamos el Monto agrupado por "Amor" (0 o 1). Después dividimos
# cada grupo entre el total general y multiplicamos por 100 para tener un
# porcentaje. .with_columns() agrega esa nueva columna calculada al DataFrame.
st.subheader("3. ¿Qué porcentaje de mis gastos son 'por amor'? 💕")

monto_por_amor = GASTOS.group_by("Amor").agg(pl.col("Monto").sum().alias("Monto"))
total_general = monto_por_amor.select(pl.col("Monto").sum()).item()

monto_por_amor = monto_por_amor.with_columns(
    (pl.col("Monto") / total_general * 100).alias("Porcentaje")
)

col_normal, col_amor = st.columns(2)
for fila in monto_por_amor.iter_rows(named=True):
    columna = col_amor if fila["Amor"] == 1 else col_normal
    etiqueta = "Por amor 💕" if fila["Amor"] == 1 else "Gasto normal"
    with columna:
        st.metric(etiqueta, f"{fila['Porcentaje']:.1f}%", f"S/ {fila['Monto']:,.2f}")

st.divider()

# ---- 4. ¿Me paso del presupuesto en alguna categoría? ----------------------
# Métodos: .filter() / .group_by() / .agg() / join()
# Métodos (streamlit): st.selectbox() / st.columns() / st.column_config.ProgressColumn()
#
# Como el presupuesto es MENSUAL, tiene sentido comparar el gasto de UN MES
# específico contra el presupuesto mensual de cada categoría.

st.subheader("4. ¿Me paso del presupuesto en alguna categoría?")

# La fila "Total" del presupuesto no representa una categoría real,
# por lo que la eliminamos antes de hacer la comparación.
presupuesto_categorias = PRESUPUESTO.filter(pl.col("Categoría") != "Total")

# ---- Selector de mes -------------------------------------------------------
# Usamos un selectbox para elegir el mes a analizar.
# Lo colocamos dentro de una columna angosta para que el widget no ocupe
# todo el ancho de la página.
meses_disponibles = (
    GASTOS.select(pl.col("Mes")).unique().sort("Mes").to_series().to_list()
)

col_mes, _ = st.columns([1, 8])

with col_mes:
    mes_seleccionado = st.selectbox(
        "Mes",
        options=meses_disponibles,
    )

st.caption(f"Comparación del presupuesto para el mes {mes_seleccionado}")

# ---- Filtrar el mes seleccionado -------------------------------------------
gastos_mes = GASTOS.filter(pl.col("Mes") == mes_seleccionado)

# ---- Calcular gasto por categoría ------------------------------------------
gasto_por_categoria = gastos_mes.group_by("Categoría").agg(
    pl.col("Monto").sum().alias("Gastado")
)

# ---- Comparar contra el presupuesto ----------------------------------------
# Además calculamos:
# - Porcentaje del presupuesto utilizado.
# - Un indicador visual (🟢 o 🔴) dependiendo de si se excedió.
comparacion = (
    presupuesto_categorias.join(
        gasto_por_categoria,
        on="Categoría",
        how="left",
    )
    .fill_null(0)
    .with_columns((pl.col("Gastado") / pl.col("Presupuesto") * 100).alias("Porcentaje"))
    .with_columns(
        pl.when(pl.col("Porcentaje") <= 99)
        .then(pl.lit("🟢"))
        .otherwise(pl.lit("🔴"))
        .alias("Estado")
    )
)

# ---- Mostrar resultados ----------------------------------------------------
# ProgressColumn dibuja automáticamente una barra horizontal para visualizar
# qué porcentaje del presupuesto se ha utilizado.
# Como Streamlit no permite cambiar el color de la barra, agregamos una
# columna "Estado" con un semáforo:
#   🟢 = dentro del presupuesto
#   🔴 = presupuesto excedido
st.dataframe(
    comparacion.select(
        [
            "Categoría",
            "Gastado",
            "Presupuesto",
            "Estado",
            "Porcentaje",
        ]
    ),
    column_config={
        "Gastado": st.column_config.NumberColumn(
            format="S/ %.2f",
        ),
        "Presupuesto": st.column_config.NumberColumn(
            format="S/ %.2f",
        ),
        "Estado": st.column_config.TextColumn(
            "Estado",
            width="small",
        ),
        "Porcentaje": st.column_config.ProgressColumn(
            "% usado",
            format="%.0f%%",
            min_value=0,
            max_value=100,
        ),
    },
    hide_index=True,
    width="stretch",
)
