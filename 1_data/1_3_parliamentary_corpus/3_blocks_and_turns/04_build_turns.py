"""Speaking turns linked to measures (turns.parquet).

Builds the corpus of speaking turns: the texts spoken in the plenary and
committee amendment blocks that were linked to a tax-expenditure measure
(through the amendment discussed). One row per turn longer than 200
characters, with the speaker as printed, the text, the measure, the venue
(floor or committee) and the 2011 evaluation score of the measure. This is a
corpus of texts linked to measures through amendments, not classified data:
the turns carry no position, argument or other coding.

Steps
    1. Floor turns (cell 75): paragraphs of debate_blocks.parquet whose
       (sitting uid, amendment) is a block of debate_matched.parquet,
       deduplicated on (block, ordre), kept if over 200 characters (cell 82).
    2. Committee turns (cell 76): the text of each committee_matched block is
       split on speaker headings ("M. ..." / "Mme ...") and turns over 200
       characters are kept (truncated to 3,000 characters).
    3. Measures (cells 80, 82, 84): floor turns get the measure of their block
       (sitting|amendment key, cell 84); committee turns get the measure of
       their amendment uid (map built in cell 82); score from
       measures_with_bands.csv (cell 80).
    4. Assembly and save (cell 85).

Inputs
    INTERMEDIATE / "debate_blocks.parquet", "debate_matched.parquet"  (01_plenary_15_17.py)
    INTERMEDIATE / "committee_matched.parquet"                        (03_committee.py)
    INTERMEDIATE / "measures_with_bands.csv"                          (1_data/1_3_parliamentary_corpus/2_amendments, matching step)
Outputs
    INTERMEDIATE / "turns.parquet"   columns orateur, texte, measure, venue, score

Thesis numbers
    Pipeline step, no thesis number directly. Final run: 5,340 turns on 129
    measures (floor 1,623, committee 3,717; every turn has a measure and a
    score in the final file).

Source
    Master Thesis_7 Committee Debates (7_Committee.ipynb), cells 75, 76, 80
    (g only), 82 (fl_t, cm_t and the uid -> measure map only), 84, 85. Cells
    74, 77-79, 81, 83 are exploration or superseded (role/groupe columns of
    cells 77 and 79 are not in the final file).

Changes from the notebook
    Drive paths replaced by src/config.py; the lines of cells 80 and 82 that
    filled an intermediate TURNS frame (overwritten in cell 85) are dropped.

Known caveats
    - Legislature 14 is not included (debate_matched_14 and
      committee_matched_14 are not used).
    - No uid or date column: a turn cannot be traced back to its amendment
      or sitting from turns.parquet alone.
    - The row index of turns.parquet is the key used by the (archived)
      argument files (column idx); do not reorder it.
    - Committee turns are cut from the block texts of committee_matched
      (improved CLOSE), not from committee_blocks.parquet; see 03_committee.py.
    - Turns with no measure would be kept (no filter); in the final file
      there are none.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

DATA = INTERMEDIATE

# cell 76
SPK = re.compile(r"(M\.|Mme)\s+((?:le |la )?[^.]{2,60}?)\s*\.\s")


def main():
    # cell 75
    fl = pd.read_parquet(DATA / "debate_matched.parquet")
    cm = pd.read_parquet(DATA / "committee_matched.parquet")
    keep_blocks = set(fl["seance"] + "|" + fl["amendement"].astype(str))

    D = pd.read_parquet(DATA / "debate_blocks.parquet")
    D["k"] = D["uid"].astype(str) + "|" + D["amendement"].astype(str)
    t = D[D["k"].isin(keep_blocks)].drop_duplicates(["k", "ordre"])
    print(f"{len(t):,} turns in matched floor blocks")

    # cell 76
    rows = []
    for _, r in cm.iterrows():
        txt = str(r["texte"])
        parts = SPK.split(txt)
        # parts alternates: [pre, title, name, text, title, name, text, ...]
        for i in range(1, len(parts) - 2, 3):
            speech = parts[i + 2].strip()
            if len(speech) > 200:
                rows.append({"measure": r["measure"], "uid": r["uid"],
                             "venue": "committee", "cr": r.get("cr"),
                             "orateur": f"{parts[i]} {parts[i+1]}".strip(),
                             "texte": speech[:3000]})
    CT = pd.DataFrame(rows)
    print(f"{len(CT):,} committee turns over 200 chars")

    # cell 80
    g = pd.read_csv(DATA / "measures_with_bands.csv", dtype={"code": str})

    # cell 82
    fl_t = (t[t["texte"].str.len() > 200][["uid", "amendement", "orateur", "texte"]]
            .copy().assign(venue="floor"))
    cm_t = CT[["uid", "orateur", "texte"]].copy().assign(venue="committee")
    print(f"floor {len(fl_t):,}, committee {len(cm_t):,}")
    m = pd.concat([fl[["uid", "measure"]], cm[["uid", "measure"]]]).drop_duplicates("uid")

    # cell 84
    fl["k"] = fl["seance"].astype(str) + "|" + fl["amendement"].astype(str)
    fl_t["k"] = fl_t["uid"].astype(str) + "|" + fl_t["amendement"].astype(str)
    fl_t["measure"] = fl_t["k"].map(fl.drop_duplicates("k").set_index("k")["measure"])
    print("floor turns with a measure:", fl_t["measure"].notna().sum())

    # cell 85
    fl_t2 = fl_t[["orateur", "texte", "measure"]].assign(venue="floor")
    cm_t2 = cm_t[["orateur", "texte"]].assign(venue="committee")
    cm_t2["measure"] = cm_t["uid"].map(m.set_index("uid")["measure"])

    TURNS = pd.concat([fl_t2, cm_t2], ignore_index=True)
    TURNS["score"] = TURNS["measure"].map(g.set_index("code")["score"])

    print(f"{len(TURNS):,} turns, {TURNS['measure'].nunique()} measures")
    print(pd.crosstab(TURNS["score"], TURNS["venue"]).to_string())
    TURNS.to_parquet(DATA / "turns.parquet", index=False)


if __name__ == "__main__":
    main()
