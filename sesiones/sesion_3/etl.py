from pathlib import Path
import polars as pl
from medir_tiempo import medir_tiempo

CURRENT_DIR = Path(__file__).parent
DATA_RAW = CURRENT_DIR / "data_raw"
DATA_PROCESSED = CURRENT_DIR / "data_processed"
FINANZAS_PATH = DATA_RAW / "finanzas_personales.xlsx"


def leer_finanzas():
    # Usar pl.read_excel para generar las siguientes variables
    df_gastos = pl.read_excel(FINANZAS_PATH, sheet_name="Gastos")
    df_presupuesto = pl.read_excel(FINANZAS_PATH, sheet_name="Presupuesto")
    return df_gastos, df_presupuesto


def procesar_gastos(gastos: pl.DataFrame):
    # drop: Queremos ahora borrar la columna "descripción"
    gastos = gastos.drop("Descripción")

    # rename: Queremos renombrar "Unammed: 4" a "Amor"
    gastos = gastos.rename({"__UNNAMED__4": "Amor"})

    # replace: Queremos reemplazar "Amor" por una variable dummy:
    # 1 si es por amor, 0 si no lo es
    # Modificamos los valores de la columna "Amor" utilizando `replace()` dentro de `with_columns()`.
    gastos = gastos.with_columns(pl.col("Amor").replace({"Amor": 1}))

    # fill_null: Ahora a reemplazar NaN por 0
    gastos = gastos.with_columns(pl.col("Amor").cast(pl.Int8).fill_null(0))

    # select: para consultar una parte del dataframe
    gastos = gastos.with_columns(
        pl.col("Categoría").replace({"Transport": "Transporte"})
    )
    # Vamos a crear una columna "mes" para que sea más sencillo manipular
    gastos = gastos.with_columns(
        pl.col("Fecha").dt.month().alias("Mes")
    )

    return gastos


def guardar_gastos_presupuesto(gastos: pl.DataFrame, presupuesto: pl.DataFrame) -> None:
    # Guardamos
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    gastos.write_csv(DATA_PROCESSED / "gastos.csv")
    presupuesto.write_csv(DATA_PROCESSED / "presupuesto.csv")


@medir_tiempo
def main() -> None:
    gastos, presupuesto = leer_finanzas()
    gastos = procesar_gastos(gastos)
    guardar_gastos_presupuesto(gastos, presupuesto)


if __name__ == "__main__":
    main()
