"""Section 6.2.1 - Counts reported in the text, from the manually reviewed passages.

Input
    data/te_passages_with_evaluation_reviewed.csv
        The 536 passages found by 01_search_evaluation_bodies.py, each read
        and coded in the column 'genuine' (1 = an evaluation body is cited
        about a tax expenditure; 0 = not, e.g. the Court of Audit cited on
        public debt in a passage that also mentions an exemption).
    data/te_passages_precision_check_50.csv
        A random sample of 50 matches read first, before the full review, to
        estimate the precision of the automatic search.

Reproduces (section 6.2.1)
    - 494 genuine passages out of 536 matches; with the 20,000 passages
      referring to a tax expenditure printed by step 1, about 2.5%.
    - Shares of genuine passages naming each body: Court of Audit about 65%,
      General Inspectorate of Finance about 22%, France Strategy about 10%,
      Council for Compulsory Levies about 8% (a passage may name several).
    - Distribution by venue and period; concentration on the large measures.
    - Timing: where the speaker gives the report's year, most citations come
      within two years of publication (about 60%; 145 dated citations in
      102 passages).
Outputs
    tables/ch6_2_1_*.csv
"""
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)
DENOMINATOR = 20_000   # printed by step 1 (committee 2,699 + plenary 17,301)

BODIES = ["Court of Audit", "General Inspectorate of Finance", "Council for Compulsory Levies", "France Strategy"]
MEASURES = ["research tax credit", "Dutreil pact", "home services credit", "film and audiovisual credits"]
BODY_RX = {
    "Court of Audit": r"Cour des comptes",
    "General Inspectorate of Finance": r"Inspection générale des finances|\bIGF\b",
    "Council for Compulsory Levies": r"Conseil des prélèvements obligatoires|\bCPO\b",
    "France Strategy": r"France Stratégie",
}


def main():
    a = pd.read_csv(HERE / "data" / "te_passages_with_evaluation_reviewed.csv")
    g = a[a.genuine == 1].copy()
    print(f"Matches: {len(a)}; genuine after reading: {len(g)}; "
          f"share of the {DENOMINATOR:,} passages: {len(g) / DENOMINATOR:.1%}")

    pc = pd.read_csv(HERE / "data" / "te_passages_precision_check_50.csv")
    print(f"Precision check on a random sample of {len(pc)} matches: {pc.genuine.mean():.0%} genuine")

    shares = g[BODIES].mean().rename("share_of_genuine_passages")
    print("\nShare of genuine passages naming each body:")
    print(shares.map("{:.0%}".format).to_string())
    shares.to_csv(TAB / "ch6_2_1_shares_by_body.csv")

    by = g.groupby(["period", "venue"]).size().unstack(fill_value=0)
    print("\nGenuine passages by period and venue:")
    print(by.to_string())
    by.to_csv(TAB / "ch6_2_1_by_period_venue.csv")

    bp = g.groupby("period")[BODIES].sum()
    bp.to_csv(TAB / "ch6_2_1_bodies_by_period.csv")
    mp = g.groupby("period")[MEASURES].sum()
    print("\nGenuine passages mentioning the large measures, by period:")
    print(mp.to_string())
    mp.to_csv(TAB / "ch6_2_1_large_measures_by_period.csv")
    print(f"Any of the four large measures: {g[MEASURES].any(axis=1).mean():.0%} of genuine passages")

    # Timing: citations where the speaker names the report's year
    rows = []
    for idx, r in g.iterrows():
        t, py = r.text, int(r.year)
        for b, p in BODY_RX.items():
            for m in re.finditer(p, t):
                win = t[max(0, m.start() - 120):m.end() + 120]
                for y in re.findall(r"\b(20[01]\d|202[0-6])\b", win):
                    y = int(y)
                    if 2008 <= y <= py:
                        rows.append((b, y, py, idx))
    d = pd.DataFrame(rows, columns=["body", "report_year", "debate_year", "pid"])
    d = d.drop_duplicates(["body", "report_year", "pid"])
    d["gap"] = d.debate_year - d.report_year
    d["gap_group"] = pd.cut(d.gap, [-1, 2, 5, 30], labels=["0-2 years", "3-5 years", "6+ years"])
    print(f"\nDated citations: {len(d)} in {d.pid.nunique()} passages")
    print(d.gap_group.value_counts(normalize=True).sort_index().map("{:.0%}".format).to_string())
    d.to_csv(TAB / "ch6_2_1_dated_citations.csv", index=False)
    print("\nMost cited reports (10 or more dated citations), citations by debate year:")
    for (b, ry), s in d.groupby(["body", "report_year"]):
        if len(s) >= 10:
            print(f"  {b} {ry}: {s.debate_year.value_counts().sort_index().to_dict()}")
    print("\nNote: recent reports cannot yet have long gaps, which slightly favours short gaps;"
          " the pattern holds for the 2013 and 2018 Court of Audit reports.")


if __name__ == "__main__":
    main()
