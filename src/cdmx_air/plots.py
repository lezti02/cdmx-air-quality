"""Shared plotting style and helpers."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .clustering import SCENARIO_ORDER
from .config import FIGURES_DIR

SCENARIO_COLORS = dict(
    zip(SCENARIO_ORDER, ["#66C2A5", "#8DA0CB", "#E78AC3", "#FC8D62"], strict=True)
)


def set_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save_fig(fig: plt.Figure, name: str) -> None:
    """Save a figure to reports/figures/<name>.png."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / f"{name}.png")


def missing_heatmap(pct_missing: pd.DataFrame, title: str) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 9))
    sns.heatmap(
        pct_missing,
        annot=True,
        fmt=".0f",
        cmap="Reds",
        vmin=0,
        vmax=100,
        linewidths=0.5,
        cbar_kws={"label": "Missing values (%)"},
        ax=ax,
    )
    ax.set(title=title, xlabel="Pollutant", ylabel="Monitoring station")
    return fig


def stacked_share(table: pd.DataFrame, title: str, xlabel: str, kind: str = "bar") -> plt.Figure:
    """Stacked bars (or areas) of scenario share; `table` rows sum to 100."""
    colors = [SCENARIO_COLORS[c] for c in table.columns]
    fig, ax = plt.subplots(figsize=(12, 5))
    if kind == "area":
        table.plot(kind="area", stacked=True, color=colors, alpha=0.85, linewidth=0, ax=ax)
        ax.margins(x=0)
    else:
        table.plot(kind=kind, stacked=True, color=colors, width=0.85, edgecolor="white", ax=ax)
    ax.set(title=title, xlabel=xlabel, ylabel="Share of hours (%)", ylim=(0, 100))
    ax.legend(title="Scenario", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.tick_params(axis="x", rotation=0)
    return fig
