"""Cox model (4.2.2): score per point, controls, scheduled closures, period split.

Taken from the analysis notebook (Untitled9.ipynb, cells 11, 31 and 35) on the
frozen v3.5 dataset. Models are fitted with lifelines' CoxPHFitter, which
handles tied event times with Efron's method (the data are annual, so almost
all event times are tied). Standard errors are the model-based ones.

Inputs
    data/intermediate/termination_dataset_v35.csv   (1_data/1_2_panel_2009_2026/)
    data/intermediate/guillaume_all.csv             (1_data/1_1_evaluation_2011/): beneficiaries,
                                                    cost in 2011, tax concerned
    data/intermediate/vm_2009_2019.parquet          (1_data/1_2_panel_2009_2026/): year of creation
Reproduces (Chapter 5)
    5.3  Score per point, scored measures (N 278, 99 events): HR 0.773
         (0.642-0.930), p = 0.006 - reported as 0.77 (0.64-0.93).
         With controls (households, log cost, no cost estimate, age, income
         tax): 0.786 (0.653-0.946), reported as 0.79.
         Without the 13 closures scheduled in 2011: 0.762.
    5.4  Terminations per year by score group (Figure 5.3);
         Cox by period: 2011-2014 0.623 (p = 0.009); from 2015 0.849 (p = 0.146).
    Robustness (not reported as a result): proportional-hazards tests on the
    scaled Schoenfeld residuals (Grambsch-Therneau), Kaplan-Meier time
    transform, for the score and globally, main and controls models.
Outputs (tables/)
    cox_models.csv, cox_with_controls.csv, terminations_per_year.csv, ph_tests.csv
"""
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import proportional_hazard_test
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "src" / "config.py").exists()) / "src"))
from config import INTERMEDIATE  # noqa: E402

TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)
ORDER = ["0", "1", "2", "3", "not scored"]
CONTROLS = ["households", "log_cost", "no_cost_estimate", "age", "income_tax"]
warnings.filterwarnings("ignore")


def yr(x):
    m = re.search(r"(19|20)\d{2}", str(x))
    return int(m.group(0)) if m else np.nan


def cox_row(data, cols, label, key="score_num"):
    f = CoxPHFitter().fit(data[["duration", "event"] + cols], "duration", "event")
    s = f.summary.loc[key]
    return dict(model=label, N=len(data), events=int(data["event"].sum()),
                HR=round(s["exp(coef)"], 3), CI_low=round(s["exp(coef) lower 95%"], 3),
                CI_high=round(s["exp(coef) upper 95%"], 3), p=round(s["p"], 4))


def with_controls(sc):
    """Controls as coded in Untitled9.ipynb, cell 11."""
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
    return c


def ph_tests(data, cols, label):
    """Schoenfeld-residual tests: lifelines per covariate (KM transform) and the
    Grambsch-Therneau global test (formula of survival::cox.zph before v3)."""
    data = data[["duration", "event"] + cols].reset_index(drop=True)
    f = CoxPHFitter().fit(data, "duration", "event")
    per = proportional_hazard_test(f, data, time_transform="km").summary
    R = f.compute_residuals(data, "schoenfeld")
    t = data.loc[R.index, "duration"].values
    km = KaplanMeierFitter().fit(data["duration"], data["event"])
    xx = (1 - km.survival_function_at_times(t).values)
    xx = xx - xx.mean()
    V = f.variance_matrix_.loc[R.columns, R.columns].values
    ne = len(R)
    test = xx @ (R.values @ V * ne)
    zg = float(test @ np.linalg.solve(V, test)) / (ne * (xx ** 2).sum())
    rows = [dict(model=label, term=k, chi2=round(per.loc[k, "test_statistic"], 3), df=1,
                 p=round(per.loc[k, "p"], 3)) for k in cols]
    rows.append(dict(model=label, term="GLOBAL", chi2=round(zg, 3), df=len(cols),
                     p=round(stats.chi2.sf(zg, len(cols)), 3)))
    return rows


def main():
    d = pd.read_csv(INTERMEDIATE / "termination_dataset_v35.csv", dtype={"code": str, "score": str})
    d["code"] = d["code"].str.zfill(6)
    d["group"] = d["group"].astype(str)
    sc = d[d["group"].isin(ORDER[:4])].copy()
    sc["score_num"] = sc["score"].astype(int)

    ev = d[d["event"] == 1]
    yt = pd.crosstab(ev["event_year"], ev["group"], margins=True).reindex(columns=ORDER + ["All"], fill_value=0)
    yt.to_csv(TAB / "terminations_per_year.csv")
    print("Terminations per year:\n", yt.to_string(), "\n")

    # Period split (Untitled9 c35): 2011-2014 with later closures counted as open;
    # from 2015 the measures still open at the end of 2014, clock restarted.
    early = sc.copy()
    early["event"] = ((sc["event"] == 1) & (sc["duration"] <= 3)).astype(int)
    early["duration"] = sc["duration"].clip(upper=3)
    late = sc[sc["duration"] > 3].copy()
    late["duration"] = late["duration"] - 3

    c = with_controls(sc)
    rows = [cox_row(sc, ["score_num"], "main (score per point)"),
            cox_row(c, ["score_num"] + CONTROLS, "with controls"),
            cox_row(sc[sc["sched_end_2011"] == 0], ["score_num"], "without closures scheduled in 2011"),
            cox_row(early, ["score_num"], "period 2011-2014"),
            cox_row(late, ["score_num"], "period 2015-2026")]
    C = pd.DataFrame(rows)
    C.to_csv(TAB / "cox_models.csv", index=False)
    print("Cox models (lifelines CoxPHFitter, Efron ties):\n", C.to_string(index=False), "\n")

    f = CoxPHFitter().fit(c[["duration", "event", "score_num"] + CONTROLS], "duration", "event")
    full = f.summary[["exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].round(3)
    full.to_csv(TAB / "cox_with_controls.csv")
    print("Model with controls:\n", full.to_string(), "\n")

    ph = pd.DataFrame(ph_tests(sc, ["score_num"], "main") + ph_tests(c, ["score_num"] + CONTROLS, "with controls"))
    ph.to_csv(TAB / "ph_tests.csv", index=False)
    print("Proportional-hazards tests (Schoenfeld residuals, KM transform):\n", ph.to_string(index=False))


if __name__ == "__main__":
    main()
