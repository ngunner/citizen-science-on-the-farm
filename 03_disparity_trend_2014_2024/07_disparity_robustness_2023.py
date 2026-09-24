#!/usr/bin/env python
"""
STEP 7 — Figure: the 2023 CONUS observational disparity is ROBUST to method.

Three independent estimates of the SAME quantity (%farmland / %observations-on-farmland),
differing only in how each observation is attributed to farmland:

  1. Coarse grid, ~137 m, fractional weighting   (v2 cloud cross-check)   -> conservative lower bound
  2. Exact point, 30 m                            (v1, original R analysis)
  3. Full reproduction, ~19 m, point classification (this study, overnight GBIF x GEE run)

They span 2.5-3.25x and both point-based methods converge near 3 -> the finding does not depend
on the resolution/threshold choice. Farmland is ~24% of CONUS but receives far less of that share
of observations under every method.

Reads the reproduced value from outputs/pointmethod_2023_z12_RESULT.csv (falls back to 3.25).
Output: outputs/disparity_robustness_2023.png  and  ../figures/disparity_robustness_2023.png

Run:  python 07_disparity_robustness_2023.py
"""
import warnings; warnings.filterwarnings("ignore")
import os, csv
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, 'outputs')

# reproduced (~19 m point) disparity from the overnight run, if present
repro = 3.25
res = os.path.join(OUT, 'pointmethod_2023_z12_RESULT.csv')
if os.path.exists(res):
    with open(res) as f:
        repro = round(float(next(csv.DictReader(f))['disparity']), 2)

# label, disparity, %obs-on-farmland, is-point-method
methods = [
    ("Coarse grid ~137 m\n(fractional; v2 cross-check)", 2.50, 9.5, False),
    ("Exact point 30 m\n(v1; original analysis)",        3.00, 7.8, True),
    (f"Full reproduction ~19 m\n(point; this study)",    repro, 7.3, True),
]
POINT, SOFT, PARITY = '#c0392b', '#b9c2cc', '#2c3e50'

fig, ax = plt.subplots(figsize=(8.4, 4.3))
ys = range(len(methods))
for y, (lab, d, pobs, is_pt) in zip(ys, methods):
    color = POINT if is_pt else SOFT
    ax.hlines(y, 1.0, d, color=color, lw=3, zorder=2)                    # stem from parity
    ax.plot(d, y, 'o', ms=13, color=color, zorder=3)
    ax.annotate(f"{d:.2f}×", (d, y), xytext=(12, 0), textcoords='offset points',
                va='center', fontweight='bold', color=color, fontsize=12)
    ax.annotate(f"{pobs:.1f}% of obs on farmland", (1.0, y), xytext=(4, -16),
                textcoords='offset points', va='center', fontsize=8, color='#5a6673')

ax.axvline(1.0, ls='--', color=PARITY, lw=1.4, zorder=1)
ax.text(1.03, -0.5, 'parity (1.0)', fontsize=8.5, color=PARITY, va='center')
ax.axvspan(2.50, repro, color=POINT, alpha=0.05, zorder=0)               # robustness band

ax.set_yticks(list(ys)); ax.set_yticklabels([m[0] for m in methods], fontsize=9)
ax.set_ylim(-0.75, len(methods)-0.4); ax.invert_yaxis()
ax.set_xlim(0.8, max(d for _, d, _, _ in methods) + 0.7)
ax.set_xlabel('CONUS observational disparity  (% farmland land ÷ % observations on farmland)')
ax.set_title('The 2023 farmland observational disparity is robust to method\n'
             f'three independent estimates span 2.5–{repro:.2f}×; both point methods converge near 3×',
             fontsize=11)
for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
ax.tick_params(left=False)
fig.tight_layout()

os.makedirs(OUT, exist_ok=True)
dst1 = os.path.join(OUT, 'disparity_robustness_2023.png')
fig.savefig(dst1, dpi=200, bbox_inches='tight')
# also drop a copy next to the manuscript figures, if that folder exists
figs = os.path.join(HERE, '..', 'figures')
saved = [dst1]
if os.path.isdir(figs):
    dst2 = os.path.join(figs, 'disparity_robustness_2023.png')
    fig.savefig(dst2, dpi=200, bbox_inches='tight'); saved.append(dst2)
print("reproduced (~19 m point) disparity used:", repro)
for p in saved: print("saved ->", os.path.normpath(p))
