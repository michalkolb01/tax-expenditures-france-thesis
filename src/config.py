"""Paths used by every script in the replication package.

Set the environment variable THESIS_ROOT to the folder that contains this
package (for example the package folder in Google Drive when running in
Colab). By default the package root is the parent of this file's folder.

    import sys; sys.path.insert(0, 'src')
    from config import RAW, INTERMEDIATE, ROOT

Large source files (debate transcripts, inventory PDFs, amendment dumps)
are not stored in the package. data/README.md lists where to download
them; once downloaded they go in data/raw/.
"""
import os
from pathlib import Path

ROOT = Path(os.environ.get("THESIS_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"
RAW = DATA / "raw"                    # downloaded public sources, unchanged
INTERMEDIATE = DATA / "intermediate"  # datasets built by the pipeline
FIGURES = ROOT / "figures"

for p in (RAW, INTERMEDIATE, FIGURES):
    p.mkdir(parents=True, exist_ok=True)


def in_colab() -> bool:
    try:
        import google.colab  # noqa: F401
        return True
    except ImportError:
        return False
