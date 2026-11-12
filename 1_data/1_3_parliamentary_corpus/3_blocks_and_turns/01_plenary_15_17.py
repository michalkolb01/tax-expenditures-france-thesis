"""Plenary debates, legislatures 15-17 (2017-2026): amendment blocks and their link to measures.

Parses every sitting record (compte rendu) of the Assembly open data, cuts each
sitting into blocks (one block = the paragraphs that discuss one amendment,
ending with the paragraph that records its outcome), extracts the commission
and government opinions given in each block, and links each block to one
amendment of the amendment dataset, and through it to a tax-expenditure
measure. The result is a corpus of texts linked to measures through
amendments; nothing here classifies the content of the debates.

Steps
    1. Legislature 17: parse_seance (cell 9) -> segment v2 (cells 10 + 12:
       OUTCOME codes from cell 10, walk back to the nearest opener, capped at
       60 paragraphs) -> extract_avis (cell 14). Writes debate_blocks_17.parquet
       and debate_avis_17.parquet (cell 15).
    2. Legislatures 15 and 16 with the same functions (cell 36), appended to
       legislature 17; columns cast to str and dates parsed (cell 37).
    3. Repair of the legislature-17 sitting dates in debate_avis.parquet from
       the sitting uid (cell 43).
    4. Matching blocks to amendments (cells 38 + 44): same number and
       legislature, filed 0-60 days before the sitting, amendment on the bill
       most often matched in that sitting, block resolving to exactly one
       amendment; then kept only if the amendment is in
       amendments_classified.csv (amendments linked to a measure).

Inputs
    RAW / "an_portal" / "debats_leg15.xml.zip", "debats_leg16.xml.zip",
        "debats_leg17.xml.zip"      Assembly open data, sitting records
    INTERMEDIATE / "amendments_15_17.parquet"    (1_data/1_3_parliamentary_corpus/2_amendments)
    INTERMEDIATE / "amendments_classified.csv"   (1_data/1_3_parliamentary_corpus/2_amendments; called
        classified_combined.csv in the notebook)
Outputs
    INTERMEDIATE / "debate_blocks_17.parquet"   paragraphs in amendment blocks, leg 17
    INTERMEDIATE / "debate_avis_17.parquet"     one row per block, leg 17
    INTERMEDIATE / "debate_blocks.parquet"      paragraphs in amendment blocks, leg 15-17
    INTERMEDIATE / "debate_avis.parquet"        one row per block with the opinions, leg 15-17
    INTERMEDIATE / "debate_matched.parquet"     blocks linked to one amendment and a measure

Thesis numbers
    Pipeline step, no thesis number directly (feeds 04_build_turns.py).

Source
    Master Thesis_6 Debates (6_Debates.ipynb), cells 9, 10 (OUTCOME only),
    12, 14, 15, 36, 37, 38, 43, 44. Cells 0-8, 11, 13, 16-35, 39-42 and 45-50
    are exploration, diagnostics or superseded versions and are not kept.
    finance_dossiers.csv (cell 22) has no writer and was only used in dead
    cells; it is dropped.

Changes from the notebook
    - Drive paths replaced by src/config.py; the notebook state carried from
      cell to cell is passed explicitly between functions.
    - In the notebook, cell 16 (dead, exploratory) had converted the
      legislature-17 dates to datetime before cell 36 appended legislatures
      15-16; cell 37 then turned those dates into NaT, and cell 43 repaired
      them from the sitting uid. Cell 16 is not run here, so the leg-17 dates
      are already correct after step 2; the repair (step 3) is kept as in the
      notebook and is then a no-op.

Known caveats
    - Only blocks that resolve to exactly one amendment are kept; blocks on
      bills where the same number is used by several amendments are dropped.
    - Blocks are delimited by the outcome paragraph; the walk-back to the
      opener is capped at 60 paragraphs.
    - Cell 37 casts every object column of debate_avis to str, so missing
      opinions are stored as the string "None".
"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

AN = RAW / "an_portal"
DATA = INTERMEDIATE

# cell 10 (only the outcome codes are kept; its segment() was replaced in cell 12)
OUTCOME = {"ADOP_ADT", "REJET_ADT", "RETRAIT_ADT", "SCRUT_PUB_ADT_1_9",
           "ADT_SORTS_DIRECT_1_10", "ADT_SORTS_DIRECT_1_20", "SORT_SS_ADT_1_70"}

# cell 12
OPENERS = {"DISC_ARTICLES_3_1", "DISC_ARTICLES_3_4_1"}

# cell 14
AVIS_C = re.compile(r"avis de la commission", re.I)
AVIS_G = re.compile(r"avis du [Gg]ouvernement", re.I)


# cell 9
def parse_seance(xml_bytes):
    r = ET.fromstring(xml_bytes)
    NS = r.tag.split("}")[0] + "}" if "}" in r.tag else ""

    def g(tag):
        e = r.find(f".//{NS}{tag}")
        return e.text if e is not None else None

    meta = {"uid": g("uid"), "date": g("dateSeance"),
            "legislature": g("legislature"), "seance": g("numSeance")}

    rows = []
    for p in r.iter(f"{NS}paragraphe"):
        a = p.attrib
        nom = p.find(f".//{NS}orateur/{NS}nom")
        idt = p.find(f".//{NS}orateur/{NS}id")
        txt = p.find(f"{NS}texte")
        rows.append({
            **meta,
            "ordre": int(a.get("ordre_absolu_seance") or 0),
            "grammaire": a.get("code_grammaire"),
            "valeur": (a.get("valeur") or "").strip(),
            "type_debat": a.get("type_debat"),
            "orateur": nom.text if nom is not None else None,
            "orateur_id": idt.text if idt is not None else None,
            "texte": " ".join("".join(txt.itertext()).split()) if txt is not None else "",
        })
    return pd.DataFrame(rows)


# cell 12 (segment v2)
def segment(d, max_len=60):
    d = d.sort_values("ordre").reset_index(drop=True)
    d["amendement"] = None
    for i, r in d.iterrows():
        if r["grammaire"] not in OUTCOME:
            continue
        num = re.sub(r"\D", "", r["valeur"] or "")
        if not num:
            continue
        # walk back to the nearest opener, capped
        j = i
        while j > 0 and (i - j) < max_len:
            if d.loc[j - 1, "grammaire"] in OUTCOME:
                break
            if d.loc[j, "grammaire"] in OPENERS and j < i:
                break
            j -= 1
        d.loc[j:i, "amendement"] = num
    return d


# cell 14
def extract_avis(bloc):
    bloc = bloc.sort_values("ordre").reset_index(drop=True)
    out = {"avis_commission": None, "qui_commission": None,
           "avis_gouvernement": None, "qui_gouvernement": None}
    for i, r in bloc.iterrows():
        t = r["texte"] or ""
        nxt = bloc.iloc[i + 1] if i + 1 < len(bloc) else None
        if nxt is None:
            continue
        if AVIS_C.search(t) and out["avis_commission"] is None:
            out["avis_commission"] = nxt["texte"]
            out["qui_commission"] = nxt["orateur"]
        elif AVIS_G.search(t) and out["avis_gouvernement"] is None:
            out["avis_gouvernement"] = nxt["texte"]
            out["qui_gouvernement"] = nxt["orateur"]
    return out


# cell 15
def run_leg17():
    rows, avis = [], []
    with zipfile.ZipFile(AN / "debats_leg17.xml.zip") as f:
        names = [x for x in f.namelist() if "/compteRendu/" in x]
        for k, n in enumerate(names):
            try:
                d = segment(parse_seance(f.read(n)))
            except Exception:
                continue
            bb = d[d["amendement"].notna()]
            if not len(bb):
                continue
            rows.append(bb)
            for num, bloc in bb.groupby("amendement"):
                avis.append({"seance": bloc["uid"].iloc[0],
                             "date": bloc["date"].iloc[0][:8],
                             "legislature": bloc["legislature"].iloc[0],
                             "amendement": num,
                             "n_paragraphes": len(bloc),
                             "type_debat": bloc["type_debat"].mode().iloc[0]
                             if bloc["type_debat"].notna().any() else None,
                             **extract_avis(bloc)})
            if k % 100 == 0:
                print(f"  {k}/{len(names)}")

    D = pd.concat(rows, ignore_index=True)
    A = pd.DataFrame(avis)
    print(f"\n{len(A):,} amendment blocks across {A['seance'].nunique()} sittings")
    print(f"  commission avis: {A['avis_commission'].notna().sum():,}")
    print(f"  government avis: {A['avis_gouvernement'].notna().sum():,}")

    D.to_parquet(DATA / "debate_blocks_17.parquet", index=False)
    A.to_parquet(DATA / "debate_avis_17.parquet", index=False)
    return D, A


# cell 36
def run_leg(leg):
    rows, avis = [], []
    with zipfile.ZipFile(AN / f"debats_leg{leg}.xml.zip") as f:
        names = [x for x in f.namelist() if "/compteRendu/" in x]
        for k, n in enumerate(names):
            try:
                d = segment(parse_seance(f.read(n)))
            except Exception:
                continue
            bb = d[d["amendement"].notna()]
            if not len(bb):
                continue
            rows.append(bb)
            for num, bloc in bb.groupby("amendement"):
                avis.append({"seance": bloc["uid"].iloc[0],
                             "date": bloc["date"].iloc[0][:8],
                             "legislature": bloc["legislature"].iloc[0],
                             "amendement": num,
                             "n_paragraphes": len(bloc),
                             **extract_avis(bloc)})
            if k % 200 == 0:
                print(f"  leg {leg}: {k}/{len(names)}")
    return pd.concat(rows, ignore_index=True), pd.DataFrame(avis)


def build_all(D, A):
    # cell 36
    D15, A15 = run_leg(15)
    D16, A16 = run_leg(16)
    print(f"\nleg 15: {len(A15):,} blocks")
    print(f"leg 16: {len(A16):,} blocks")
    D = pd.concat([D, D15, D16], ignore_index=True)
    A = pd.concat([A, A15, A16], ignore_index=True)

    # cell 37
    A["date"] = A["date"].astype(str).str.slice(0, 8)
    A["date"] = pd.to_datetime(A["date"], format="%Y%m%d", errors="coerce")
    for c in A.columns:
        if A[c].dtype == object:
            A[c] = A[c].astype(str)

    D.to_parquet(DATA / "debate_blocks.parquet", index=False)
    A.to_parquet(DATA / "debate_avis.parquet", index=False)
    print(f"{len(A):,} blocks across {A['seance'].nunique():,} sittings")
    print(A.groupby("legislature").size().to_string())
    print(f"with a commission avis: {(A['avis_commission'] != 'None').sum():,}")
    print(f"with a government avis: {(A['avis_gouvernement'] != 'None').sum():,}")


def repair_dates_and_match():
    # cell 38
    A = pd.read_parquet(DATA / "debate_avis.parquet")
    am = pd.read_parquet(DATA / "amendments_15_17.parquet").drop_duplicates("uid")
    cl = pd.read_csv(DATA / "amendments_classified.csv", dtype={"measure": str})
    A["date"] = pd.to_datetime(A["date"], errors="coerce")
    am["date_depot"] = pd.to_datetime(am["date_depot"], errors="coerce")
    print(f"{len(A):,} blocks, {len(am):,} amendments, {len(cl):,} classified")

    # cell 43: repair leg-17 dates from the sitting uid
    D = pd.read_parquet(DATA / "debate_blocks.parquet")
    dates = (D[D["legislature"] == "17"][["uid", "date"]]
             .drop_duplicates("uid").set_index("uid")["date"])
    mask = A["legislature"] == "17"
    A.loc[mask, "date"] = pd.to_datetime(
        A.loc[mask, "seance"].map(dates).astype(str).str.slice(0, 8),
        format="%Y%m%d", errors="coerce")
    print("NaT remaining:", A[mask]["date"].isna().sum())
    A.to_parquet(DATA / "debate_avis.parquet", index=False)

    # cell 44
    cand = A.merge(am[["uid", "numero", "legislature", "texte_ref", "date_depot", "sort"]],
                   left_on=["amendement", "legislature"],
                   right_on=["numero", "legislature"], how="inner")
    cand["lag"] = (cand["date"] - cand["date_depot"]).dt.days
    cand = cand[(cand["lag"] >= 0) & (cand["lag"] <= 60)]

    # identify each sitting's bill from the numbers mentioned that day
    bill = (cand.groupby(["seance", "texte_ref"]).size().rename("n").reset_index()
            .sort_values("n", ascending=False).drop_duplicates("seance"))
    cand = cand.merge(bill[["seance", "texte_ref"]].rename(columns={"texte_ref": "b"}),
                      on="seance")
    tight = cand[cand["texte_ref"] == cand["b"]]

    # keep only blocks resolving to exactly one amendment
    u = tight.groupby(["seance", "amendement"])["uid"].nunique()
    keep = set(u[u == 1].index)
    tight = tight[tight.set_index(["seance", "amendement"]).index.isin(keep)]

    m = tight.merge(cl[["uid", "measure", "categorie"]], on="uid")
    print(f"{len(tight):,} unambiguous blocks")
    print(f"{len(m):,} reach a classified amendment, {m['measure'].nunique()} measures\n")
    print(m.groupby("legislature").size().to_string())
    m.to_parquet(DATA / "debate_matched.parquet", index=False)


def main():
    D, A = run_leg17()
    build_all(D, A)
    repair_dates_and_match()


if __name__ == "__main__":
    main()
