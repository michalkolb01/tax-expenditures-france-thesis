# =====================================================================
# Chapter 6, section 6.3 - workbook for a structured reading of the
# arguments made in the debates, measure by measure.
#
# Source: the corpus of interventions linked to measures through the
# amendments they discuss (see section 4.x).
#   arguments_v3_dedup.csv  - one row per distinct intervention, with the
#                             measure code and the earlier classification
#   turns.parquet           - the texts (row order = 'idx')
#   tax_expenditures_panel_2009_2026.xlsx - measure names and 2011 scores
#
# Selection rule (fixed in advance):
#   - the 9 measures with the most interventions in the corpus, and
#   - every measure scored 0 or 1 in 2011 with at least 20 interventions.
# For each measure, all substantive interventions are kept (off-topic and
# purely procedural ones excluded), up to the 40 longest for the largest
# measures.
#
# Output (in ch6/6_3_arguments/data): ch6_reading_workbook.xlsx with
#   Instructions, Codebook, Template (one row per measure to fill in),
#   Summary (counts of measures, updated as you fill the template), and
#   one reading sheet per measure (M01, M02, ...).
# =====================================================================
import glob, re
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from config import INTERMEDIATE  # noqa: E402

TOP_N = 9          # most debated measures
MIN_CONDEMNED = 20 # minimum interventions for measures scored 0 or 1
CAP = 40           # maximum passages per measure (the longest are kept)

def find(name):
    p = INTERMEDIATE / name
    assert p.exists(), f'not found: {p} (built by 03_debate_corpus/ and 01_inventory_panel/)'
    return str(p)

OUT = str(Path(__file__).resolve().parent / "data")

# ---------------------------------------------------------------------
# 1. Corpus
# ---------------------------------------------------------------------
args  = pd.read_csv(find('arguments_v3_dedup.csv'))
turns = pd.read_parquet(find('turns.parquet'))
panel = pd.read_excel(find('tax_expenditures_panel_2009_2026.xlsx'), sheet_name='one_row_per_measure')
panel['code'] = panel['code'].astype(str)

args['texte']   = args['idx'].map(lambda i: turns.iloc[i]['texte'])
args['measure'] = args['measure'].astype(str)
corpus = args.drop_duplicates(['measure', 'texte'])
names  = panel.set_index('code')['name']
scores = panel.set_index('code')['score_2011'].astype(str)

# ---------------------------------------------------------------------
# 2. Selection of measures
# ---------------------------------------------------------------------
n = corpus.groupby('measure').size().rename('n').reset_index()
n['name']  = n['measure'].map(names)
n['score'] = n['measure'].map(scores)
n = n.sort_values('n', ascending=False)
top  = n.head(TOP_N).assign(rule=f'One of the {TOP_N} most debated measures')
cond = n[n.score.isin(['0', '1']) & (n.n >= MIN_CONDEMNED)].assign(
        rule=f'Scored 0 or 1 in 2011, at least {MIN_CONDEMNED} interventions')
sel = pd.concat([top, cond]).drop_duplicates('measure').reset_index(drop=True)
sel['sheet'] = [f'M{i+1:02d}' for i in range(len(sel))]
print(f'{len(sel)} measures selected')

# ---------------------------------------------------------------------
# 3. Passages per measure
# ---------------------------------------------------------------------
subst = corpus[(corpus.categorie != 'hors_sujet') & (corpus.niveau != 'hors_fond')].copy()
subst['length'] = subst['texte'].str.len()
passages = {}
for _, m in sel.iterrows():
    p = subst[subst.measure == m.measure].nlargest(CAP, 'length')
    passages[m.sheet] = p
    sel.loc[sel.sheet == m.sheet, 'kept'] = len(p)
    sel.loc[sel.sheet == m.sheet, 'available'] = (subst.measure == m.measure).sum()

# ---------------------------------------------------------------------
# 4. Workbook
# ---------------------------------------------------------------------
F = 'Arial'
HDR = Font(name=F, bold=True, color='FFFFFF'); HFILL = PatternFill('solid', fgColor='305496')
INPUT = PatternFill('solid', fgColor='FFF2CC'); BODY = Font(name=F, size=10)
WRAP = Alignment(wrap_text=True, vertical='top'); LINE = Border(bottom=Side(style='thin', color='BFBFBF'))
ARGS = ['Cost', 'Effects or windfall', 'Distribution or targeting', 'Need of a group or territory',
        'Design or fit', 'Fairness or values']

def header(ws, row, labels, widths=None):
    for j, h in enumerate(labels, 1):
        c = ws.cell(row, j, h); c.font = HDR; c.fill = HFILL
        c.alignment = Alignment(wrap_text=True, vertical='center')
    if widths:
        for j, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(j)].width = w

wb = Workbook()

# Instructions
ws = wb.active; ws.title = 'Instructions'
text = [
 ('Structured reading of the arguments in the debates, measure by measure', True),
 ('', False),
 ('For each measure listed in the Template sheet:', True),
 ('1. Open its reading sheet (M01, M02, ...) and read the passages. Each passage is one intervention linked to the measure through the amendment it discusses.', False),
 ('2. Mark in the reading sheet any passage that is not about this measure (column "About this measure?" = No). These are matching errors and are counted in the Template.', False),
 ('3. Fill the measure\'s row in the Template sheet (yellow cells): which argument types appear among those arguing to restrict or remove the measure, and among those arguing to keep or extend it (Yes/No for each type).', False),
 ('4. Record whether any defender disputes the 2011 score or argues about the measure\'s effects, which evaluations are cited, and one or two quotes you may use.', False),
 ('', False),
 ('Side is judged relative to the change discussed: a speaker who supports an amendment removing, restricting or refusing to extend the measure argues to restrict it; a speaker who opposes such an amendment, or supports an extension, argues to keep or extend it.', False),
 ('The columns "Earlier position" and "Earlier category" in the reading sheets come from the automated classification and are only a guide.', False),
 ('', False),
 (f'Selection rule: the {TOP_N} measures with the most interventions in the corpus, plus every measure scored 0 or 1 in 2011 with at least {MIN_CONDEMNED} interventions. Off-topic and purely procedural interventions are excluded. For measures with more than {CAP} substantive interventions, the {CAP} longest are kept.', False),
 ('Reliability: a week later, reread 4 or 5 measures and fill the "Reread" columns without looking at your first answers; the Summary sheet reports the agreement.', False),
 ('', False),
 ('Row 2 of the Template is filled in as an example; overwrite it with your own reading.', False)]
for i, (t, b) in enumerate(text, 1):
    c = ws.cell(i, 1, t); c.font = Font(name=F, bold=b, size=12 if i == 1 else 10); c.alignment = Alignment(wrap_text=True)
ws.column_dimensions['A'].width = 130

# Codebook
cb = wb.create_sheet('Codebook')
header(cb, 1, ['Argument type', 'Definition', 'Level (Fischer, section 2.7)', 'Example'], [28, 62, 26, 50])
code = [
 ('Cost', 'The revenue forgone, its size or growth', 'Verification', '"This measure now costs €1 billion a year"'),
 ('Effects or windfall', 'Whether the measure achieves its objective; windfall for beneficiaries who would have acted anyway', 'Verification', '"It has no measurable effect on private research"'),
 ('Distribution or targeting', 'Who benefits: concentration on affluent households or large firms, or exclusion of some groups', 'Verification', '"Half the credit goes to fifty large groups"'),
 ('Need of a group or territory', 'The situation of beneficiaries: insularity, age, disability, a sector in difficulty', 'Validation', '"Corsican firms face the costs of insularity"'),
 ('Design or fit', 'Whether the measure is well designed for its purpose: abuse, diversion, complexity', 'Validation', '"The credit is diverted to furnished tourist lets"'),
 ('Fairness or values', 'Fairness, rights, family policy, keeping firms in family or French hands, the general interest', 'Vindication', '"Families should not be penalised for educating their children"')]
for i, row in enumerate(code, 2):
    for j, v in enumerate(row, 1):
        c = cb.cell(i, j, v); c.font = BODY; c.alignment = WRAP

# Template
tp = wb.create_sheet('Template')
cols = (['Sheet', 'Measure (annex title)', '2011 score', 'Interventions in corpus', 'Passages in reading sheet',
         'Passages not about this measure', 'Selection rule']
        + [f'Restrict: {a}' for a in ARGS] + [f'Keep or extend: {a}' for a in ARGS]
        + ['A defender disputes the 2011 score or argues effects?', 'Evaluations cited (which, by whom)',
           'Quote 1 (with speaker)', 'Quote 2 (with speaker)', 'Notes',
           'Reread: restrict arguments (list)', 'Reread: keep arguments (list)', 'Reread agrees with first reading?'])
header(tp, 1, cols)
first_arg = 8; last_arg = first_arg + 2 * len(ARGS) - 1
for i, m in sel.iterrows():
    r = i + 2
    ws_name = m.sheet
    vals = [ws_name, m['name'], m.score, int(m.n), int(m.kept)]
    for j, v in enumerate(vals, 1):
        c = tp.cell(r, j, v); c.font = BODY; c.alignment = WRAP
    # passages marked "No" in the reading sheet are counted by formula
    c = tp.cell(r, 6, f"=COUNTIF('{ws_name}'!$G$2:$G${CAP + 1},\"No\")"); c.font = BODY
    c = tp.cell(r, 7, m.rule); c.font = BODY; c.alignment = WRAP
    for j in range(first_arg, len(cols) + 1):
        c = tp.cell(r, j); c.fill = INPUT; c.font = BODY; c.alignment = WRAP
nrow = len(sel) + 1
yn = DataValidation(type='list', formula1='"Yes,No"', allow_blank=True); tp.add_data_validation(yn)
yn.add(f'{get_column_letter(first_arg)}2:{get_column_letter(last_arg + 1)}{nrow}')
yn2 = DataValidation(type='list', formula1='"Yes,No,Partly"', allow_blank=True); tp.add_data_validation(yn2)
yn2.add(f'{get_column_letter(len(cols))}2:{get_column_letter(len(cols))}{nrow}')
for j, w in enumerate([7, 46, 8, 11, 11, 12, 26] + [12] * (2 * len(ARGS)) + [16, 30, 40, 40, 24, 22, 22, 14], 1):
    tp.column_dimensions[get_column_letter(j)].width = w
tp.freeze_panes = 'C2'
# example row
for j in range(first_arg, first_arg + len(ARGS)):
    tp.cell(2, j, 'No')
tp.cell(2, first_arg + 2, 'Yes'); tp.cell(2, first_arg + 1, 'Yes')
for j in range(first_arg + len(ARGS), last_arg + 1):
    tp.cell(2, j, 'No')
tp.cell(2, first_arg + len(ARGS) + 1, 'Yes')
tp.cell(2, last_arg + 1, 'No'); tp.cell(2, last_arg + 5, 'Example row: replace with your own reading')

# Summary
sm = wb.create_sheet('Summary')
sm.cell(1, 1, 'Number of measures in whose debates each argument type appears, by side').font = Font(name=F, bold=True)
header(sm, 3, ['Argument type', 'Measures: restrict or remove', 'Measures: keep or extend'], [36, 28, 28])
for i, a in enumerate(ARGS):
    r = 4 + i
    sm.cell(r, 1, a).font = BODY
    cr = get_column_letter(first_arg + i); ck = get_column_letter(first_arg + len(ARGS) + i)
    sm.cell(r, 2, f'=COUNTIF(Template!${cr}$2:${cr}${nrow},"Yes")').font = BODY
    sm.cell(r, 3, f'=COUNTIF(Template!${ck}$2:${ck}${nrow},"Yes")').font = BODY
r = 4 + len(ARGS) + 1
cd = get_column_letter(last_arg + 1); ca = get_column_letter(len(cols))
sm.cell(r, 1, 'Measures where a defender disputes the 2011 score or argues effects').font = BODY
sm.cell(r, 2, f'=COUNTIF(Template!${cd}$2:${cd}${nrow},"Yes")').font = BODY
sm.cell(r + 1, 1, 'Passages not about their measure (matching errors found)').font = BODY
sm.cell(r + 1, 2, f'=SUM(Template!$F$2:$F${nrow})').font = BODY
sm.cell(r + 2, 1, 'Passages read in total').font = BODY
sm.cell(r + 2, 2, f'=SUM(Template!$E$2:$E${nrow})').font = BODY
sm.cell(r + 4, 1, 'Reliability check').font = Font(name=F, bold=True)
sm.cell(r + 5, 1, 'Measures reread').font = BODY
sm.cell(r + 5, 2, f'=COUNTA(Template!${ca}$2:${ca}${nrow})').font = BODY
sm.cell(r + 6, 1, 'Rereadings that agree with the first reading').font = BODY
sm.cell(r + 6, 2, f'=COUNTIF(Template!${ca}$2:${ca}${nrow},"Yes")').font = BODY
sm.cell(r + 8, 1, f'Out of {len(sel)} measures. Counts update as you fill the Template.').font = Font(name=F, italic=True, size=9)

# Reading sheets
for _, m in sel.iterrows():
    rs = wb.create_sheet(m.sheet)
    rs.cell(1, 9, f"{m['name']} (2011 score: {m.score}; {int(m.n)} interventions; {int(m.kept)} shown)").font = Font(name=F, italic=True, size=9)
    header(rs, 1, ['#', 'Venue', 'Speaker', 'Passage', 'Earlier position', 'Earlier category', 'About this measure?', 'Your note'],
           [5, 10, 18, 100, 12, 14, 12, 30])
    for i, (_, p) in enumerate(passages[m.sheet].iterrows(), 2):
        t = re.sub(r'\s+', ' ', str(p.texte)).strip()
        vals = [i - 1, p.venue, p.orateur, t[:3000] + ('…' if len(t) > 3000 else ''), p.position, p.categorie]
        for j, v in enumerate(vals, 1):
            c = rs.cell(i, j, v); c.font = BODY; c.alignment = WRAP; c.border = LINE
        for j in (7, 8):
            c = rs.cell(i, j); c.fill = INPUT; c.font = BODY; c.alignment = WRAP
    dv = DataValidation(type='list', formula1='"Yes,No"', allow_blank=True); rs.add_data_validation(dv)
    dv.add(f'G2:G{CAP + 1}')
    rs.freeze_panes = 'D2'

path = f'{OUT}/ch6_reading_workbook.xlsx'
wb.save(path)
sel[['sheet', 'measure', 'name', 'score', 'n', 'available', 'kept', 'rule']].to_csv(f'{OUT}/ch6_reading_selection.csv', index=False)
print('saved', path)
print(sel[['sheet', 'name', 'score', 'n', 'kept']].to_string(index=False))
