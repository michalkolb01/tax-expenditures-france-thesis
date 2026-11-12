"""Survival analysis (4.2.1): termination by 2011 score, routes, Kaplan-Meier.

Taken from the analysis notebook (Untitled9.ipynb, cells 31 and 34) on the
frozen v3.5 dataset.

Input
    data/intermediate/termination_dataset_v35.csv
        built by 1_data/1_2_panel_2009_2026/03_build_termination_v35.py: one row
        per measure open in 2011 (379), with score group, event (terminated by
        2026), event_year, duration from 2011, mechanism, basis, sched_end_2011.
Reproduces (Chapter 5)
    5.1  Population followed: 379 measures, 278 scored (95/81/42/60), 101 not scored.
    5.2  Terminated by 2026: 41/95, 33/81, 10/42, 15/60, 38/101 (137 in all).
         Routes, grouped by the `mechanism` column (how the measure ended):
         end date recorded in the annex (end_date_unverified + sunset) 111;
         suppression by law (repeal + underlying_tax_reform + external) 26.
         The cross-tabulation with `basis` (where the year comes from) is
         written for reference.
         13 scored measures with a closure already scheduled in 2011.
         Kaplan-Meier survival by score group (Figure 5.1: 02_figure_5_1.py).
Outputs (tables/)
    termination_shares_by_score.csv, routes_by_score.csv, route_by_basis.csv,
    km_survival_by_score.csv
"""
import sys
from pathlib import Path

import pandas as pd
from lifelines import KaplanMeierFitter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "src" / "config.py").exists()) / "src"))
from config import INTERMEDIATE  # noqa: E402

TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)
ORDER = ["0", "1", "2", "3", "not scored"]
END_DATE = {"end_date_unverified", "sunset"}
ORIGIN = 2011


def route(mechanism):
    """The chapter's two routes, from the `mechanism` column."""
    if pd.isna(mechanism) or mechanism == "":
        return ""
    return "end date recorded in the annex" if mechanism in END_DATE else "suppression by law"


def load():
    d = pd.read_csv(INTERMEDIATE / "termination_dataset_v35.csv", dtype={"code": str, "score": str})
    d["code"] = d["code"].str.zfill(6)
    d["group"] = d["group"].astype(str)
    d["route"] = d["mechanism"].where(d["event"] == 1).map(route)
    return d


def main():
    d = load()
    sh = d.groupby("group").agg(measures=("code", "size"), terminated=("event", "sum")).reindex(ORDER)
    sh.loc["all"] = sh.sum()
    sh["share"] = (sh["terminated"] / sh["measures"]).round(3)
    sh.to_csv(TAB / "termination_shares_by_score.csv")
    print("Population and terminations:\n", sh.to_string(), "\n")

    ev = d[d["event"] == 1]
    r = pd.crosstab(ev["route"], ev["group"], margins=True).reindex(columns=ORDER + ["All"], fill_value=0)
    r.to_csv(TAB / "routes_by_score.csv")
    print("Routes (grouped by `mechanism`):\n", r.to_string(), "\n")
    rb = pd.crosstab([ev["route"], ev["mechanism"]], ev["basis"], margins=True)
    rb.to_csv(TAB / "route_by_basis.csv")
    print("Route x basis:\n", rb.to_string(), "\n")

    sc = d[d["group"].isin(ORDER[:4])]
    print("Scheduled closure in 2011 (scored):", int(sc["sched_end_2011"].sum()), "\n")

    km = []
    for g in ORDER:
        s = d[d["group"] == g]
        sf = KaplanMeierFitter().fit(s["duration"], event_observed=s["event"]).survival_function_.iloc[:, 0]
        km.append(pd.DataFrame({"group": g, "year": (sf.index + ORIGIN).round(2), "share_not_terminated": sf.values}))
    km = pd.concat(km, ignore_index=True)
    km.to_csv(TAB / "km_survival_by_score.csv", index=False)
    last = km.groupby("group")["share_not_terminated"].last().reindex(ORDER).round(3)
    print("Kaplan-Meier share not terminated at the end of the window:\n", last.to_string())


if __name__ == "__main__":
    main()
