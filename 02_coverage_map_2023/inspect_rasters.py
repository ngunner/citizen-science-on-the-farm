#!/usr/bin/env python3
# Provenance: copied from `Figures/Neglected Ag/inspect_rasters.py` (last modified 2025-11-17) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Script to inspect raster files and check their value ranges.
This helps verify the correct values are being used in the GEE script.
"""

import rasterio
import numpy as np
from collections import Counter

def inspect_raster(filepath, name):
    """Inspect a raster file and print statistics about its values."""
    print(f"\n{'='*60}")
    print(f"Inspecting: {name}")
    print(f"File: {filepath}")
    print(f"{'='*60}")
    
    try:
        with rasterio.open(filepath) as src:
            # Get raster info
            print(f"\nRaster Info:")
            print(f"  Shape: {src.shape}")
            print(f"  CRS: {src.crs}")
            print(f"  Transform: {src.transform}")
            print(f"  Data type: {src.dtypes[0]}")
            print(f"  No data value: {src.nodata}")
            print(f"  Number of bands: {src.count}")
            
            # Read all bands - sample to avoid memory issues
            for band_idx in range(1, src.count + 1):
                print(f"\n  Band {band_idx}:")
                
                # Sample the raster (every Nth pixel) to avoid memory issues
                # Read in blocks and sample
                sample_factor = max(1, min(100, src.width // 1000))  # Sample more for large rasters
                print(f"    Sampling every {sample_factor} pixels to manage memory...")
                
                # Read a representative sample
                window_size = min(5000, src.width, src.height)
                window = rasterio.windows.Window(0, 0, window_size, window_size)
                data_sample = src.read(band_idx, window=window)
                
                # Also sample from different regions
                if src.width > window_size or src.height > window_size:
                    # Sample from center
                    center_x = src.width // 2
                    center_y = src.height // 2
                    center_window = rasterio.windows.Window(
                        max(0, center_x - window_size//2),
                        max(0, center_y - window_size//2),
                        window_size, window_size
                    )
                    center_sample = src.read(band_idx, window=center_window)
                    data_sample = np.concatenate([data_sample.flatten(), center_sample.flatten()])
                else:
                    data_sample = data_sample.flatten()
                
                # Mask no-data values
                if src.nodata is not None:
                    valid_data = data_sample[data_sample != src.nodata]
                    print(f"    No-data pixels in sample: {np.sum(data_sample == src.nodata)}")
                else:
                    valid_data = data_sample
                
                if len(valid_data) > 0:
                    # Get unique values and their counts
                    unique_vals, counts = np.unique(valid_data, return_counts=True)
                    
                    print(f"    Sample size: {len(valid_data):,} pixels")
                    print(f"    Min value: {np.min(valid_data)}")
                    print(f"    Max value: {np.max(valid_data)}")
                    print(f"    Mean value: {np.mean(valid_data):.4f}")
                    print(f"    Median value: {np.median(valid_data):.4f}")
                    
                    print(f"\n    Unique values found in sample (top 20 by frequency):")
                    # Sort by frequency
                    value_counts = list(zip(unique_vals, counts))
                    value_counts.sort(key=lambda x: x[1], reverse=True)
                    
                    for val, count in value_counts[:20]:
                        percentage = (count / len(valid_data)) * 100
                        print(f"      Value {val}: {count:,} pixels ({percentage:.2f}%)")
                    
                    if len(value_counts) > 20:
                        print(f"      ... and {len(value_counts) - 20} more unique values")
                    
                    # Check specifically for value 3 (agricultural) and value 0 (not observed)
                    if 3 in unique_vals:
                        idx = np.where(unique_vals == 3)[0][0]
                        print(f"\n    ✓ Value 3 (agricultural) found: {counts[idx]:,} pixels ({counts[idx]/len(valid_data)*100:.2f}%)")
                    else:
                        print(f"\n    ✗ Value 3 (agricultural) NOT found in sample!")
                        print(f"      This suggests the script may be looking for the wrong value.")
                else:
                    print(f"    No valid data in this band")
                    
    except Exception as e:
        print(f"Error reading raster: {e}")

if __name__ == "__main__":
    import os
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(script_dir, "Raw")
    
    # Inspect agricultural raster
    ag_raster = os.path.join(raw_dir, "ag_raster.tif")
    if os.path.exists(ag_raster):
        inspect_raster(ag_raster, "Agricultural Raster")
    else:
        print(f"Warning: {ag_raster} not found")
    
    # Inspect observation raster
    obs_raster = os.path.join(raw_dir, "obs_1km_raster_merged.tif")
    if os.path.exists(obs_raster):
        inspect_raster(obs_raster, "Observation Raster")
    else:
        print(f"Warning: {obs_raster} not found")
    
    print(f"\n{'='*60}")
    print("Inspection complete!")
    print(f"{'='*60}\n")

