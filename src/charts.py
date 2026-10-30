"""Static PNG charts for the README (reports/figures/).

Usage:
    python src/charts.py        # reads the CSVs in exports/

The interactive versions live in the dashboard (src/build_dashboard.py).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
FIGURES = ROOT / "reports" / "figures"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e4e3df"

plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "axes.titlecolor": INK,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
})


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(EXPORTS / f"{name}.csv")


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / name, bbox_inches="tight")
    plt.close(fig)


def monthly_revenue() -> None:
    df = load("monthly_kpis")
    df["order_month"] = pd.to_datetime(df["order_month"])
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(df["order_month"], df["revenue"] / 1e6, color=BLUE, linewidth=2, marker="o", markersize=4)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("£%.1fM"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
    ax.set_ylim(bottom=0)
    ax.set_title("Monthly revenue, Dec 2009 – Nov 2011")
    peak = df.loc[df["revenue"].idxmax()]
    ax.annotate(f"Peak {peak['order_month']:%b %Y}\n£{peak['revenue'] / 1e6:.2f}M",
                xy=(peak["order_month"], peak["revenue"] / 1e6), xytext=(-90, -10),
                textcoords="offset points", color=INK, fontsize=9,
                arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.8))
    save(fig, "monthly_revenue.png")


def cohort_heatmap() -> None:
    df = load("cohort_retention")
    df = df[df["month_number"].between(1, 12)]
    grid = df.pivot(index="cohort_month", columns="month_number", values="retention_pct")
    grid.index = pd.to_datetime(grid.index).strftime("%b %Y")
    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(grid.values, cmap="Blues", aspect="auto", vmin=0, vmax=40)
    ax.set_xticks(range(len(grid.columns)), labels=grid.columns)
    ax.set_yticks(range(len(grid.index)), labels=grid.index)
    ax.grid(False)
    for (i, j), v in pd.DataFrame(grid.values).stack().items():
        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                color="white" if v > 28 else INK)
    ax.set_xlabel("Months since first purchase")
    ax.set_title("Cohort retention: % of each cohort buying again in month N")
    fig.colorbar(im, ax=ax, format=mtick.PercentFormatter(decimals=0), shrink=0.7)
    save(fig, "cohort_retention.png")


def rfm_segments() -> None:
    df = load("rfm_segments").sort_values("pct_revenue")
    fig, ax = plt.subplots(figsize=(9, 4))
    y = range(len(df))
    h = 0.38
    ax.barh([i + h / 2 for i in y], df["pct_customers"], height=h, color=BLUE, label="% of customers")
    ax.barh([i - h / 2 for i in y], df["pct_revenue"], height=h, color=ORANGE, label="% of revenue")
    ax.set_yticks(list(y), labels=df["segment"])
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("RFM segments: share of customers vs share of revenue")
    save(fig, "rfm_segments.png")


def pareto() -> None:
    df = load("customer_pareto")
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["pct_customers"], df["cumulative_pct_revenue"], color=BLUE, linewidth=2)
    at20 = df.loc[(df["pct_customers"] - 20).abs().idxmin()]
    ax.scatter([at20["pct_customers"]], [at20["cumulative_pct_revenue"]], color=BLUE, s=36, zorder=3)
    ax.annotate(f"Top 20% of customers\n= {at20['cumulative_pct_revenue']:.1f}% of revenue",
                xy=(at20["pct_customers"], at20["cumulative_pct_revenue"]), xytext=(18, -40),
                textcoords="offset points", fontsize=9, color=INK)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_xlabel("Customers, ranked by revenue")
    ax.set_ylim(0, 101)
    ax.set_xlim(0, 100)
    ax.set_title("Revenue concentration (Pareto curve)")
    save(fig, "customer_pareto.png")


if __name__ == "__main__":
    FIGURES.mkdir(parents=True, exist_ok=True)
    monthly_revenue()
    cohort_heatmap()
    rfm_segments()
    pareto()
    print(f"Saved figures to {FIGURES}")
