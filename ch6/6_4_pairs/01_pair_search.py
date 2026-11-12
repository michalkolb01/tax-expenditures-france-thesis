"""Section 6.4 - Systematic search for comparable pairs of measures.

The pairs in 6.4 were chosen to hold as much as possible constant:
    1. the same or almost the same 2011 score (0 or 1);
    2. the same decision (the same bill, article or amendment);
    3. the closest possible policy area;
    4. different outcomes (one abolished, one kept).

This script documents the two searches behind the choice.

Search 1 - same bill, same family of the annex, different fate
    Using the amendments matched to measures (data/intermediate/
    amendments_classified.csv: one row per amendment-measure pair with the
    direction of the amendment) and the panel, it lists pairs of measures
    scored 0 or 1 that were both targeted by amendments to remove or narrow
    them in the same bill, belong to the same family of the annex (same
    first four digits of the code, or same first three for close
    families), and had different fates (one ended, one still open in 2026).
    Output: tables/pair_candidates_same_bill.csv
    Result used in the thesis: the two income-tax reductions for local
    investment funds (110228 mainland, 110245 Corsica; both scored 0;
    debated together in the bills for 2021, 2022 and 2025) -> Pair C.

Search 2 - one decision with many measures: article 5 of the finance bill for 2026
    Article 5 proposed abolishing 23 tax expenditures at once. The codes are
    taken from the government's impact assessment (Évaluations préalables
    des articles du PLF 2026, article 5, section 4.3). The script attaches
    each code's 2011 score from the panel. Within this decision, measures of
    the same area shared the same fate, so no pair met all four criteria;
    the closest is Pair B (work medal bonuses / long-term illness
    allowances, both scored 0).
    Output: tables/plf2026_article5_scores.csv

Thesis text: section 6.4, introduction (how the pairs were chosen).
"""
import itertools
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from config import INTERMEDIATE  # noqa: E402

HERE = Path(__file__).resolve().parent
TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)

# Codes abolished or modified by article 5 of the PLF 2026 (impact assessment, section 4.3)
PLF2026_ART5 = [60105, 110215, 110239, 110242, 120104, 120116, 120129, 120204, 160201, 160303,
                190212, 200214, 200215, 210315, 210327, 220108, 320109, 520125, 530211, 800215,
                800216, 930102]


def load_panel():
    x = pd.ExcelFile(INTERMEDIATE / "tax_expenditures_panel_2009_2026.xlsx")
    m = x.parse("one_row_per_measure")
    y = x.parse("one_row_per_year")
    status = y.sort_values("vm_year").groupby("numero").last()["status"]
    m = m.set_index("code")
    m["status_last"] = status
    m["ended"] = (m.last_annex < 2026) | m.status_last.astype(str).str.contains("closed")
    m["score"] = m.score_2011.astype(str)
    return m


def search_same_bill(m):
    c = pd.read_csv(INTERMEDIATE / "amendments_classified.csv").dropna(subset=["measure"])
    c["measure"] = c.measure.astype(int)
    # bill identifier from the amendment uid: legislature + bill number
    c["bill"] = c.uid.str.extract(r"(L1\d)")[0] + "-" + c.uid.str.extract(r"B(\d+)")[0]
    cut = c[c.categorie.isin(["supprime", "restreint"])]
    rows = []
    for bill, g in cut.groupby("bill"):
        ms = [k for k in g.measure.unique() if k in m.index and m.loc[k, "score"] in ("0", "1")]
        for a, b in itertools.combinations(ms, 2):
            same_family = str(a)[:-2] == str(b)[:-2] or str(a)[:3] == str(b)[:3]
            if same_family and m.loc[a, "ended"] != m.loc[b, "ended"]:
                rows.append({"bill": bill,
                             "code_a": a, "name_a": m.loc[a, "name"], "score_a": m.loc[a, "score"],
                             "ended_a": m.loc[a, "ended"],
                             "code_b": b, "name_b": m.loc[b, "name"], "score_b": m.loc[b, "score"],
                             "ended_b": m.loc[b, "ended"]})
    r = pd.DataFrame(rows).drop_duplicates(subset=["code_a", "code_b"])
    r.to_csv(TAB / "pair_candidates_same_bill.csv", index=False)
    print(f"Search 1: {len(r)} candidate pairs (same bill, same family, different fate)")
    fip = r[r.code_a.isin([110228, 110245]) | r.code_b.isin([110228, 110245])]
    print(fip[["bill", "code_a", "score_a", "ended_a", "code_b", "score_b", "ended_b"]].to_string(index=False))


def search_article5(m):
    rows = [{"code": k, "name": m.loc[k, "name"] if k in m.index else "",
             "score_2011": m.loc[k, "score"] if k in m.index else "not in panel"} for k in PLF2026_ART5]
    r = pd.DataFrame(rows)
    r.to_csv(TAB / "plf2026_article5_scores.csv", index=False)
    print(f"\nSearch 2: article 5 of the PLF 2026, {len(r)} codes")
    print(r.score_2011.value_counts().to_string())


if __name__ == "__main__":
    panel = load_panel()
    search_same_bill(panel)
    search_article5(panel)
