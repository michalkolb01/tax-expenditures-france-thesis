"""Figure 5.1 - Kaplan-Meier: share of measures not terminated, by 2011 score.

Redraws the analysis notebook's figure (Untitled9.ipynb, cells 13-20 and 34)
with src/thesis_style.py (Latin Modern Roman, grey-scale palette, no title).

Input   data/intermediate/termination_dataset_v35.csv
Output  figures/fig5_1_survival_by_score.pdf (+ .png)
Requires the Latin Modern fonts (apt-get install fonts-lmodern); check with
`pdffonts figures/fig5_1_survival_by_score.pdf` (LMRoman10-Regular embedded).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from lifelines import KaplanMeierFitter  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "src" / "config.py").exists()) / "src"))
from config import INTERMEDIATE  # noqa: E402
from thesis_style import LINESTYLES, PALETTE, figsize, save_figure, use_thesis_style  # noqa: E402

ORDER = ["0", "1", "2", "3", "not scored"]
LABEL = {"0": "Score 0", "1": "Score 1", "2": "Score 2", "3": "Score 3", "not scored": "Not scored"}
ORIGIN = 2011


def main():
    use_thesis_style()
    d = pd.read_csv(INTERMEDIATE / "termination_dataset_v35.csv", dtype={"code": str, "score": str})
    d["group"] = d["group"].astype(str)
    fig, ax = plt.subplots(figsize=figsize(1.0))
    for g, col, ls in zip(ORDER, PALETTE, LINESTYLES):
        s = d[d["group"] == g]
        sf = KaplanMeierFitter().fit(s["duration"], event_observed=s["event"]).survival_function_.iloc[:, 0]
        ax.step(sf.index + ORIGIN, sf.values, where="post", color=col, linestyle=ls, linewidth=1.8,
                label=f"{LABEL[g]} ($n$ = {len(s)})")
    ax.set_xlim(ORIGIN, 2026)
    ax.set_xticks(range(2012, 2027, 2))
    ax.set_ylim(0.5, 1.01)   # axis starts at 0.5; noted in the caption
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of measures not terminated")
    ax.legend(loc="lower left")
    save_figure(fig, "fig5_1_survival_by_score")
    print("Written figures/fig5_1_survival_by_score.pdf and .png")


if __name__ == "__main__":
    main()
