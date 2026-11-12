"""Build the readable panel workbook tax_expenditures_panel_2009_2026.xlsx.

Pipeline step, no thesis number directly (the workbook is read by
2_methods/2_4_arguments/01_build_reading_workbook.py and 2_methods/2_5_pairs/01_pair_search.py
for measure names and 2011 scores).

Stacks the two Voies et moyens parquets into one row per measure and
edition, extracts the year of the end of eligibility ("fin du fait
générateur") and of the end of budgetary cost, classes each measure-year as
"open, no end date" / "open, sunset clause" / "closed to new beneficiaries",
attaches the 2011 score (or "not in the 2011 report"), and writes a
one-row-per-measure summary (first and last annex, status in 2011 and in
the last annex).

Inputs
    data/intermediate/vm_2009_2019.parquet   (02_parse_voies_et_moyens.py)
    data/intermediate/vm_2020_2026.parquet   (02_parse_voies_et_moyens.py)
    data/intermediate/guillaume_all.csv      (01_parse_guillaume_2011.py)
Outputs
    data/intermediate/tax_expenditures_panel_2009_2026.xlsx
        sheet one_row_per_measure   851 measures
        sheet one_row_per_year      9,303 measure-years
Needs
    pip install pandas pyarrow openpyxl

Source
    Untitled9.ipynb, cell 3 (the only writer of this file; checked: the
    file in the package has the same sheets, columns and row counts).

Caveats
    - The notebook wrote to data/validation/; the package keeps the file in
      data/intermediate/.
    - For 2009-2019 the cost is the raw text of the three cost figures
      (cost_text); for 2020-2026 it is the three numeric columns
      cost_year_minus2, cost_year_minus1, cost_year. They are not merged.
    - Unnumbered 2011 measures ("DF ... NR") are zero-padded like the codes
      but match no annex number, so they do not appear in the panel.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

DATA = INTERMEDIATE


def yr(x):
    m = re.search(r"(19|20)\d{2}", str(x))
    return int(m.group(0)) if m else np.nan


def status(r):
    if pd.isna(r["end_eligibility"]):
        return "open, no end date"
    if r["end_eligibility"] >= r["vm_year"]:
        return "open, sunset clause"
    return "closed to new beneficiaries"


def main():
    # --- 1. Yearly panel: one row per measure per annex -----------------------
    a = pd.read_parquet(DATA / "vm_2009_2019.parquet")
    b = pd.read_parquet(DATA / "vm_2020_2026.parquet")
    a = a.rename(columns={"fin_fait": "end_eligibility_raw", "fin_incid": "end_cost_raw",
                          "costs": "cost_text"})
    b = b.rename(columns={"fin_fait_generateur": "end_eligibility_raw",
                          "fin_incidence": "end_cost_raw",
                          "realisation": "cost_year_minus2", "prevision_1": "cost_year_minus1",
                          "prevision_2": "cost_year"})
    keep = ["numero", "vm_year", "libelle", "end_eligibility_raw", "end_cost_raw",
            "cost_text", "cost_year_minus2", "cost_year_minus1", "cost_year"]
    panel = pd.concat([a.reindex(columns=keep), b.reindex(columns=keep)], ignore_index=True)
    panel["numero"] = panel["numero"].astype(str).str.zfill(6)
    panel["end_eligibility"] = panel["end_eligibility_raw"].map(yr)
    panel["end_cost"] = panel["end_cost_raw"].map(yr)
    panel["status"] = panel.apply(status, axis=1)

    scores = pd.read_csv(DATA / "guillaume_all.csv", dtype=str)[["code", "score"]].drop_duplicates("code")
    scores["code"] = scores["code"].str.strip().str.zfill(6)
    panel = panel.merge(scores.rename(columns={"code": "numero"}), on="numero", how="left")
    panel["score"] = panel["score"].fillna("not in the 2011 report")
    panel = panel.sort_values(["numero", "vm_year"])

    # --- 2. One row per measure -----------------------------------------------
    first = panel.groupby("numero").first()
    last = panel.groupby("numero").last()
    s2011 = panel[panel["vm_year"] == 2011].set_index("numero")["status"]
    summary = pd.DataFrame({
        "name": last["libelle"],
        "score_2011": last["score"],
        "first_annex": first["vm_year"],
        "last_annex": last["vm_year"],
        "status_in_2011": s2011,
        "status_in_last_annex": last["status"],
        "end_eligibility_in_last_annex": last["end_eligibility"],
    }).reset_index().rename(columns={"numero": "code"})

    # --- 3. Save --------------------------------------------------------------
    out = DATA / "tax_expenditures_panel_2009_2026.xlsx"
    with pd.ExcelWriter(out) as w:
        summary.to_excel(w, sheet_name="one_row_per_measure", index=False)
        panel.to_excel(w, sheet_name="one_row_per_year", index=False)
    print(f"{len(summary)} measures, {len(panel)} measure-years\nSaved to {out}")


if __name__ == "__main__":
    main()
