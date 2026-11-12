"""Table 5.1 - The 2011 evaluation: number of measures and cost in 2011 by score.

Computed over the 470 measures examined by the committee (the whole 2011
report, as the chapter says), not over the 379 measures followed in the
survival analysis.

Input
    data/intermediate/guillaume_all.csv   (01_parse_guillaume_2011.py)
        cost_2011 in EUR million; 'nc', 'ε' and '-' (no figure) count as missing.
Reproduces (Table 5.1, section 5.1; data described in 4.1.1)
    Measures: 125 / 99 / 46 / 69 / 131 (scores 0-3, not scored), 470 in total.
    Cost in 2011 (EUR million): 11,764 / 28,236 / 11,393 / 9,305 / 4,935;
    total 65,633.
Output
    tables/table5_1_scores_costs_2011.csv
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "src" / "config.py").exists()) / "src"))
from config import INTERMEDIATE  # noqa: E402

TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)
ORDER = ["0", "1", "2", "3", "not scored"]


def main():
    g = pd.read_csv(INTERMEDIATE / "guillaume_all.csv", dtype=str)
    g["cost"] = pd.to_numeric(g["cost_2011"], errors="coerce")
    g["score"] = g["score"].replace({"Non évalué": "not scored"})
    t = g.groupby("score").agg(measures=("code", "size"), cost_2011_m_eur=("cost", "sum")).reindex(ORDER)
    t.loc["total"] = t.sum()
    t.to_csv(TAB / "table5_1_scores_costs_2011.csv")
    print("Table 5.1 (470 measures of the 2011 report):\n", t.round(0).to_string())


if __name__ == "__main__":
    main()
