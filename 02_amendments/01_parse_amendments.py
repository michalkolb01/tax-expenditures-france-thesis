"""Parse the Assemblée nationale amendment open data and label finance bills.

Reads the amendment archives of legislatures 14 to 17, reduces both formats
to one table (one row per amendment), extracts the tax-code articles cited
in each amendment, and labels the amendments filed on finance bills
(projets de loi de finances) with the budget year of the bill.

- Legislatures 15-17: one namespaced XML file per amendment inside each
  archive (amendements_leg15/16/17.xml.zip).
- Legislature 14: one large XML holding every amendment, with different
  field names and no namespace, streamed with iterparse.

Article citations are extracted two ways: `articles_strict` requires the tax
code (CGI or CIBS) to be named within 80 characters after the article;
`articles_loose` takes every citation in an amendment that mentions the code
anywhere. The article-40 compensation clause ("La perte de recettes ... est
compensée ...", which cites articles 575, 575 A and 1665 bis) is removed
before extraction (legislatures 15-17 only, as in the notebook).

Finance-bill labels come from the dossiers archives (document titles for
leg 14, dossier titles for legs 15-17): `is_finance` (title contains
"projet de loi de finances" but not "financement de la sécurité sociale"),
`plf_year` ("pour YYYY" in the title), `is_49_3`. This is a label, not a
filter.

Inputs
    data/raw/an_portal/amendements_leg14.xml.zip
    data/raw/an_portal/amendements_leg15.xml.zip, ..._leg16..., ..._leg17...
    data/raw/an_portal/dossiers_leg14.xml.zip
    data/raw/an_portal/dossiers_leg15.xml.zip, ..._leg16..., ..._leg17...
    (downloaded by 00_acquisition/, see manifest_an_portal.csv)
Outputs
    data/intermediate/amendments_14.parquet     (167,420 amendments, 2012-07-05 to 2017-02-16)
    data/intermediate/amendments_15_17.parquet  (598,947 amendments parsed; see caveat)
Reproduces
    Pipeline step, no thesis number directly. Counts printed in the notebook:
    leg 14: 167,420 amendments, 13,781 with a strict citation; legs 15-17:
    598,947 amendments, 0 parse errors, 30,912 with a strict citation;
    90,729 finance-bill amendments (PLF 2021-2026), 0 under 49.3.
Source
    Master Thesis_1 Scraping.ipynb, cells 4 (setup), 26 (cleaning and article
    extraction), 28 (parse legs 15-17), 30 (parse leg 14), 32 (leg 14 labels),
    34 (legs 15-17 labels).
Changes from the notebook
    - Paths through src/config.py; the notebook's RAW (raw/an_portal) is
      RAW / "an_portal" here.
    - The notebook cached the parsed frames (cells 28 and 30), then re-read and
      re-saved them after labelling (cells 32 and 34). Re-running the labelling
      on an already labelled cache gives `title_x`/`title_y` columns and breaks.
      Here labelling always runs on the freshly parsed frame and each file is
      written once. No parse cache.
Known caveats
    - Legs 15-17: the merge with dossier titles (cell 34) inflated the saved
      file from 598,947 to 648,213 rows in the thesis run: duplicated
      amendments (probably because titles are deduplicated within each
      legislature but not after concatenating the three, so a dossier key
      present in several archives joins more than once; not verified). Kept as
      it was; downstream steps deduplicate on `uid` where it matters.
      02_match_articles.py reads the file as written here.
    - Legs 15-17 labelling finds finance bills for PLF 2021-2026 only: the
      leg-15 bills for 2018-2020 get no label (cause not investigated). 0 bills
      found under 49.3. The labels are not used by the matching.
    - Leg 14 amendments do not have the compensation clause removed before
      article extraction (as in the notebook).
Run time
    About twenty minutes (legs 15-17 archives: ~600,000 XML files).
"""
import html
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

AN = RAW / "an_portal"


# ---------------------------------------------------------------------------
# Cleaning and article extraction (cell 26)
# ---------------------------------------------------------------------------
def clean(s):
    """Unescape twice, strip tags, normalise whitespace."""
    if not s:
        return ""
    s = html.unescape(html.unescape(s))
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


GAGE = re.compile(
    r"(?:La perte|Les pertes|La perte éventuelle|Cette perte)\s+de\s+recettes.*?$",
    re.I | re.S)


def strip_gage(s):
    """Remove the article-40 compensation clause, which cites articles 575,
    575 A and 1665 bis in almost every amendment that costs money."""
    return re.sub(r"\s+", " ", GAGE.sub("", s or "")).strip()


# Longest suffixes first: Python alternation takes the first match, so
# "quater" would otherwise swallow "quaterdecies".
SUF = ("quaterdecies|quindecies|sexdecies|septdecies|octodecies|novodecies|"
       "quatervicies|quinvicies|sexvicies|septvicies|octovicies|novovicies|"
       "undecies|duodecies|terdecies|tervicies|unvicies|duovicies|"
       "quinquies|septies|sexies|octies|nonies|decies|vicies|tricies|"
       "quater|bis|ter")
NUM = (rf"(?:L\.|R\.|D\.)?\s?\d+(?:\s*er\b)?(?:[-‐‑]\d+)*"
       rf"(?:\s+(?:{SUF})\b)*(?:\s+[A-Z]\b)?(?:\s+(?:bis|ter|quater)\b)?")
ARTICLE_RE = re.compile(rf"\barticles?\s+({NUM}(?:\s*(?:,|\bet\b)\s*{NUM})*)", re.I)
CODE_NEAR = re.compile(
    r"(code g[ée]n[ée]ral des imp[ôo]ts|\bCGI\b|"
    r"code des impositions sur les biens et services|\bCIBS\b)", re.I)


def norm_art(s):
    return re.sub(r"[‐‑‒–—]", "-", str(s)).strip()


def articles(text):
    out = []
    for m in ARTICLE_RE.finditer(text):
        for p in re.split(r"\s*(?:,|\bet\b)\s*", m.group(1)):
            p = norm_art(re.sub(r"\s+", " ", p))
            if p and re.match(r"^(?:[LRD]\.\s?)?\d", p):
                out.append(p)
    return out


def articles_cgi(text):
    """Articles followed within ~80 chars by a tax-code reference."""
    out = []
    for m in ARTICLE_RE.finditer(text):
        if not CODE_NEAR.search(text[m.end(): m.end() + 80]):
            continue
        for p in re.split(r"\s*(?:,|\bet\b)\s*", m.group(1)):
            p = norm_art(re.sub(r"\s+", " ", p))
            if p and re.match(r"^(?:[LRD]\.\s?)?\d", p):
                out.append(p)
    return out


def articles_cgi_loose(text):
    """If the amendment mentions the tax code anywhere, take all citations."""
    if not CODE_NEAR.search(text):
        return []
    return [norm_art(a) for a in articles(text)]


# ---------------------------------------------------------------------------
# Legislatures 15, 16 and 17 (cell 28)
# ---------------------------------------------------------------------------
NS = "{http://schemas.assemblee-nationale.fr/referentiel}"


def txt(root, path):
    el = root.find(path)
    return el.text if el is not None and el.text else None


def parse(xml_bytes, source):
    r = ET.fromstring(xml_bytes)
    disp = clean(txt(r, f"{NS}corps/{NS}contenuAuteur/{NS}dispositif"))
    expose = clean(txt(r, f"{NS}corps/{NS}contenuAuteur/{NS}exposeSommaire"))
    both = strip_gage(disp) + " " + strip_gage(expose)
    cosign = r.findall(f"{NS}signataires/{NS}cosignataires/{NS}acteurRef")
    return {
        "uid":           txt(r, f"{NS}uid"),
        "legislature":   txt(r, f"{NS}legislature"),
        "numero":        txt(r, f"{NS}identification/{NS}numeroOrdreDepot"),
        "numero_long":   txt(r, f"{NS}identification/{NS}numeroLong"),
        "examen_ref":    txt(r, f"{NS}examenRef"),
        "texte_ref":     txt(r, f"{NS}texteLegislatifRef"),
        "organe_examen": txt(r, f"{NS}identification/{NS}prefixeOrganeExamen"),
        "auteur":        txt(r, f"{NS}signataires/{NS}auteur/{NS}acteurRef"),
        "groupe":        txt(r, f"{NS}signataires/{NS}auteur/{NS}groupePolitiqueRef"),
        "type_auteur":   txt(r, f"{NS}signataires/{NS}auteur/{NS}typeAuteur"),
        "n_cosign":      len(cosign),
        "division":      txt(r, f"{NS}pointeurFragmentTexte/{NS}division/{NS}titre"),
        "date_depot":    txt(r, f"{NS}cycleDeVie/{NS}dateDepot"),
        "sort":          txt(r, f"{NS}cycleDeVie/{NS}sort"),
        "dispositif":    disp,
        "expose":        expose,
        "articles_strict": "|".join(dict.fromkeys(articles_cgi(both))),
        "articles_loose":  "|".join(dict.fromkeys(articles_cgi_loose(both))),
        "source_file":   source,
    }


def parse_zip(leg):
    rows = []
    with zipfile.ZipFile(AN / f"amendements_leg{leg}.xml.zip") as f:
        names = [n for n in f.namelist() if n.endswith(".xml")]
        for i, n in enumerate(names):
            try:
                r = parse(f.read(n), n)
                r["dossier"] = n.split("/")[1] if n.count("/") > 2 else None
                rows.append(r)
            except Exception as e:
                rows.append({"source_file": n, "error": f"{type(e).__name__}: {e}"})
            if i % 20000 == 0 and i:
                print(f"    {i:,}/{len(names):,}")
    return rows


# ---------------------------------------------------------------------------
# Legislature 14 (cell 30)
# ---------------------------------------------------------------------------
def t14(el, path):
    x = el.find(path)
    return x.text if x is not None and x.text else None


def parse_leg14(zip_path):
    rows = []
    with zipfile.ZipFile(zip_path) as z:
        with z.open(z.namelist()[0]) as fh:
            for _, el in ET.iterparse(fh, events=("end",)):
                if el.tag != "amendement":
                    continue
                disp = clean(t14(el, "corps/dispositif"))
                expose = clean(t14(el, "corps/exposeSommaire"))
                both = disp + " " + expose
                rows.append({
                    "uid":           t14(el, "uid"),
                    "legislature":   "14",
                    "numero":        t14(el, "identifiant/numero"),
                    "numero_long":   t14(el, "numeroLong"),
                    "texte_ref":     t14(el, "identifiant/saisine/refTexteLegislatif"),
                    "organe_examen": t14(el, "identifiant/saisine/organeExamen"),
                    "partie_plf":    t14(el, "identifiant/saisine/numeroPartiePLF"),
                    "etape":         t14(el, "etapeTexte"),
                    "auteur":        t14(el, "signataires/auteur/acteurRef"),
                    "groupe":        t14(el, "signataires/auteur/groupePolitiqueRef"),
                    "type_auteur":   t14(el, "signataires/auteur/typeAuteur"),
                    "n_cosign":      len(el.findall("signataires/cosignataires/acteurRef")),
                    "division":      t14(el, "pointeurFragmentTexte/division/titre"),
                    "date_depot":    t14(el, "dateDepot"),
                    "sort":          t14(el, "sort/sortEnSeance") or t14(el, "etat"),
                    "dispositif":    disp,
                    "expose":        expose,
                    "articles_strict": "|".join(dict.fromkeys(articles_cgi(both))),
                    "articles_loose":  "|".join(dict.fromkeys(articles_cgi_loose(both))),
                })
                el.clear()
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Finance-bill labels (cells 32 and 34)
# ---------------------------------------------------------------------------
def parse_dossiers14(zip_path):
    rows = []
    with zipfile.ZipFile(zip_path) as z:
        with z.open(z.namelist()[0]) as fh:
            for _, el in ET.iterparse(fh, events=("end",)):
                if el.tag != "document":
                    continue
                uid = el.find("uid")
                ttl = el.find("titres/titrePrincipal")
                dos = el.find("dossierRef")
                if uid is not None and uid.text:
                    rows.append({"texte_ref": uid.text,
                                 "title": ttl.text if ttl is not None and ttl.text else None,
                                 "dossier": dos.text if dos is not None and dos.text else None})
                el.clear()
    return pd.DataFrame(rows).drop_duplicates("texte_ref")


FIN = re.compile(r"projet de loi de finances", re.I)
NOT = re.compile(r"financement de la s[ée]curit[ée] sociale", re.I)


def label_finance(df):
    t = df["title"].fillna("")
    df["is_finance"] = t.str.contains(FIN) & ~t.str.contains(NOT)
    y = t.str.extract(r"pour (\d{4})")[0]
    df["plf_year"] = pd.to_numeric(y, errors="coerce").where(df["is_finance"])
    df["is_49_3"] = t.str.contains(r"responsabilit[ée] du Gouvernement", case=False)
    return df


def dossier_titles(leg):
    rows = []
    with zipfile.ZipFile(AN / f"dossiers_leg{leg}.xml.zip") as z:
        for n in z.namelist():
            if "/dossierParlementaire/" not in n:
                continue
            t = z.read(n).decode("utf-8", "ignore")
            m = re.search(r"<titre>(.*?)</titre>", t, re.S)
            rows.append({"dossier": n.split("/")[-1][:-4],
                         "title": clean(m.group(1)) if m else None})
    return pd.DataFrame(rows).drop_duplicates("dossier")


def main():
    assert articles_cgi("l'article 200 quaterdecies du code général des impôts") == ["200 quaterdecies"]
    assert articles_cgi("l'article 790 A bis du code général des impôts") == ["790 A bis"]
    assert articles_cgi("l'article 279-0 bis du code général des impôts") == ["279-0 bis"]

    # --- legislatures 15-17: parse (cell 28), then label (cell 34) ---
    all_rows = []
    for leg in (15, 16, 17):
        print(f"leg {leg}")
        all_rows += parse_zip(leg)
    am = pd.DataFrame(all_rows)
    am["date_depot"] = pd.to_datetime(am["date_depot"], errors="coerce")
    print(f"\n{len(am):,} amendments, "
          f"{am.get('error', pd.Series(dtype=str)).notna().sum()} errors")
    print(f"with a strict citation: {(am['articles_strict'].fillna('') != '').sum():,}")

    titles = pd.concat([dossier_titles(15), dossier_titles(16), dossier_titles(17)],
                       ignore_index=True)
    am = label_finance(am.merge(titles, on="dossier", how="left"))
    print(f"legs 15-17: {am['is_finance'].sum():,} finance-bill amendments, "
          f"{am['is_49_3'].sum():,} under 49.3 ({len(am):,} rows after the title merge)")
    print(am[am["is_finance"]].groupby("plf_year").size().to_string())
    am.to_parquet(INTERMEDIATE / "amendments_15_17.parquet", index=False)

    # --- legislature 14: parse (cell 30), then label (cell 32) ---
    am14 = parse_leg14(AN / "amendements_leg14.xml.zip")
    am14["date_depot"] = pd.to_datetime(am14["date_depot"], errors="coerce")
    print(f"parsed {len(am14):,} amendments")
    print(f"with a strict citation: {(am14['articles_strict'] != '').sum():,}")
    print(f"dates: {am14['date_depot'].min().date()} to {am14['date_depot'].max().date()}")

    d14 = parse_dossiers14(AN / "dossiers_leg14.xml.zip")
    am14 = label_finance(am14.merge(d14, on="texte_ref", how="left"))
    print(f"leg 14: {am14['is_finance'].sum():,} finance-bill amendments")
    print(am14[am14["is_finance"]].groupby("plf_year").size().to_string())
    am14.to_parquet(INTERMEDIATE / "amendments_14.parquet", index=False)


if __name__ == "__main__":
    main()
