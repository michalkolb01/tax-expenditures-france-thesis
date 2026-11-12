"""Parse the Voies et moyens tome II inventories, 2009-2026, into a panel.

Pipeline step, no thesis number directly (the panel feeds the termination
dataset of chapter 5, the matching of amendments in 1_data/1_3_parliamentary_corpus/2_amendments/ and
data/intermediate/tax_expenditures_panel_2009_2026.xlsx, built by
03_build_panel_xlsx.py).

Two eras, two formats:
- 2020-2026: the DGFiP spreadsheets. Four sheets (Références juridiques,
  Chiffrages, Bénéficiaires, Echéances) joined on measure number and
  edition. Leading zeros lost by Excel are restored.
- 2009-2019: PDF only. Each measure is the block of labelled fields from
  its six-digit number to the next one; a block counts only if it carries
  a descriptive field label (Réf., Création/modification, PLF de
  déclassement, Fin du fait générateur).
Legal references are reduced to article numbers (column `articles`,
"|"-separated) by split_refs(), which is unit-tested on load.

Check: the 2020 PDF is parsed with a reader for the newer layout and
compared with the 2020 spreadsheet (468 measures in both; creation year
468/468; beneficiary count 214/214 where both present; legal articles
457/468).

Also parses the "BILAN DES MESURES" section at the start of each 2009-2019
edition (suppressions/creations/increases/reductions, voted and proposed,
with the legal instrument).

Inputs
    data/raw/vmt_tome2/vm_2009.pdf ... vm_2026.pdf
    data/raw/vmt_tome2/vm_2020.xlsx ... vm_2024.xlsx, vm_2025.xls, vm_2026.xls
Outputs
    data/intermediate/vm_2009_2019.parquet      6,018 rows, 718 measures
                                                (one row per measure-year)
    data/intermediate/vm_2020_2026.parquet      3,285 rows, 577 measures
    data/intermediate/vm_bilan_2009_2019.csv    372 rows, 226 measures
Needs
    pip install pypdf pandas pyarrow openpyxl xlrd   (xlrd for the .xls)

Source
    Master Thesis_3 Tome II (3_TomeII.ipynb), cells 2 (setup), 4
    (split_refs), 6 (spreadsheet years), 8 (join, articles), 10 (PDF
    years), 12 (2020 PDF vs spreadsheet check), 14 (save the parquets),
    19 (bilan -> vm_bilan_2009_2019.csv), 23 (final rewrite of the
    `articles` column of both parquets with the final split_refs).

    Dropped: cell 16 (Step 7, membership of the 215 condemned measures per
    year -> survival_curve.csv) and cell 21 (Step 9, legislative action on
    the condemned measures -> suppressions_proposed.csv). Both are
    descriptive; survival_curve.csv is read by no later notebook, and
    suppressions_proposed.csv was exploratory and is not used downstream.

Caveats
    - The raw folder was raw/voies_et_moyens/ in the notebook; it is
      data/raw/vmt_tome2/ here, as in data/README.md (same file names).
    - Cell 23 was run in a later session after split_refs had been
      extended (it reapplies the final split_refs to the saved parquets).
      Run in order here, cell 23 changes nothing; it is kept so the
      parquets are by construction those of the final rewrite.
    - The notebook's Result text says legal articles agree for 455/468 in
      2020; the cell output (with the final split_refs) says 457/468.
    - 2009 lists fewer measures (511) than later editions: a coverage
      effect of that edition, not attrition (88 measures first appear in
      2010).
    - In 2016 only 424 of 525 PDF measures have a parsed legal reference
      (about 500 in other years).
    - From 2020 the information of the bilan is in the `motif` column of
      the Echéances sheet; vm_bilan covers 2009-2019 only.
"""
import collections
import re
import sys
from pathlib import Path

import pandas as pd
import pypdf

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

VM = RAW / "vmt_tome2"
DATA = INTERMEDIATE

# ---------------------------------------------------------------------------
# Step 1 - legal references (cell 4)
# ---------------------------------------------------------------------------
# Longest suffixes first: Python alternation takes the first match, so
# "quater" would otherwise swallow "quaterdecies".
SUF = ("quaterdecies|quindecies|sexdecies|septdecies|octodecies|novodecies|"
       "quatervicies|quinvicies|sexvicies|septvicies|octovicies|novovicies|"
       "undecies|duodecies|terdecies|tervicies|unvicies|duovicies|"
       "quinquies|septies|sexies|octies|nonies|decies|vicies|tricies|"
       "quater|bis|ter")


def norm_art(s):
    return re.sub(r"[‐‑‒–—]", "-", str(s)).strip()


def split_refs(s):
    """A reference string -> the article numbers it contains."""
    if pd.isna(s) or str(s) == "nan":
        return []
    out = []
    for part in re.split(r"\s*(?:,|\bet\b)\s*", norm_art(s)):
        part = re.sub(r"^[#\s]+", "", part)
        part = re.sub(r"^[IVXLC]+\s+(?:du|de la|de l'|d')\s*", "", part, flags=re.I)
        part = re.sub(r"^(?:article|art\.)\s*", "", part, flags=re.I)
        if re.match(r"^\d{1,2}\s*°", part) or re.match(r"^[a-z](\s|$|\))", part):
            continue
        if re.fullmatch(r"\d{1,2}", part):
            continue
        part = re.sub(r"[-\s]\d{1,2}\s*°.*$", "", part)
        m = re.match(rf"^((?:L\.|R\.|D\.)?\s?\d+(?:-\d+)*(?:-[a-z])?"
                     rf"(?:\s+(?:{SUF}))*(?:\s+[A-Z]\b)?"
                     rf"(?:\s+(?:bis|ter|quater))?)", part)
        if m:
            out.append(re.sub(r"\s+", " ", m.group(1)).strip())
    return out


assert split_refs("200 quaterdecies") == ["200 quaterdecies"]
assert split_refs("790 A bis") == ["790 A bis"]
assert split_refs("199 sexvicies") == ["199 sexvicies"]
assert split_refs("# 279-0 bis") == ["279-0 bis"]
assert split_refs("220 sexies, 220 F") == ["220 sexies", "220 F"]
assert split_refs("794, 795-2°, 4°") == ["794", "795"]

# ---------------------------------------------------------------------------
# Step 2-3 - spreadsheet years 2020-2026 (cells 6, 8)
# ---------------------------------------------------------------------------
XLS_YEARS = {2020: "xlsx", 2021: "xlsx", 2022: "xlsx", 2023: "xlsx",
             2024: "xlsx", 2025: "xls", 2026: "xls"}

REFS = ["categorie", "sous_cat", "sous_sous_cat", "numero", "libelle",
        "norme", "code_ref", "reference"]
CHIFF = ["categorie", "sous_cat", "sous_sous_cat", "numero", "libelle",
         "realisation", "prevision_1", "prevision_2"]
BENEF = ["categorie", "sous_cat", "sous_sous_cat", "numero", "libelle",
         "nature", "nombre"]
ECH = ["categorie", "sous_cat", "sous_sous_cat", "numero", "libelle",
       "creation", "derniere_modif", "fin_fait_generateur",
       "fin_incidence", "suppression", "chgt_depuis_vm", "motif"]


def fix_code(s):
    """Restore the six-digit measure number Excel has mangled."""
    return s.astype(str).str.strip().str.split(".").str[0].str.zfill(6)


def read_sheet(path, sheet, cols, skip, year):
    df = pd.read_excel(path, sheet_name=sheet, header=None).iloc[skip:].copy()
    df = df.iloc[:, :len(cols)]
    df.columns = cols
    df["numero"] = fix_code(df["numero"])
    df["vm_year"] = year
    return df[df["numero"].str.match(r"^\d{6}$", na=False)]


def parse_spreadsheets():
    parts = collections.defaultdict(list)
    for y, ext in XLS_YEARS.items():
        p = VM / f"vm_{y}.{ext}"
        for key, (sheet, cols, skip) in {
            "refs":  ("Références juridiques", REFS,  2),
            "cost":  ("Chiffrages",            CHIFF, 3),
            "benef": ("Bénéficiaires",         BENEF, 2),
            "ech":   ("Echéances",             ECH,   4),
        }.items():
            parts[key].append(read_sheet(p, sheet, cols, skip, y))
        print(f"{y}: {len(parts['refs'][-1])} measures")

    X = {k: pd.concat(v, ignore_index=True) for k, v in parts.items()}

    vm = (X["refs"][["numero", "vm_year", "libelle", "norme", "code_ref", "reference"]]
          .merge(X["cost"][["numero", "vm_year", "realisation", "prevision_1", "prevision_2"]],
                 on=["numero", "vm_year"], how="left")
          .merge(X["benef"][["numero", "vm_year", "nature", "nombre"]],
                 on=["numero", "vm_year"], how="left")
          .merge(X["ech"][["numero", "vm_year", "creation", "derniere_modif",
                           "fin_fait_generateur", "fin_incidence", "suppression", "motif"]],
                 on=["numero", "vm_year"], how="left"))

    vm["articles"] = vm["reference"].map(lambda s: "|".join(split_refs(s)))
    vm["nombre"] = pd.to_numeric(vm["nombre"], errors="coerce")
    for c in ["realisation", "prevision_1", "prevision_2"]:
        vm[c] = pd.to_numeric(vm[c], errors="coerce")
    for c in vm.columns:
        if vm[c].dtype == object:
            vm[c] = vm[c].astype(str)

    assert vm["numero"].str.len().eq(6).all(), "a measure code lost its leading zero"
    print(f"{len(vm):,} rows, {vm['numero'].nunique()} distinct measures, "
          f"{vm['vm_year'].nunique()} editions")
    return vm


# ---------------------------------------------------------------------------
# Step 4 - PDF years 2009-2019 (cell 10)
# ---------------------------------------------------------------------------
BLOCK = re.compile(r"(?=\b\d{6}\s)")
VAL = r"(?:\d[\d\s]*|ε|nc|-|0)"

NEXT = (r"(?=\s+(?:Missions? et programmes?|Objectif|Bénéficiaires|"
        r"Méthode de chiffrage|Fiabilité|Création\s*/\s*modification|"
        r"Fin du fait générateur|Fin d.incidence budgétaire|"
        r"PLF de déclassement|Réf\.)\s*\w*\s*:|$)")

FIELDS = {
    "mission":      r"Mission et programme\s*:\s*(.*?)" + NEXT,
    "objectif":     r"Objectif\s*:\s*(.*?)" + NEXT,
    "benef_raw":    r"Bénéficiaires\s*(\d{4})?\s*:\s*(.*?)" + NEXT,
    "methode":      r"Méthode de chiffrage\s*:\s*(.*?)" + NEXT,
    "fiabilite":    r"Fiabilité\s*:\s*(.*?)" + NEXT,
    "creation":     r"Création\s*/\s*modification\s*:\s*(\d{4})\s*/\s*(\d{4})",
    "fin_fait":     r"Fin du fait générateur\s*:\s*(.*?)" + NEXT,
    "fin_incid":    r"Fin d.incidence budgétaire\s*:\s*(.*?)" + NEXT,
    "declassement": r"PLF de déclassement\s*:\s*(\d{4})",
    "reference":    r"Réf\.\s*\w*\s*:\s*(.*?)$",
}


def parse_vm_pdf(path, year):
    r = pypdf.PdfReader(path)
    blob = " ".join(re.sub(r"\s+", " ", p.extract_text() or "") for p in r.pages)
    blob = blob.replace("’", "'").replace("ʼ", "'")
    blob = re.sub(r"PLF \d{4}\s+\d+\s+Chiffrages des dépenses fiscales", " ", blob)
    blob = re.sub(r"Voies et Moyens II", " ", blob)

    rows = []
    for part in BLOCK.split(blob):
        if not re.match(r"^\d{6}\s", part):
            continue
        if not re.search(r"(Réf\.\s*\w*\s*:|Création\s*/\s*modification\s*:|"
                         r"PLF de déclassement\s*:|Fin du fait générateur\s*:)", part):
            continue

        code, body = part[:6], part[6:].strip()
        head = re.split(r"\s+(?:Mission(?:s)? et programme|Objectif|Bénéficiaires)", body)[0]
        nums = re.findall(rf"(?<![\d,])({VAL})(?=\s|$)", head)
        libelle = head
        for n in nums[-3:]:
            if n in libelle:
                libelle = libelle[:libelle.rfind(n)]

        row = {"numero": code, "vm_year": year,
               "libelle": re.sub(r"\s+", " ", libelle).strip(),
               "costs": "|".join(x.strip() for x in nums[-3:])}

        for name, pat in FIELDS.items():
            m = re.search(pat, body, re.S)
            if not m:
                continue
            if name == "creation":
                row["creation"], row["derniere_modif"] = m.group(1), m.group(2)
            elif name == "benef_raw":
                row["benef_year"] = m.group(1)
                row["benef_raw"] = re.sub(r"\s+", " ", m.group(2)).strip()
            else:
                row[name] = re.sub(r"\s+", " ", m.group(1)).strip()
        rows.append(row)
    return pd.DataFrame(rows)


def parse_pdfs():
    pdf_parts = []
    for y in range(2009, 2020):
        d = parse_vm_pdf(VM / f"vm_{y}.pdf", y)
        assert len(d) > 300, f"{y}: only {len(d)} measures — the format may differ"
        pdf_parts.append(d)
        print(f"{y}: {len(d):>4} measures, ref {d['reference'].notna().sum():>4}, "
              f"déclassé {d.get('declassement', pd.Series(dtype=str)).notna().sum():>3}")

    P = pd.concat(pdf_parts, ignore_index=True)
    P["articles"] = P["reference"].map(lambda s: "|".join(split_refs(s)))
    print(f"\n{len(P):,} rows, {P['numero'].nunique()} distinct measures")
    return P


# ---------------------------------------------------------------------------
# Step 5 - check the PDF reader against the 2020 spreadsheet (cell 12)
# ---------------------------------------------------------------------------
NEW_FIELDS = {
    "creation":  r"Création\s+(\d{4})",
    "modif":     r"Modification\s+(\d{4})",
    "fin_fait":  r"Fin du fait générateur\s+(.*?)(?=\s+(?:Fin d.incidence|Bénéficiaires|Fiabilité|Norme|Méthode|Référence|Mission)|$)",
    "benef_raw": r"Bénéficiaires\s+(.*?)(?=\s+(?:Fiabilité|Norme|Méthode|Référence|Mission)|$)",
    "reference": r"Référence\s+(?:code|livre|loi)[^\d]*?([\d].*?)(?=\s+Mission|$)",
}


def parse_vm_new(path, year):
    r = pypdf.PdfReader(path)
    blob = " ".join(re.sub(r"\s+", " ", p.extract_text() or "") for p in r.pages)
    blob = blob.replace("’", "'")
    rows = []
    for part in BLOCK.split(blob):
        if not re.match(r"^\d{6}\s", part) or "Impact budgétaire" not in part:
            continue
        row = {"numero": part[:6], "vm_year": year}
        for name, pat in NEW_FIELDS.items():
            m = re.search(pat, part[6:], re.S)
            if m:
                row[name] = re.sub(r"\s+", " ", m.group(1)).strip()
        rows.append(row)
    return pd.DataFrame(rows)


def check_2020(vm):
    p20 = parse_vm_new(VM / "vm_2020.pdf", 2020)
    x20 = vm[vm["vm_year"] == 2020]
    both = set(p20["numero"]) & set(x20["numero"])
    print(f"measures — PDF {len(p20)}, xlsx {len(x20)}, in both {len(both)}")

    m = p20.merge(x20[["numero", "creation", "nombre", "reference"]],
                  on="numero", suffixes=("_pdf", "_xls"))

    a = pd.to_numeric(m["creation_pdf"], errors="coerce")
    b = pd.to_numeric(m["creation_xls"], errors="coerce")
    print(f"creation year agrees: {((a == b) | (a.isna() & b.isna())).sum()}/{len(m)}")

    n_pdf = pd.to_numeric(m["benef_raw"].str.extract(r"([\d\s]+)")[0]
                          .str.replace(" ", ""), errors="coerce")
    d = (n_pdf - m["nombre"]).abs()
    print(f"beneficiary count agrees: {(d == 0).sum()}/{d.notna().sum()} where both present")

    same = m.apply(lambda r: set(split_refs(r["reference_pdf"]))
                   == set(split_refs(r["reference_xls"])), axis=1)
    print(f"legal articles agree: {same.sum()}/{len(m)}")


# ---------------------------------------------------------------------------
# Step 8 - the bilan of legislative changes, 2009-2019 (cell 19)
# ---------------------------------------------------------------------------
SECTIONS = [
    "Suppressions votées", "Suppressions proposées",
    "Créations votées", "Créations proposées",
    "Augmentations votées", "Augmentations proposées",
    "Diminutions votées", "Diminutions proposées",
    "Réductions votées", "Réductions proposées",
    "Suppressions consécutives",
]
SEC_RE = re.compile("(" + "|".join(re.escape(s) for s in SECTIONS) + ")", re.I)
ROW_RE = re.compile(r"\b([A-Z]{2,8})\s+(\d{6})\s+(.*?)"
                    r"((?:Loi|Projet de loi|Décision|Ordonnance|Article|LFR|"
                    r"\d(?:ème|er)? loi)[^0-9]*?(?:\d{4})?[^A-Z]*?)"
                    r"(?=\s+(?:[A-Z]{2,8}\s+\d{6}|$))", re.S)


def parse_bilan(path, year):
    r = pypdf.PdfReader(path)
    blob = " ".join(re.sub(r"\s+", " ", p.extract_text() or "") for p in r.pages[:45])
    blob = blob.replace("’", "'")
    i = blob.find("BILAN DES MESURES")
    if i < 0:
        return pd.DataFrame()
    seg = blob[i:i + 20000]

    pos = [(m.start(), m.group(1)) for m in SEC_RE.finditer(seg)]
    pos.append((len(seg), None))

    rows = []
    for (start, label), (end, _) in zip(pos, pos[1:]):
        for r_ in ROW_RE.finditer(seg[start:end]):
            rows.append({"vm_year": year, "section": label,
                         "impot": r_.group(1), "numero": r_.group(2),
                         "libelle": re.sub(r"\s+", " ", r_.group(3)).strip(),
                         "fondement": re.sub(r"\s+", " ", r_.group(4)).strip()})
    return pd.DataFrame(rows)


def build_bilan():
    bilans = []
    for y in range(2009, 2020):
        d = parse_bilan(VM / f"vm_{y}.pdf", y)
        # the cost figures trail the legal reference; drop them
        d["fondement"] = d["fondement"].str.replace(
            r"(?:\s+(?:\d[\d\s]*|Epsilon|ε|nc|-))+$", "", regex=True).str.strip()
        bilans.append(d)
        print(f"{y}: {len(d):>3} rows")

    B = pd.concat(bilans, ignore_index=True)
    B.to_csv(DATA / "vm_bilan_2009_2019.csv", index=False)
    print(f"\n{len(B)} rows, {B['numero'].nunique()} distinct measures")
    print(B["section"].value_counts().to_string())


# ---------------------------------------------------------------------------
# Final articles rewrite (cell 23)
# ---------------------------------------------------------------------------
def rewrite_articles():
    P = pd.read_parquet(DATA / "vm_2009_2019.parquet")
    vm = pd.read_parquet(DATA / "vm_2020_2026.parquet")
    P["articles"] = P["reference"].map(lambda s: "|".join(split_refs(s)))
    vm["articles"] = vm["reference"].map(lambda s: "|".join(split_refs(s)))
    P.to_parquet(DATA / "vm_2009_2019.parquet", index=False)
    vm.to_parquet(DATA / "vm_2020_2026.parquet", index=False)

    both = pd.concat([P, vm])
    for c in ["110250", "730213"]:   # expected: 199 sexvicies, 279-0 bis
        r = both[both["numero"] == c].sort_values("vm_year").tail(1)
        print(c, "->", r.iloc[0]["articles"])
    print("rewritten")


def main():
    print(sorted(p.name for p in VM.iterdir()))

    vm = parse_spreadsheets()
    P = parse_pdfs()
    check_2020(vm)

    # Step 6 - save (cell 14)
    for c in P.columns:
        if P[c].dtype == object:
            P[c] = P[c].astype(str)
    P.to_parquet(DATA / "vm_2009_2019.parquet", index=False)
    vm.to_parquet(DATA / "vm_2020_2026.parquet", index=False)
    print(f"2009–2019: {len(P):,} rows")
    print(f"2020–2026: {len(vm):,} rows")
    print(f"{P['vm_year'].nunique() + vm['vm_year'].nunique()} editions in total")

    build_bilan()
    rewrite_articles()


if __name__ == "__main__":
    main()
