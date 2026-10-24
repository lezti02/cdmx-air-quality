"""Project-wide constants and paths."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

# Pollutant files published by SEDEMA, one .xls per pollutant and year.
POLLUTANT_FILES = ["CO", "NO", "NO2", "NOX", "O3", "PM10", "PM25", "PMCO", "SO2"]

# PMCO (coarse fraction) is PM10 - PM2.5, so it adds no new information.
POLLUTANTS = ["CO", "NO", "NO2", "NOX", "O3", "PM10", "PM25", "SO2"]

# NOX is NO + NO2, so it is excluded from the modelling features.
MODEL_FEATURES = ["CO", "NO", "NO2", "O3", "SO2", "PM10", "PM25"]

# SEDEMA encodes missing readings with these sentinel values.
MISSING_CODES = [-99, -999]

# The only stations that measure every pollutant with an acceptable
# share of missing data (see the missing-data heatmap in notebook 01).
SELECTED_STATIONS = ["AJM", "CAM", "MER", "NEZ", "PED", "TLA", "UIZ"]

STATION_NAMES = {
    "AJM": "Ajusco Medio",
    "CAM": "Camarones",
    "MER": "Merced",
    "NEZ": "Nezahualcóyotl",
    "PED": "Pedregal",
    "TLA": "Tlalnepantla",
    "UIZ": "UAM Iztapalapa",
}

UNITS = {
    "CO": "ppm",
    "NO": "ppb",
    "NO2": "ppb",
    "NOX": "ppb",
    "O3": "ppb",
    "SO2": "ppb",
    "PM10": "µg/m³",
    "PM25": "µg/m³",
}

RANDOM_STATE = 42
