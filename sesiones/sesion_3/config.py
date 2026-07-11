from pathlib import Path


CURRENT_DIR = Path(__file__).parent
DATA_RAW = CURRENT_DIR / "data_raw"
DATA_PROCESSED = CURRENT_DIR / "data_processed"
FINANZAS_PATH = DATA_RAW / "finanzas_personales.xlsx"
