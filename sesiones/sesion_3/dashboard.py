"""
================================================================================
 TUTORIAL + DASHBOARD: STREAMLIT PASO A PASO
================================================================================

Este script cumple dos objetivos:

  1. Enseñar, en orden, los componentes principales de Streamlit (con
     comentarios explicando qué hace cada uno y por qué se usa).
  2. Usar esos componentes para armar un dashboard real con tus datos
     de GASTOS y PRESUPUESTO (leídos con polars).

Cómo correrlo:
    streamlit run dashboard_gastos.py

Streamlit no es un script normal: cada vez que el usuario interactúa con un
widget (un selectbox, un slider, etc.), Streamlit vuelve a ejecutar TODO el
archivo de arriba hacia abajo. Por eso:
  - El orden del código = el orden en que aparece en pantalla.
  - Hay que evitar cálculos pesados repetidos -> para eso existe @st.cache_data.
================================================================================
"""

import streamlit as st
import polars as pl
from pathlib import Path
from config import DATA_PROCESSED

# from config import DATA_PROCESSED  # <- descomenta esto en tu proyecto real


# ==============================================================================
# PASO 0: CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
# st.set_page_config() DEBE ser el primer comando de Streamlit que se ejecuta
# en el script (antes de cualquier st.algo()). Configura el título de la
# pestaña del navegador, el ícono, y si el layout usa todo el ancho de la
# pantalla ("wide") o queda centrado ("centered").
st.set_page_config(
    page_title="Dashboard de Gastos",
    page_icon="💸",
    layout="wide",
)

# ==============================================================================
# PASO 1: TEXTO Y TÍTULOS
# ==============================================================================
# Streamlit tiene varios niveles de texto:
#   st.title()    -> el título principal de la página (H1)
#   st.header()   -> encabezado de sección (H2)
#   st.subheader()-> subtítulo (H3)
#   st.markdown() -> texto libre en formato Markdown (soporta **negrita**, etc.)
#   st.write()    -> el "todoterreno": detecta el tipo de dato y lo muestra
#                    bien (texto, número, DataFrame, gráfico...). Ideal para
#                    prototipar rápido.
st.title("💸 Dashboard de Gastos")
st.markdown(
    "Explorá tus gastos por **categoría**, **mes** y compará contra tu "
    "**presupuesto**. Este dashboard fue construido con Streamlit + Polars."
)


# ==============================================================================
# PASO 2: CARGA DE DATOS (con caché)
# ==============================================================================
# @st.cache_data le dice a Streamlit: "esta función es cara/lenta, no la
# vuelvas a ejecutar en cada interacción, guarda el resultado en memoria y
# reusalo mientras los ARGUMENTOS no cambien". Es clave para no releer los
# CSV cada vez que el usuario mueve un slider.


@st.cache_data
def cargar_datos():
    gastos = pl.read_csv(DATA_PROCESSED / "gastos.csv", try_parse_dates=True)
    presupuesto = pl.read_csv(DATA_PROCESSED / "presupuesto.csv")
    return gastos, presupuesto


# Si los archivos no existen (por ejemplo, al probar este script suelto),
# generamos datos de ejemplo para que el dashboard siempre pueda mostrarse.
GASTOS, PRESUPUESTO = cargar_datos()

# ==============================================================================
# PASO 3: LA BARRA LATERAL (SIDEBAR) Y LOS WIDGETS DE FILTRO
# ==============================================================================
# `with st.sidebar:` mete todo lo que está indentado adentro en la barra
# lateral izquierda, en vez del cuerpo principal. Es el lugar clásico para
# poner filtros que no queremos que ocupen espacio central.
#
# Cada widget de Streamlit devuelve el valor actual seleccionado por el
# usuario. Guardarlo en una variable es lo que nos permite filtrar los datos.
with st.sidebar:
    st.header("🔍 Filtros")

    # st.select_slider / st.slider: elegir un rango numérico con un control
    # deslizante. Acá lo usamos para elegir un rango de meses.
    meses_disponibles = list(GASTOS.select(pl.col("Mes")).unique().sort(pl.col("Mes")))
    mes_min, mes_max = st.select_slider(
        "Rango de meses",
        options=meses_disponibles,
    )
    mes_min = mes_max = meses_disponibles[0]

    # st.checkbox: un booleano simple (True/False).
    solo_amor = st.checkbox("Mostrar solo gastos 'Amor' 💕", value=False)

    # st.radio: elegir una sola opción entre pocas, mostradas todas a la vez.
    orden = st.radio(
        "Ordenar tabla por",
        options=["Fecha", "Monto"],
        horizontal=True,
    )

    # st.multiselect: elegir varias opciones de una lista.
    categorias_disponibles = sorted(GASTOS["Categoría"].unique().to_list())
    categorias_seleccionadas = st.multiselect(
        "Categorías",
        options=categorias_disponibles,
        default=categorias_disponibles,  # por defecto, todas seleccionadas
    )


# ==============================================================================
# PASO 4: APLICAR LOS FILTROS CON POLARS
# ==============================================================================
# Con los valores que salieron de los widgets, filtramos el DataFrame de
# polars normalmente, usando pl.col(...) como siempre.
gastos_filtrados = GASTOS.filter(
    pl.col("Categoría").is_in(categorias_seleccionadas)
    & pl.col("Mes").is_between(mes_min, mes_max)
)

if solo_amor:
    gastos_filtrados = gastos_filtrados.filter(pl.col("Amor") == 1)

gastos_filtrados = gastos_filtrados.sort(orden)


# ==============================================================================
# PASO 5: MÉTRICAS (KPIs) CON st.columns Y st.metric
# ==============================================================================
# st.columns(n) divide el ancho disponible en n columnas para poner
# elementos uno al lado del otro (en vez de apilados verticalmente).
# st.metric() muestra un número grande con una etiqueta, ideal para KPIs,
# y opcionalmente una flecha de variación (delta) arriba/abajo.
col1, col2, col3 = st.columns(3)

total_gastado = gastos_filtrados["Monto"].sum() or 0.0
total_presupuesto = PRESUPUESTO["Presupuesto"].sum() or 0.0
diferencia = total_presupuesto - total_gastado
n_transacciones = gastos_filtrados.height

with col1:
    st.metric("Total gastado", f"S/ {total_gastado:,.2f}")
with col2:
    st.metric(
        "Vs. presupuesto",
        f"S/ {total_presupuesto:,.2f}",
        delta=f"S/ {diferencia:,.2f} disponible" if diferencia >= 0 else f"S/ {abs(diferencia):,.2f} excedido",
        delta_color="normal" if diferencia >= 0 else "inverse",
    )
with col3:
    st.metric("N° de transacciones", n_transacciones)


# ==============================================================================
# PASO 6: TABS PARA ORGANIZAR CONTENIDO
# ==============================================================================
# st.tabs() crea pestañas dentro de la página. Cada pestaña es un contexto
# `with` donde metemos contenido distinto, sin necesidad de scroll infinito.
tab_resumen, tab_tabla, tab_comparacion = st.tabs(
    ["📊 Resumen", "📋 Tabla detallada", "🎯 Presupuesto vs Real"]
)


# ---- TAB 1: RESUMEN -----------------------------------------------------
with tab_resumen:
    st.subheader("Gasto total por categoría")

    # Agrupamos con polars y pasamos a pandas para los charts nativos de
    # Streamlit, que esperan pandas o dicts/listas simples.
    gasto_por_categoria = (
        gastos_filtrados.group_by("Categoría")
        .agg(pl.col("Monto").sum().alias("Monto"))
        .sort("Monto", descending=True)
        .to_pandas()
        .set_index("Categoría")
    )

    col_izq, col_der = st.columns(2)
    with col_izq:
        # st.bar_chart: gráfico de barras rápido, sin configurar nada.
        st.bar_chart(gasto_por_categoria)
    with col_der:
        # st.dataframe: tabla interactiva (se puede ordenar por columna,
        # buscar, hacer scroll). Distinto de st.table(), que es estática.
        st.dataframe(gasto_por_categoria, width="stretch")

    st.subheader("Evolución mensual")
    gasto_por_mes = (
        gastos_filtrados.group_by("Mes")
        .agg(pl.col("Monto").sum().alias("Monto"))
        .sort("Mes")
        .to_pandas()
        .set_index("Mes")
    )
    # st.line_chart: igual que bar_chart pero como línea, útil para ver
    # tendencias en el tiempo.
    st.line_chart(gasto_por_mes)


# ---- TAB 2: TABLA DETALLADA ----------------------------------------------
with tab_tabla:
    st.subheader("Todas las transacciones filtradas")

    # st.dataframe acepta un objeto `column_config` para personalizar cómo
    # se ve cada columna (formato de moneda, barras de progreso, etc.)
    st.dataframe(
        gastos_filtrados.to_pandas(),
        width="stretch",
        column_config={
            "Monto": st.column_config.NumberColumn("Monto", format="S/ %.2f"),
            "Amor": st.column_config.CheckboxColumn("¿Amor?"),
        },
        hide_index=True,
    )

    # st.download_button: permite exportar lo que se está viendo. Muy común
    # en dashboards reales para que el usuario se lleve los datos filtrados.
    csv_bytes = gastos_filtrados.write_csv().encode("utf-8")
    st.download_button(
        "⬇️ Descargar CSV filtrado",
        data=csv_bytes,
        file_name="gastos_filtrados.csv",
        mime="text/csv",
    )


# ---- TAB 3: PRESUPUESTO VS REAL ------------------------------------------
with tab_comparacion:
    st.subheader("¿Cómo vas respecto a tu presupuesto?")

    comparacion = (
        PRESUPUESTO.join(
            gastos_filtrados.group_by("Categoría").agg(pl.col("Monto").sum().alias("Gastado")),
            on="Categoría",
            how="left",
        )
        .fill_null(0)
        .with_columns(
            (pl.col("Gastado") / pl.col("Presupuesto")).alias("pct")
        )
    )

    # st.progress: barra de progreso simple, útil para ver de un vistazo
    # qué porcentaje del presupuesto de cada categoría ya se gastó.
    for fila in comparacion.iter_rows(named=True):
        pct = min(max(fila["pct"], 0.0), 1.0)  # st.progress necesita 0..1
        st.write(f"**{fila['Categoría']}** — S/ {fila['Gastado']:,.2f} de S/ {fila['Presupuesto']:,.2f}")
        st.progress(pct)
        if fila["pct"] > 1:
            # st.error / st.warning / st.success / st.info: cajas de alerta
            # con color, para resaltar mensajes puntuales.
            st.error(f"⚠️ Te pasaste del presupuesto en {fila['Categoría']}")


# ==============================================================================
# PASO 7: EXPANDER PARA CONTENIDO OPCIONAL
# ==============================================================================
# st.expander crea una sección plegable, ideal para detalles que no todos
# necesitan ver siempre (notas, explicación de la metodología, datos crudos).
with st.expander("ℹ️ ¿Cómo se calculan estas cifras?"):
    st.markdown(
        """
        - **Total gastado**: suma de la columna `Monto` en los gastos filtrados.
        - **Presupuesto**: suma de la columna `Presupuesto`, sin filtrar
          (el presupuesto es fijo, no depende de los filtros de fecha/categoría).
        - **% usado por categoría**: `Gastado / Presupuesto` de esa categoría.
        """
    )


# ==============================================================================
# RESUMEN DE COMPONENTES USADOS (referencia rápida)
# ==============================================================================
# st.set_page_config   -> configurar la pestaña/layout (siempre primero)
# @st.cache_data        -> cachear funciones lentas (ej. leer CSV)
# st.title/header/...   -> jerarquía de texto
# st.markdown           -> texto con formato libre
# st.sidebar            -> barra lateral para filtros
# st.multiselect         -> elegir varias opciones
# st.slider              -> elegir rango numérico
# st.checkbox            -> booleano
# st.radio                -> una opción entre pocas
# st.columns              -> layout en columnas
# st.metric                -> KPI con delta
# st.tabs                  -> pestañas de contenido
# st.bar_chart / line_chart -> gráficos rápidos
# st.dataframe              -> tabla interactiva
# st.download_button         -> exportar datos
# st.progress                 -> barra de avance
# st.error/warning/success/info -> cajas de alerta
# st.expander                    -> contenido plegable
# ==============================================================================