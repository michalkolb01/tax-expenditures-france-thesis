"""Section 6.2.2 - Counts of references to the 2011 evaluation.

Input
    data/evaluation2011_candidates_RAW_reviewed.csv
        The 218 candidates from 01_search_2011_report.py, each read in full
        and coded:
          keep = 1  genuine reference to the 2011 evaluation (58)
          keep = 0  not a reference (157): other bodies, other reports
          keep = ?  uncertain (3), excluded from the counts; 'note' says why
          use       how the speaker uses the reference (genuine rows only):
                    'support removal / refuse extension', 'defend measure',
                    'report as a whole'
          note      reasoning for doubtful cases

Reproduces (section 6.2.2)
    - 58 references between October 2011 and 2026, a minimum given the limits
      of any search.
    - By period: 12 in October-December 2011; 28 in 2012-2016; 16 in
      2017-2021; 2 in 2022-2026 (both in 2024).
    - Use: 36 support removing or restricting a measure (about 60%), 15
      defend a measure, 7 concern the report as a whole.
    - Known-item test: the 17 October 2013 school-fee reference is among the
      genuine references.
Outputs
    tables/ch6_2_2_references_by_year.csv, tables/ch6_2_2_references_by_period_use.csv
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
TAB = HERE / "tables"
TAB.mkdir(exist_ok=True)


def main():
    b = pd.read_csv(HERE / "data" / "evaluation2011_candidates_RAW_reviewed.csv", dtype=str)
    print("Candidates:", len(b), "| coding:", b.keep.value_counts().to_dict())
    print("\nUncertain cases (excluded):")
    print(b[b.keep == "?"][["date", "note"]].to_string(index=False))

    k = b[b.keep == "1"].copy()
    k["year"] = k["year"].astype(int)
    k["period"] = pd.cut(k.year, [2010, 2011, 2016, 2021, 2026],
                         labels=["Oct-Dec 2011", "2012-2016", "2017-2021", "2022-2026"])
    print(f"\nGenuine references: {len(k)}")
    by_year = k.year.value_counts().sort_index()
    print(by_year.to_string())
    by_year.to_csv(TAB / "ch6_2_2_references_by_year.csv")

    t = pd.crosstab(k.period, k.use, margins=True)
    print("\nBy period and use:")
    print(t.to_string())
    t.to_csv(TAB / "ch6_2_2_references_by_period_use.csv")
    share = (k.use == "support removal / refuse extension").mean()
    print(f"\nShare supporting removal or restriction: {share:.0%}")

    known = k[k.date.str.startswith("20131017")]
    print("Known item (17 Oct 2013) among genuine references:", len(known) > 0)


if __name__ == "__main__":
    main()
