"""Figure style matching a LaTeX document set in Latin Modern Roman.

Latin Modern is the default LaTeX font (Computer Modern, via
\\usepackage{lmodern}). Every text element of the figures (titles, axis
labels, tick labels, legends and mathematics) uses it, at the size of the
thesis body text, so that figures and text look the same on the page.

Usage
-----
    import sys; sys.path.insert(0, 'src')
    from thesis_style import use_thesis_style, save_figure, figsize
    use_thesis_style()
    fig, ax = plt.subplots(figsize=figsize(1.0))
    ...
    save_figure(fig, 'fig5_1_survival_by_score')   # writes PDF (and PNG)

In LaTeX:  \\includegraphics[width=\\textwidth]{figures/fig5_1_survival_by_score.pdf}

Fonts
-----
On Ubuntu or Colab, install the fonts once:
    !apt-get -qq install fonts-lmodern
On macOS or Windows, install "Latin Modern Roman" from CTAN
(https://ctan.org/pkg/lm) or use the copy shipped with a TeX distribution.
"""
import glob
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Width of the LaTeX text block in inches. Measure it in your document with
# \\the\\textwidth (in points) and divide by 72.27. 6.0 in fits A4 with
# 2.5 cm margins; change it once here if your layout differs.
TEXT_WIDTH_IN = 6.0
BODY_PT = 11          # body text size of the thesis (10, 11 or 12 pt)

FONT_DIRS = [
    "/usr/share/texmf/fonts/opentype/public/lm",
    "/usr/share/texlive/texmf-dist/fonts/opentype/public/lm",
    "/usr/share/fonts/opentype/lmodern",
    os.path.expanduser("~/Library/Fonts"),
    "/Library/Fonts",
]


def _register_latin_modern() -> str:
    """Register the Latin Modern Roman files with matplotlib; return the family name."""
    # Latin Modern ships several optical sizes (5 to 17 pt) under one family
    # name; LaTeX uses the 10-pt design for body text, so register only that.
    found = []
    for d in FONT_DIRS:
        found += glob.glob(os.path.join(d, "lmroman10-*.otf"))
    for f in found:
        font_manager.fontManager.addfont(f)
    names = {font_manager.FontProperties(fname=f).get_name() for f in found}
    # Matplotlib may already have indexed the other optical sizes under the
    # same family name; remove them so the 10-pt design is always chosen.
    fm = font_manager.fontManager
    fm.ttflist = [e for e in fm.ttflist
                  if not (e.name in names and "lmroman10-" not in os.path.basename(e.fname).lower())]
    try:
        fm._findfont_cached.cache_clear()
    except AttributeError:
        pass
    if "Latin Modern Roman" in names:
        return "Latin Modern Roman"
    if names:
        return sorted(names)[0]
    raise RuntimeError(
        "Latin Modern Roman not found. Install it (apt-get install fonts-lmodern, "
        "or from https://ctan.org/pkg/lm) and run again."
    )


def use_thesis_style(body_pt: int = BODY_PT) -> None:
    family = _register_latin_modern()
    small = body_pt - 1
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": [family],
        "mathtext.fontset": "cm",          # Computer Modern maths, as in LaTeX
        "axes.unicode_minus": False,
        "font.size": body_pt,
        "axes.titlesize": body_pt,
        "axes.labelsize": body_pt,
        "xtick.labelsize": small,
        "ytick.labelsize": small,
        "legend.fontsize": small,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "lines.linewidth": 1.4,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,                # embed fonts as TrueType/OpenType
        "ps.fonttype": 42,
    })


def figsize(width_fraction: float = 1.0, aspect: float = 0.62):
    """Figure size in inches for a fraction of the LaTeX text width."""
    w = TEXT_WIDTH_IN * width_fraction
    return (w, w * aspect)


# Grey-scale-safe palette (prints well in black and white).
PALETTE = ["#1b1b1b", "#5f5f5f", "#9a9a9a", "#c8c8c8", "#7a1f1f"]
LINESTYLES = ["-", "--", "-.", ":", (0, (5, 1, 1, 1))]


def save_figure(fig, name: str, folder=None, png: bool = True) -> None:
    """Save as vector PDF for LaTeX, plus a PNG preview."""
    from config import FIGURES
    folder = folder or FIGURES
    os.makedirs(folder, exist_ok=True)
    fig.savefig(os.path.join(folder, f"{name}.pdf"))
    if png:
        fig.savefig(os.path.join(folder, f"{name}.png"), dpi=300)
    plt.close(fig)
