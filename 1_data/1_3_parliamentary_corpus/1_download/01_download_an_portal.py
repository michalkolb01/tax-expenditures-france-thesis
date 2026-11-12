"""Download the Assemblée nationale open-data archives (legislatures 14-17).

Pipeline step, no thesis number directly.

For each dataset (amendements, debats, dossiers, reunions, acteurs) and
legislature, opens the portal page, reads off the download link, the MD5
checksum and the publication date, downloads the .xml.zip in 2 MB ranged
pieces (resumable: a .part file is kept), verifies the checksum, and writes
one manifest row per dataset. Datasets the portal does not publish
(debates and meetings of legislature 14) get an "absent" row so the gap is
visible.

Inputs
    https://data.assemblee-nationale.fr (portal pages listed in SOURCES)
Outputs
    data/raw/an_portal/<dataset>_leg<NN>.xml.zip   17 archives, about 2 GB
    data/raw/discovered.json                        cache of the page reads
    1_data/1_3_parliamentary_corpus/1_download/manifests/manifest_an_portal.csv one row per dataset
                                                    (19 rows: 17 ok, 2 absent)
Needs
    pip install requests beautifulsoup4 pandas

Source
    Master Thesis_1 Scraping (1_Scraping.ipynb), cells 4 (setup), 6 (source
    list), 8 (page reading), 10 (download), 12 (manifest). Cells 14-15
    (listing what is on disk) are diagnostics and were dropped.

Caveats
    - amendements_leg15 and amendements_leg16 (738 MB and 412 MB) were too
      large to transfer from Colab: they were downloaded by hand on a laptop
      from the same portal pages and uploaded (MANUAL; manifest column
      how = "laptop"). This script skips them; download them by hand into
      data/raw/an_portal/ under the same names.
    - Legislature 17 files are rebuilt every morning by the portal, so a file
      downloaded on an earlier day shows verified = False: it is an older
      edition, not a damaged file. The thesis used the editions published on
      2026-08-26 (see the manifest).
    - The amendment archives are stored here in an_portal/, not in the
      amendments/ folder named in data/README.md.
    - The manifest was written to raw/ in the notebook; it now goes to
      1_data/1_3_parliamentary_corpus/1_download/manifests/.
"""
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "src" / "config.py").exists()) / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
MANIFESTS = HERE / "manifests"
OUT = RAW / "an_portal"          # the downloaded files
NOTES_FILE = RAW / "discovered.json"

HEADERS = {"User-Agent": "research"}

B = "https://data.assemblee-nationale.fr"
A15 = f"{B}/archives-anterieures/archives-15e"
A14 = f"{B}/archives-anterieures/archives-14e"

SOURCES = {
    ("amendements", 17): f"{B}/travaux-parlementaires/amendements/tous-les-amendements",
    ("amendements", 16): f"{B}/archives-16e/amendements/tous-les-amendements",
    ("amendements", 15): f"{A15}/amendements",
    ("amendements", 14): f"{A14}/amendements",

    ("debats",      17): f"{B}/travaux-parlementaires/debats",
    ("debats",      16): f"{B}/archives-16e/debats",
    ("debats",      15): f"{A15}/debats-en-seance-publique",

    ("dossiers",    17): f"{B}/travaux-parlementaires/dossiers-legislatifs",
    ("dossiers",    16): f"{B}/archives-16e/dossiers-legislatifs",
    ("dossiers",    15): f"{A15}/dossiers-legislatifs",
    ("dossiers",    14): f"{A14}/dossiers-legislatifs",

    ("reunions",    17): f"{B}/reunions/reunions",
    ("reunions",    16): f"{B}/archives-16e/reunions",
    ("reunions",    15): f"{A15}/reunions",

    ("acteurs",     17): f"{B}/acteurs/historique-des-deputes",
    ("acteurs",     16): f"{B}/archives-16e/historique-des-deputes",
    ("acteurs",     15): f"{A15}/deputes-senateurs-et-ministres",
}

# Not published by the portal at all.
ABSENT = {
    ("debats",   14): "not on the portal — DILA is the source (notebook 2)",
    ("reunions", 14): "not on the portal",
}

# Too large to transfer from Colab; downloaded on a laptop and uploaded to Drive.
MANUAL = {("amendements", 15), ("amendements", 16)}

NEEDED = {"page", "link", "checksums", "published", "read_at"}


def read_page(url):
    soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=30).content,
                         "html.parser")
    links = [requests.compat.urljoin(url, a["href"])
             for a in soup.find_all("a", href=True)
             if a["href"].lower().endswith(".xml.zip")]
    text = soup.get_text(" ", strip=True)
    return {"page": url,
            "link": links[0] if links else None,
            "checksums": re.findall(r"\b([0-9a-f]{32})\b", text),
            "published": re.findall(r"\b(20\d\d-\d\d-\d\d \d\d:\d\d:\d\d)", text)[:1],
            "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def read_pages():
    """Read each portal page once; reuse the cached reads on a rerun."""
    PAGES = {}
    if NOTES_FILE.exists():
        saved = json.loads(NOTES_FILE.read_text())
        loaded = {(k.rsplit("|", 1)[0], int(k.rsplit("|", 1)[1])): v
                  for k, v in saved.items()}
        if all(NEEDED <= set(v) for v in loaded.values()):
            PAGES = loaded
            print(f"loaded {len(PAGES)} pages from an earlier run")
        else:
            print("saved file is from an older version — reading the pages again")

    if not PAGES:
        for key, url in SOURCES.items():
            try:
                PAGES[key] = read_page(url)
                print(f"{key[0]:12} leg {key[1]}  ->  {PAGES[key]['link']}")
            except Exception as e:
                print(f"{key[0]:12} leg {key[1]}  ->  FAILED: {e}")
            time.sleep(2)
        NOTES_FILE.write_text(json.dumps({f"{k[0]}|{k[1]}": v for k, v in PAGES.items()},
                                         indent=2))

    assert PAGES, "no pages were read"
    return PAGES


def checksum(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download(url, dest, piece=2 << 20, tries=40):
    part = dest.with_suffix(".part")
    total = int(requests.head(url, headers=HEADERS,
                              allow_redirects=True, timeout=60)
                .headers["content-length"])
    have = part.stat().st_size if part.exists() else 0

    while have < total:
        end = min(have + piece - 1, total - 1)
        for attempt in range(tries):
            try:
                h = dict(HEADERS, Range=f"bytes={have}-{end}")
                r = requests.get(url, headers=h, timeout=60)
                if r.status_code != 206 or len(r.content) != end - have + 1:
                    raise IOError(f"bad response ({r.status_code})")
                with open(part, "ab") as f:
                    f.write(r.content)
                have += len(r.content)
                break
            except Exception:
                if attempt == tries - 1:
                    raise
                time.sleep(min(5 * (attempt + 1), 30))
        print(f"\r    {have/1e6:.0f}/{total/1e6:.0f} MB", end="", flush=True)
    print()
    part.rename(dest)


def download_all(PAGES):
    for key, info in PAGES.items():
        dest = OUT / f"{key[0]}_leg{key[1]}.xml.zip"
        if key in MANUAL:
            print(f"[laptop] {dest.name}")
        elif dest.exists():
            print(f"[have]   {dest.name}")
        elif not info["link"]:
            print(f"[skip]   {dest.name} — no link on the page")
        else:
            print(f"[get]    {dest.name}")
            try:
                download(info["link"], dest)
                got = checksum(dest)
                print("   checksum", "OK" if got in info["checksums"] else "differs: " + got)
            except Exception as e:
                print(f"   FAILED: {type(e).__name__}: {e}")


def write_manifest(PAGES):
    rows = [{"dataset": d, "legislature": l, "status": "absent", "note": why}
            for (d, l), why in ABSENT.items()]

    for (dataset, leg), info in PAGES.items():
        f = OUT / f"{dataset}_leg{leg}.xml.zip"
        row = {"dataset": dataset, "legislature": leg,
               "page": info["page"], "link": info["link"],
               "published": info["published"][0] if info["published"] else None,
               "page_read_at": info["read_at"],
               "how": "laptop" if (dataset, leg) in MANUAL else "notebook"}
        if f.exists():
            got = checksum(f)
            row.update(file=f.name, mb=round(f.stat().st_size / 1e6, 1),
                       checksum=got,
                       downloaded=datetime.fromtimestamp(f.stat().st_mtime,
                                                         timezone.utc).isoformat(timespec="seconds"),
                       verified=got in info["checksums"],
                       status="ok")
        else:
            row["status"] = "missing"
        rows.append(row)

    record = pd.DataFrame(rows)
    record.to_csv(MANIFESTS / "manifest_an_portal.csv", index=False)

    assert len(record) == len(SOURCES) + len(ABSENT), "wrong number of rows"
    print(record["status"].value_counts().to_string(), "\n")
    print(record[["dataset", "legislature", "status", "verified", "mb",
                  "published", "how"]].to_string())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    print("Files will go to:", OUT)
    PAGES = read_pages()
    download_all(PAGES)
    write_manifest(PAGES)


if __name__ == "__main__":
    main()
