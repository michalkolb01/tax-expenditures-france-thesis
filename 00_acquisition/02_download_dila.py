"""Download the DILA plenary verbatim records for 2011-2017.

Pipeline step, no thesis number directly.

The AN open-data portal has no plenary debates before legislature 15
(2017). DILA publishes them as one .taz archive per sitting. This script
lists the year folders on the DILA server, downloads every .taz for
2011-2017, records each file's size and SHA-256 (DILA publishes no
checksums), and checks that the first archive of each year opens.

Inputs
    https://echanges.dila.gouv.fr/OPENDATA/Debats/AN/<year>/*.taz
Outputs
    data/raw/dila_debats/<year>/AN_*.taz         817 files, 378 MB
    00_acquisition/manifests/manifest_dila.csv   one row per file
                                                 (year, file, url, bytes,
                                                 sha256, retrieved_at)
Needs
    pip install requests beautifulsoup4 pandas
    the `gzip` command (to unpack the Unix .Z compression of 2011-2015)

Source
    Master Thesis_1 Scraping (1_Scraping.ipynb), cells 4 (setup), 19
    (listing the year folders), 21 (download and manifest), 23 (check that
    the archives open: taz_entries).

Caveats
    - Three packagings: 2011-2015 Unix .Z compression, 2016 plain tar, 2017
      a tar inside a tar; taz_entries() handles all three. Each archive holds
      CRI_* (the transcript, used) and AAA_* (amendments annex, not used).
    - From mid-2013 the filename no longer carries the sitting date, and
      publication lags the sitting: take the date from <dateSeance> in the
      XML, never from the filename.
    - The manifest was written to raw/ in the notebook; it now goes to
      00_acquisition/manifests/.
"""
import hashlib
import io
import re
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import RAW, INTERMEDIATE, ROOT  # noqa: E402,F401

HERE = Path(__file__).resolve().parent
MANIFESTS = HERE / "manifests"
DILA = RAW / "dila_debats"
BASE = "https://echanges.dila.gouv.fr/OPENDATA/Debats/AN/"
HEADERS = {"User-Agent": "research"}

YEARS = ["2011", "2012", "2013", "2014", "2015", "2016", "2017"]


def listing(url):
    soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=60).content,
                         "html.parser")
    return [a["href"] for a in soup.find_all("a", href=True)]


def build_index():
    """List every .taz per year folder on the DILA server."""
    years = [h.strip("/") for h in listing(BASE)
             if re.fullmatch(r"(20\d\d|Annee_en_cours)/", h)]
    print(years, "\n")

    INDEX = {}
    for y in years:
        files = [h for h in listing(BASE + y + "/") if h.endswith(".taz")]
        INDEX[y] = files
        print(f"{y:16} {len(files):>4} files   first: {files[0] if files else '—'}")
        time.sleep(1)

    print("\ntotal:", sum(len(v) for v in INDEX.values()))
    return INDEX


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def download(INDEX):
    rows, n = [], 0
    for y in YEARS:
        (DILA / y).mkdir(exist_ok=True)
        for name in INDEX[y]:
            dest = DILA / y / name
            if not dest.exists():
                r = requests.get(BASE + y + "/" + name, headers=HEADERS, timeout=120)
                r.raise_for_status()
                dest.write_bytes(r.content)
                time.sleep(0.5)
            rows.append({"year": y, "file": name,
                         "url": BASE + y + "/" + name,
                         "bytes": dest.stat().st_size,
                         "sha256": sha(dest),
                         "retrieved_at": datetime.now(timezone.utc)
                         .isoformat(timespec="seconds")})
            n += 1
            if n % 50 == 0:
                print(f"  {n} files")

    dila = pd.DataFrame(rows)
    dila.to_csv(MANIFESTS / "manifest_dila.csv", index=False)
    assert len(dila) == sum(len(INDEX[y]) for y in YEARS), "count mismatch"
    print(f"\n{len(dila)} files, {dila['bytes'].sum()/1e6:.0f} MB")
    print(dila.groupby("year")["bytes"].agg(["count", "sum"]).to_string())


def taz_entries(path):
    """Open a .taz, unwrapping .Z compression and any inner tar."""
    try:
        t = tarfile.open(path)
    except tarfile.ReadError:
        raw = subprocess.run(["gzip", "-dc", str(path)],
                             capture_output=True).stdout
        t = tarfile.open(fileobj=io.BytesIO(raw))

    names = t.getnames()
    if len(names) == 1 and names[0].endswith(".tar"):
        inner = t.extractfile(names[0]).read()
        t = tarfile.open(fileobj=io.BytesIO(inner))
        names = t.getnames()
    return t, names


def check_open():
    bad = 0
    for y in YEARS:
        p = sorted((DILA / y).glob("*.taz"))[0]
        try:
            _, names = taz_entries(p)
            cri = [n for n in names if "CRI" in n]
            print(f"{y}  {p.name:26} {len(names)} entries, transcript: {cri[0]}")
        except Exception as e:
            print(f"{y}  {p.name:26} FAILED: {type(e).__name__}")
            bad += 1
    assert bad == 0, f"{bad} years failed to open"


def main():
    DILA.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    INDEX = build_index()
    download(INDEX)
    check_open()


if __name__ == "__main__":
    main()
