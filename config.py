"""Project-wide configuration for the BB84 simulator."""

DEFAULT_QUBIT_COUNT = 64
MIN_QUBIT_COUNT = 1
MAX_QUBIT_COUNT = 1024

DEFAULT_EVE_ENABLED = False
DEFAULT_INTERCEPT_RATE = 1.0
DEFAULT_RANDOM_SEED = 7
USE_DEFAULT_SEED = True

QBER_THRESHOLD = 0.11
DEFAULT_PREVIEW_ROWS = 16

PLOT_STYLE = "seaborn-v0_8-whitegrid"
PLOT_FIGSIZE = (6.4, 3.6)
PLOT_COLORS = {
    "alice": "#2563eb",
    "bob": "#16a34a",
    "eve": "#dc2626",
    "kept": "#0f766e",
    "discarded": "#94a3b8",
    "threshold": "#111827",
    "error": "#b91c1c",
}

