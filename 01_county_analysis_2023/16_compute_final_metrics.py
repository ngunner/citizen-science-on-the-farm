#!/usr/bin/env python3
"""
16_compute_final_metrics.py — derive the manuscript's county-level metrics and verify them.

Added at packaging (September 2026). In the original workflow the last five columns of the
final county table were derived in a spreadsheet from the output of step 15; this script makes
that step explicit and checks it against the shipped `data/CONUS_COUNTIES_WITH_METRICS.csv`.

Input : ../data/contus_counties_updated_optimized.csv   (output of 15_coverage_within_1km.py)
Output: ../data/CONUS_COUNTIES_WITH_METRICS_recomputed.csv

Derived columns (all proportions are fractions, not percent):
  GEOMEAN_SCORE            = cbrt(PERCENT_AGRICULTURE * PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS
                                  * PERCENTAGE_GBIF_OBS_ON_AG_LAND)             # the OEI (Methods 2.4)
  OBSERVATIONAL_DISPARITY  = PERCENT_AGRICULTURE / PERCENTAGE_GBIF_OBS_ON_AG_LAND  # Methods 2.1
      Counties with farmland but zero farmland observations have an undefined (infinite) ratio.
      The shipped table coded these 80 counties (plus 11 counties with no farmland at all) as 0.0 —
      a spreadsheet division-by-zero convention. By default this script writes `inf` for
      farmland-but-no-observations and NaN for no-farmland; pass --legacy-zero to reproduce the
      shipped 0.0 coding exactly. Both "share of counties with disparity > 1" figures are printed.
  AG_AREA_KM2              = PERCENT_AGRICULTURE * AREA_KM2
  COVERED_AG_AREA_KM2      = AG_AREA_KM2 * PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS
  GBIF_AG_OBS_COUNT_2023   = TOTAL_GBIF_OBS_COUNT_2023 * PERCENTAGE_GBIF_OBS_ON_AG_LAND
Renamed: TOTAL_GBIF_OBS_COUNT -> TOTAL_GBIF_OBS_COUNT_2023, POPULATION_DENSITY_KM2 -> POPULATION_DENSITY_2023_KM2
"""
import os, sys, argparse
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
src = os.path.join(DATA, "contus_counties_updated_optimized.csv")
ref = os.path.join(DATA, "CONUS_COUNTIES_WITH_METRICS.csv")
out = os.path.join(DATA, "CONUS_COUNTIES_WITH_METRICS_recomputed.csv")

ap = argparse.ArgumentParser(); ap.add_argument("--legacy-zero", action="store_true",
    help="code undefined disparities (no farmland observations) as 0.0, as in the shipped table")
args = ap.parse_args()

df = pd.read_csv(src, dtype={"FIPS": str})
df["FIPS"] = df["FIPS"].str.zfill(5)
df = df.rename(columns={"TOTAL_GBIF_OBS_COUNT": "TOTAL_GBIF_OBS_COUNT_2023",
                        "POPULATION_DENSITY_KM2": "POPULATION_DENSITY_2023_KM2"})

pa, pc, po = (df["PERCENT_AGRICULTURE"], df["PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS"],
              df["PERCENTAGE_GBIF_OBS_ON_AG_LAND"])
df["GEOMEAN_SCORE"] = np.cbrt(pa * pc * po)
with np.errstate(divide="ignore", invalid="ignore"):
    if args.legacy_zero:
        df["OBSERVATIONAL_DISPARITY"] = np.where(po > 0, pa / po, 0.0)
    else:
        df["OBSERVATIONAL_DISPARITY"] = np.where(po > 0, pa / po, np.where(pa > 0, np.inf, np.nan))
df["AG_AREA_KM2"] = pa * df["AREA_KM2"]
df["COVERED_AG_AREA_KM2"] = df["AG_AREA_KM2"] * pc
df["GBIF_AG_OBS_COUNT_2023"] = (df["TOTAL_GBIF_OBS_COUNT_2023"] * po).round().astype(int)

cols = ["FIPS", "COUNTYNAME", "STATE", "TIME_ZONE", "CWA", "FE_AREA", "LATITUDE", "LONGITUDE",
        "PERCENTAGE_GBIF_OBS_ON_AG_LAND", "PERCENTAGE_OF_AG_LAND_WITHIN_1KM_GBIF_OBS", "PERCENT_AGRICULTURE",
        "GEOMEAN_SCORE", "TOTAL_GBIF_OBS_COUNT_2023", "GBIF_AG_OBS_COUNT_2023", "GBIF_OBS_DENSITY_KM2",
        "OBSERVATIONAL_DISPARITY", "PERCENT_DEVELOPED", "PERCENT_FOREST", "AREA_KM2", "AG_AREA_KM2",
        "COVERED_AG_AREA_KM2", "POPULATION_DENSITY_2023_KM2", "POPULATION_ESTIMATE_2023",
        "MEDIAN_HOUSEHOLD_INCOME_2022", "MEDIAN_HOUSEHOLD_INCOME_PERCENT_OF_STATE_TOTAL_2022",
        "PERCENT_ADULTS_BACHELORS_DEGREE_2023", "PERCENT_POVERTY_2023", "UNEMPLOYMENT_RATE_2023"]
df = df[cols].sort_values("GEOMEAN_SCORE", ascending=False).reset_index(drop=True)
df.to_csv(out, index=False, float_format="%.5f")
print(f"wrote {out}  ({len(df)} counties)")

# ---- headline numbers (Results 3.1, 3.3) ----
print(f"CONUS farmland share      : {df.AG_AREA_KM2.sum()/df.AREA_KM2.sum():.4f}")
print(f"CONUS obs on farmland     : {df.GBIF_AG_OBS_COUNT_2023.sum()/df.TOTAL_GBIF_OBS_COUNT_2023.sum():.4f}")
n_ag = int((pa > 0).sum()); n_gt1 = int(((pa / po.replace(0, np.nan)) > 1).sum()); n_inf = int(((pa > 0) & (po == 0)).sum())
print(f"counties with disparity>1 : {n_gt1/len(df):.4f} of all {len(df)} counties (finite ratios only; the manuscript's 81.7%)")
print(f"  + {n_inf} counties with farmland but zero farmland observations (undefined/infinite ratio)")
print(f"  => {(n_gt1+n_inf)/len(df):.4f} of all counties, or {(n_gt1+n_inf)/n_ag:.4f} of the {n_ag} counties that have any farmland, are under-observed")
print(f"farmland within 1 km      : {df.COVERED_AG_AREA_KM2.sum()/df.AG_AREA_KM2.sum():.4f}")

# ---- verification against the shipped table ----
if os.path.exists(ref):
    r = pd.read_csv(ref, dtype={"FIPS": str}); r["FIPS"] = r["FIPS"].str.zfill(5)
    m = df.merge(r, on="FIPS", suffixes=("", "_ref"))
    print(f"\nverification vs shipped CONUS_COUNTIES_WITH_METRICS.csv ({len(m)} matched rows):")
    worst = 0.0
    for c in cols[8:]:
        a, b = m[c].astype(float), m[c + "_ref"].astype(float)
        d = (a - b).abs()
        both_nan = a.isna() & b.isna()
        one_nan = (a.isna() ^ b.isna()) | (np.isinf(a) ^ np.isinf(b))
        mx = d[~both_nan].max() if (~both_nan).any() else 0.0
        worst = max(worst, mx if np.isfinite(mx) else worst)
        flag = "" if (mx <= 1e-3 and one_nan.sum() == 0) else "   <-- CHECK"
        print(f"  {c:52s} max|diff| = {mx:9.3g}   nan-mismatch = {int(one_nan.sum())}{flag}")
    if not args.legacy_zero:
        print("  (OBSERVATIONAL_DISPARITY mismatches are the 91 undefined ratios coded 0.0 in the shipped table; rerun with --legacy-zero to match exactly)")
