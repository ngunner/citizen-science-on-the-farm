#!/usr/bin/env python3
# Provenance: copied from `Final Dataset/Coverage Maps/create_agricultural_gaps.py` (last modified 2025-11-14) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Create a raster showing agricultural land without observational coverage.
Processes data in chunks on-the-fly to handle large rasters efficiently.
"""

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.windows import Window

# Input files
ag_file = 'ag_raster.tif'
obs_file = 'obs_1km_raster_merged.tif'
output_file = 'agricultural_gaps.tif'

print("Step 1: Reading metadata from both rasters...")
with rasterio.open(obs_file) as obs_src:
    obs_profile = obs_src.profile.copy()
    obs_crs = obs_src.crs
    obs_transform = obs_src.transform
    obs_shape = obs_src.shape
    
    print(f"  Observation raster: {obs_shape[0]} x {obs_shape[1]}")
    print(f"  CRS: {obs_crs}")
    print(f"  Resolution: {obs_src.res}")

with rasterio.open(ag_file) as ag_src:
    ag_crs = ag_src.crs
    ag_transform = ag_src.transform
    print(f"  Agriculture raster: {ag_src.shape[0]} x {ag_src.shape[1]}")
    print(f"  Original CRS: {ag_crs}")

print("\nStep 2 & 3: Processing rasters in chunks...")
print("  (Reprojecting agriculture data on-the-fly and identifying gaps)")
# Process in chunks to manage memory and disk space
chunk_size = 2000  # Process 2000 rows at a time
agricultural_count = 0
not_covered_count = 0
gaps_count = 0

# Create output file
output_profile = obs_profile.copy()
output_profile.update({
    'dtype': np.float32,
    'nodata': np.nan,
    'compress': 'lzw'
})

with rasterio.open(obs_file) as obs_src, \
     rasterio.open(ag_file) as ag_src, \
     rasterio.open(output_file, 'w', **output_profile) as dst:
    
    for i in range(0, obs_shape[0], chunk_size):
        rows = min(chunk_size, obs_shape[0] - i)
        window = Window(0, i, obs_shape[1], rows)
        
        # Read observation chunk
        obs_chunk = obs_src.read(1, window=window)
        
        # Reproject agriculture data for this chunk
        ag_chunk = np.empty((rows, obs_shape[1]), dtype=np.float32)
        ag_chunk.fill(np.nan)
        
        reproject(
            source=rasterio.band(ag_src, 1),
            destination=ag_chunk,
            src_transform=ag_transform,
            src_crs=ag_crs,
            dst_transform=obs_src.window_transform(window),
            dst_crs=obs_crs,
            resampling=Resampling.nearest,  # Use nearest neighbor for binary data
            dst_nodata=np.nan
        )
        
        # Create output chunk
        gaps_chunk = np.zeros((rows, obs_shape[1]), dtype=np.float32)
        
        # Identify agricultural land without coverage
        # Agriculture = 1, Observation = 0 or NaN
        agricultural_mask = (ag_chunk == 1)
        not_covered_mask = (obs_chunk == 0) | np.isnan(obs_chunk)
        gaps_mask = agricultural_mask & not_covered_mask
        
        gaps_chunk[gaps_mask] = 1
        
        # Set areas outside valid data to NaN
        both_nan = np.isnan(ag_chunk) & np.isnan(obs_chunk)
        gaps_chunk[both_nan] = np.nan
        
        # Write chunk
        dst.write(gaps_chunk, 1, window=window)
        
        # Update counts
        agricultural_count += np.sum(agricultural_mask)
        not_covered_count += np.sum(not_covered_mask)
        gaps_count += np.sum(gaps_mask)
        
        if (i // chunk_size) % 10 == 0:
            print(f"  Processed {i + rows}/{obs_shape[0]} rows...")

print(f"\nResults:")
print(f"  Agricultural pixels: {agricultural_count:,}")
print(f"  Not covered pixels: {not_covered_count:,}")
print(f"  Agricultural gaps (ag=1, obs=0/NaN): {gaps_count:,}")
if agricultural_count > 0:
    print(f"  Percentage of agricultural land without coverage: {100 * gaps_count / agricultural_count:.2f}%")

print(f"\nSuccess! Output saved to: {output_file}")
print(f"Output statistics:")
print(f"  - Shape: {obs_shape[0]} x {obs_shape[1]}")
print(f"  - Pixels with value 1 (agricultural gaps): {gaps_count:,}")
print(f"  - CRS: {obs_crs}")
print(f"  - Resolution: 30m x 30m")

