"""Chapter 5 - Figures 5.1, 5.2 and 5.3 in the thesis style (Latin Modern Roman).

Redraws the figures of the analysis notebook (Untitled9.ipynb: Kaplan-Meier,
cells 13-20 and 34; hazard ratios, cell 29; terminations per year, cell 35)
with src/thesis_style.py. Same data and estimates; only the styling changed
(fonts, size, grey-scale palette, no titles - captions are set in LaTeX).

Inputs
    ch5/tables/termination_dataset_v35.csv   (build_termination_v35.py)
    ch5/tables/cox_with_controls.csv         (02_survival_models.py)
Outputs (figures/, PDF for LaTeX + PNG preview)
    fig5_1_survival_by_score   Kaplan-Meier, share of measures not terminated, by 2011 score
    fig5_2_cox_hazard_ratios   Cox model with controls: hazard ratios and 95% CIs
    fig5_3_terminations_per_year  terminations per year, stacked by score group
Requires the Latin Modern fonts (apt-get install fonts-lmodern); check the
PDFs with `pdffonts figures/fig5_*.pdf` (LMRoman10-Regular must be embedded).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from lifelines import KaplanMeierFitter  # noqa: E402
from matplotlib.ticker import MaxNLocator, NullLocator, ScalarFormatter  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from thesis_style import LINESTYLES, PALETTE, figsize, save_figure, use_thesis_style  # noqa: E402

TAB = HERE / "tables"
ORDER = ["0", "1", "2", "3", "not scored"]
LABEL = {"0": "Score 0", "1": "Score 1", "2": "Score 2", "3": "Score 3", "not scored": "Not scored"}
ORIGIN = 2011


def fig5_1(d):
    fig, ax = plt.subplots(figsize=figsize(1.0))
    for g, col, ls in zip(ORDER, PALETTE, LINESTYLES):
        s = d[d["group"] == g]
        sf = KaplanMeierFitter().fit(s["duration"], event_observed=s["event"]).survival_function_.iloc[:, 0]
        ax.step(sf.index + ORIGIN, sf.values, where="post", color=col, linestyle=ls,
                label=f"{LABEL[g]} ($n$ = {len(s)})")
    ax.set_xlim(ORIGIN, 2026)
    ax.set_xticks(range(2012, 2027, 2))
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of measures not terminated")
    ax.legend(loc="lower left")
    save_figure(fig, "fig5_1_survival_by_score")


def fig5_2():
    res = pd.read_csv(TAB / "cox_with_controls.csv", index_col=0)
    labels = {"score_num": "Score (per point)", "households": "Benefits households",
              "log_cost": "Cost in 2011 (log)", "no_cost_estimate": "No cost estimate",
              "age": "Age of the measure (years)", "income_tax": "Income tax measure"}
    res = res.loc[list(labels)].iloc[::-1]
    y = np.arange(len(res))
    hr, lo, hi = res["exp(coef)"], res["exp(coef) lower 95%"], res["exp(coef) upper 95%"]
    fig, ax = plt.subplots(figsize=figsize(1.0, 0.5))
    ax.errorbar(hr, y, xerr=[hr - lo, hi - hr], fmt="o", color=PALETTE[0], capsize=3, markersize=4)
    ax.axvline(1, color=PALETTE[2], linestyle="--", linewidth=0.8)
    ax.set_xscale("log")
    ax.set_xlim(0.45, 2.4)
    ax.set_xticks([0.5, 0.75, 1, 1.5, 2])
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_yticks(y)
    ax.set_yticklabels([labels[k] for k in res.index])
    ax.set_xlabel("Hazard ratio of termination (95% confidence interval, log scale)")
    for i, p in enumerate(res["p"]):
        ax.text(1.02, i, f"$p$ = {p:.3f}", va="center", transform=ax.get_yaxis_transform())
    save_figure(fig, "fig5_2_cox_hazard_ratios")


def fig5_3(d):
    ev = d[d["event"] == 1]
    t = pd.crosstab(ev["event_year"], ev["group"]).reindex(index=range(2011, 2027), columns=ORDER, fill_value=0)
    fig, ax = plt.subplots(figsize=figsize(1.0))
    bottom = np.zeros(len(t))
    for g, col in zip(ORDER, PALETTE):
        ax.bar(t.index, t[g], bottom=bottom, color=col, edgecolor="white", linewidth=0.4,
               width=0.8, label=LABEL[g])
        bottom += t[g].values
    ax.set_xticks(range(2011, 2027, 1))
    ax.tick_params(axis="x", labelrotation=90)
    ax.set_xlabel("Year of termination")
    ax.set_ylabel("Number of measures terminated")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(ncol=2)
    save_figure(fig, "fig5_3_terminations_per_year")


def main():
    use_thesis_style()
    d = pd.read_csv(TAB / "termination_dataset_v35.csv", dtype={"code": str, "score": str})
    d["group"] = d["group"].astype(str)
    fig5_1(d)
    fig5_2()
    fig5_3(d)
    print("Figures written to figures/fig5_1..3 (PDF + PNG).")


if __name__ == "__main__":
    main()
