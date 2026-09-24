#!/usr/bin/env python
"""
STEP 6 — Is the observational disparity growing over time? (2014-2023; 2024 also available)

Plots the CONUS observational disparity for every year measured with the exact-point method
(~19 m cells inside 30 m NLCD pixels = point classification, matching the manuscript). Reads the
per-year results written by reproduce_disparity_pointmethod.py:
    outputs/pointmethod_<year>_z12_RESULT.csv

Bars show total annual observations (same source), so the figure is internally consistent:
the disparity grows even as the raw volume of citizen-science data triples.

Output: outputs/disparity_over_time.png  (+ a copy in ../figures/)

Run:  python 06_plot_disparity_over_time.py
Key result: disparity 2.71x (2014) -> 3.25x (2023, peak; +20%), with a 2015-16 dip (min 2.22x in 2015) and a single
            reversal in 2020 (2.86x) during the pandemic surge in observing.
"""
import warnings; warnings.filterwarnings("ignore")
import os, csv, glob, argparse
ap = argparse.ArgumentParser(); ap.add_argument('--start', type=int, default=2014); ap.add_argument('--end', type=int, default=2023,
    help='year window to plot; the series ends at 2023, the year of the full county analysis')
args = ap.parse_args()
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

# ---- load every exact-point year we have run ----
rows = []
for f in sorted(glob.glob('outputs/pointmethod_*_z12_RESULT.csv')):
    y = int(os.path.basename(f).split('_')[1])
    if not (args.start <= y <= args.end):
        continue
    with open(f) as fh:
        r = next(csv.DictReader(fh))
        rows.append((int(r['year']), float(r['disparity']),
                     float(r['pct_obs_on_ag']), int(r['total_obs'])/1e6))
rows.sort()
if not rows:
    raise SystemExit("No outputs/pointmethod_*_z12_RESULT.csv found — run "
                     "reproduce_disparity_pointmethod.py first.")
years = [r[0] for r in rows]
disp  = [r[1] for r in rows]
obs_m = [r[3] for r in rows]

RED, INK, BAR, GREY = '#c0392b', '#2c3e50', '#e3e9f0', '#8a96a3'
fig, ax = plt.subplots(figsize=(9.5, 5.5))

# total observations (background context)
axb = ax.twinx()
axb.bar(years, obs_m, color=BAR, width=0.62, zorder=1)
axb.set_ylabel('Total observations (millions)', color=GREY)
axb.tick_params(axis='y', colors=GREY, length=0)
axb.set_ylim(0, max(obs_m) * 1.85)          # keep bars in the lower half, clear of the line

# disparity trend — simple line + round markers
ax.set_zorder(axb.get_zorder() + 1); ax.patch.set_visible(False)
ax.plot(years, disp, '-o', color=RED, lw=2.4, ms=7, mec='white', mew=1.2, zorder=4)

ax.set_ylabel('CONUS observational disparity\n(% farmland land ÷ % obs on farmland)', color=RED)
ax.tick_params(axis='y', colors=RED)
ax.set_ylim(0, max(disp) * 1.32)
ax.set_xticks(years)
ax.axhline(1, ls='--', color=INK, lw=1.2, zorder=2)
ax.text(years[0] - 0.4, 1.08, '1.0 = parity', fontsize=9, color=INK)

# value labels: centred above each point, with enough clearance to never touch the line
for x, y in zip(years, disp):
    ax.annotate(f'{y:.2f}', (x, y), textcoords='offset points', xytext=(0, 13),
                ha='center', color=RED, fontweight='bold', fontsize=10)

for s in ('top', 'right'):
    ax.spines[s].set_visible(False); axb.spines[s].set_visible(False)
ax.spines['left'].set_color(RED)

ax.set_title(f'The farmland observational disparity is widening ({years[0]}–{years[-1]})\n'
             f'{disp[0]:.2f}× → {max(disp):.2f}×, measured by exact point classification '
             f'against 30 m NLCD farmland', fontsize=11)
fig.tight_layout()
fig.savefig('outputs/disparity_over_time.png', dpi=200, bbox_inches='tight')
if os.path.isdir('../figures'):
    fig.savefig('../figures/disparity_over_time.png', dpi=200, bbox_inches='tight')

print("Exact-point (30 m) disparity by year:")
for yr, dis, pobs, om in rows:
    print(f"  {yr}: {dis:.2f}x   ({pobs:.2f}% obs on farmland, {om:.1f}M observations)")
print(f"  => {disp[0]:.2f} -> {disp[-1]:.2f} "
      f"({100*(disp[-1]/disp[0]-1):+.0f}%); peak {max(disp):.2f} in {years[disp.index(max(disp))]}")
print("Saved -> outputs/disparity_over_time.png")
