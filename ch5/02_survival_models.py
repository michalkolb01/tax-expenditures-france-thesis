"""Chapter 5 - Termination shares, routes, Cox models and Table 5.1.

Taken from the analysis notebook (Untitled9.ipynb, cells 11, 31 and 35), which
ran on the frozen v3.5 dataset. Only the code behind the chapter's numbers is
kept; the KM and hazard-ratio figures are redrawn in 03_figures.py.

Inputs
    ch5/tables/termination_dataset_v35.csv   built by build_termination_v35.py
        (one row per measure open in 2011: score, event, event_year, duration
        from 2011, mechanism, basis, sched_end_2011, ...)
    data/intermediate/guillaume_all.csv      the 470 measures of the 2011 report
        (score, cost_2011, beneficiaires, impot)
    data/intermediate/vm_2009_2019.parquet   2011 annex edition (creation year)

Reproduces (Chapter 5)
    5.1  Table 5.1: number of measures and cost in 2011 (EUR million) by score,
         over the 470 measures examined by the committee (the whole report, not
         only the 379 followed): 11,764 / 28,236 / 11,393 / 9,305 / 4,935,
         total 65,633.
         Population followed: 379 measures, 278 scored (95/81/42/60), 101 not.
    5.2  Terminated by 2026: 41/95, 33/81, 10/42, 15/60, 38/101 (137).
         Routes, grouped by the `mechanism` column (the chapter's grouping):
         end date (end_date_unverified + sunset) 111, suppression by law
         (repeal + underlying_tax_reform + external) 26.
         13 scored measures with a closure already scheduled in 2011.
    5.3  Cox, score per point: HR 0.77 (0.64-0.93), p = 0.006.
         With controls (households, log cost, no cost estimate, age, income
         tax): 0.786 (0.653-0.946), rounded to 0.79 in the text.
         Without the 13 scheduled closures: 0.76.
    5.4  Terminations per year by score group; Cox by period:
         2011-2014 0.62 (p = 0.009), from 2015 0.85 (p = 0.15).
Outputs (ch5/tables/)
    table5_1_scores_costs_2011.csv, termination_shares_by_score.csv,
    routes_by_score.csv, route_by_basis.csv, terminations_per_year.csv,
    cox_models.csv, cox_with_controls.csv
"""
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
from config import INTERMEDIATE  # noqa: E402

TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)
ORDER = ["0", "1", "2", "3", "not scored"]
END_DATE = {"end_date_unverified", "sunset"}
warnings.filterwarnings("ignore")


def route(mechanism):
    """The chapter's two routes, from the `mechanism` column."""
    if pd.isna(mechanism) or mechanism == "":
        return ""
    return "end date recorded in the annex" if mechanism in END_DATE else "suppression by law"


def yr(x):
    m = re.search(r"(19|20)\d{2}", str(x))
    return int(m.group(0)) if m else np.nan


def load():
    d = pd.read_csv(TAB / "termination_dataset_v35.csv", dtype={"code": str, "score": str})
    d["code"] = d["code"].str.zfill(6)
    d["route"] = d["mechanism"].where(d["event"] == 1).map(route)
    return d


def cox_row(data, cols, label, key="score_num"):
    f = CoxPHFitter().fit(data[["duration", "event"] + cols], "duration", "event")
    s = f.summary.loc[key]
    return dict(model=label, N=len(data), events=int(data["event"].sum()),
                HR=round(s["exp(coef)"], 3), CI_low=round(s["exp(coef) lower 95%"], 3),
                CI_high=round(s["exp(coef) upper 95%"], 3), p=round(s["p"], 4))


def table_5_1():
    g = pd.read_csv(INTERMEDIATE / "guillaume_all.csv", dtype=str)
    g["cost"] = pd.to_numeric(g["cost_2011"], errors="coerce")   # 'nc', 'ε', '-' = no figure
    g["score"] = g["score"].replace({"Non évalué": "not scored"})
    t = g.groupby("score").agg(measures=("code", "size"), cost_2011_m_eur=("cost", "sum")).reindex(ORDER)
    t.loc["total"] = t.sum()
    t.to_csv(TAB / "table5_1_scores_costs_2011.csv")
    print("Table 5.1 (470 measures of the 2011 report):\n", t.round(0).to_string(), "\n")


def main():
    table_5_1()
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

    sc = d[d["group"].isin(ORDER[:4])].copy()
    sc["score_num"] = sc["score"].astype(int)
    print("Scheduled closure in 2011 (scored):", int(sc["sched_end_2011"].sum()))

    yr_tab = pd.crosstab(ev["event_year"], ev["group"], margins=True).reindex(columns=ORDER + ["All"], fill_value=0)
    yr_tab.to_csv(TAB / "terminations_per_year.csv")

    # Cox by period (Untitled9 c35): 2011-2014 with later closures counted as open;
    # from 2015 the measures still open at the end of 2014, clock restarted.
    early = sc.copy()
    early["event"] = ((sc["event"] == 1) & (sc["duration"] <= 3)).astype(int)
    early["duration"] = sc["duration"].clip(upper=3)
    late = sc[sc["duration"] > 3].copy()
    late["duration"] = late["duration"] - 3
    rows = [cox_row(sc, ["score_num"], "main (score per point)"),
            cox_row(sc[sc["sched_end_2011"] == 0], ["score_num"], "without closures scheduled in 2011"),
            cox_row(early, ["score_num"], "period 2011-2014"),
            cox_row(late, ["score_num"], "period 2015-2026")]

    # Controls (Untitled9 c11)
    g = pd.read_csv(INTERMEDIATE / "guillaume_all.csv", dtype=str).drop_duplicates("code")
    g["code"] = g["code"].str.strip().str.zfill(6)
    c = sc.merge(g[["code", "beneficiaires", "cost_2011", "impot"]], on="code", how="left")
    a = pd.read_parquet(INTERMEDIATE / "vm_2009_2019.parquet")
    a["numero"] = a["numero"].astype(str).str.zfill(6)
    r2011 = a[a["vm_year"] == 2011].drop_duplicates("numero").set_index("numero")
    c["households"] = c["beneficiaires"].fillna("").str.contains("nage", case=False).astype(int)
    cost = pd.to_numeric(c["cost_2011"].str.replace(r"[\s \xa0]", "", regex=True)
                         .str.replace(",", "."), errors="coerce")
    c["no_cost_estimate"] = cost.isna().astype(int)
    c["log_cost"] = np.log1p(cost.fillna(0))
    c["age"] = (2011 - c["code"].map(r2011["creation"]).map(yr)).clip(lower=0)
    c["age"] = c["age"].fillna(c["age"].median())
    c["income_tax"] = c["impot"].fillna("").str.lower().str.contains("impôt sur le revenu").astype(int)
    controls = ["households", "log_cost", "no_cost_estimate", "age", "income_tax"]
    rows.append(cox_row(c, ["score_num"] + controls, "with controls"))
    f = CoxPHFitter().fit(c[["duration", "event", "score_num"] + controls], "duration", "event")
    full = f.summary[["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].round(3)
    full.to_csv(TAB / "cox_with_controls.csv")

    C = pd.DataFrame(rows)
    C.to_csv(TAB / "cox_models.csv", index=False)
    print("Cox models:\n", C.to_string(index=False), "\n")
    print("Model with controls:\n", full.to_string())


if __name__ == "__main__":
    main()
