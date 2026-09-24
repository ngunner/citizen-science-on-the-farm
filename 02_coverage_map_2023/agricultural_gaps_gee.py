#!/usr/bin/env python3
# Provenance: copied from `Final Dataset/Coverage Maps/agricultural_gaps_gee.py` (last modified 2025-11-14) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
"""
Agricultural Gaps Analysis - Google Earth Engine Python API
This script identifies agricultural land without observational coverage
Processing time: 2-5 minutes (vs hours locally)

Prerequisites:
    pip install earthengine-api
    earthengine authenticate
"""

import ee
import time

# ========================================
# CONFIGURATION - UPDATE THESE PATHS
# ========================================

# Replace YOUR_USERNAME with your actual GEE username
AG_ASSET = 'users/YOUR_USERNAME/ag_raster'
OBS_ASSET = 'users/YOUR_USERNAME/obs_1km_raster'

# Output settings
OUTPUT_DESCRIPTION = 'agricultural_gaps'
OUTPUT_FOLDER = 'GEE_Outputs'  # Folder in your Google Drive
OUTPUT_SCALE = 30  # 30 meters (matches your input resolution)

# ========================================
# INITIALIZE EARTH ENGINE
# ========================================

print("========================================")
print("Initializing Google Earth Engine...")
print("========================================")

try:
    ee.Initialize()
    print("✓ Earth Engine initialized successfully")
except Exception as e:
    print("✗ Failed to initialize Earth Engine")
    print("  Please run: earthengine authenticate")
    print(f"  Error: {e}")
    exit(1)

# ========================================
# LOAD DATA
# ========================================

print("\n========================================")
print("Loading Assets...")
print("========================================")

try:
    ag_raster = ee.Image(AG_ASSET)
    obs_raster = ee.Image(OBS_ASSET)
    print(f"✓ Loaded: {AG_ASSET}")
    print(f"✓ Loaded: {OBS_ASSET}")
except Exception as e:
    print(f"✗ Error loading assets: {e}")
    print("  Make sure:")
    print("  1. Assets are uploaded to GEE")
    print("  2. Asset paths are correct")
    print("  3. Ingestion tasks are complete")
    exit(1)

# Get projections
ag_proj = ag_raster.projection()
obs_proj = obs_raster.projection()

print("\nAsset Information:")
print(f"  Agriculture CRS: {ag_proj.getInfo()['crs']}")
print(f"  Observation CRS: {obs_proj.getInfo()['crs']}")

# ========================================
# REPROJECT AGRICULTURE RASTER
# ========================================

print("\n========================================")
print("Reprojecting Agriculture Raster...")
print("========================================")
print("Reprojecting to match observation raster...")

start_time = time.time()

# Reproject agriculture raster to match observation raster
# CRITICAL: Use explicit tileScale to avoid "output too large" errors
# For very large rasters, we need to force smaller tiles (256x256)
ag_reprojected = ag_raster.reproject(
    crs=obs_proj,
    scale=OUTPUT_SCALE,
    tileScale=1  # Use smaller tiles (1 = 256x256, 2 = 512x512, etc.)
)

# Alternative approach: Use resample if reproject still fails
# Uncomment below and comment out above if needed:
# ag_reprojected = ag_raster.resample('near').reproject(
#     crs=obs_proj,
#     scale=OUTPUT_SCALE,
#     tileScale=1
# )

print("✓ Reprojection configured with tileScale=1 (256x256 tiles)")
print("  This prevents 'output too large' errors for big rasters")

# ========================================
# IDENTIFY GAPS
# ========================================

print("\n========================================")
print("Identifying Agricultural Gaps...")
print("========================================")

# Create masks using vectorized operations
# Agricultural land = 1
agricultural_mask = ag_reprojected.eq(1)

# Not covered = 0 or null
not_covered_mask = obs_raster.eq(0).Or(obs_raster.mask().Not())

# Gaps = agricultural AND not covered
gaps_image = agricultural_mask.And(not_covered_mask)

# Convert to float for proper output
gaps_image = gaps_image.toFloat()

# Mask out areas where both inputs are null
both_null = ag_reprojected.mask().Not().And(obs_raster.mask().Not())
gaps_image = gaps_image.updateMask(both_null.Not())

print("✓ Gap analysis configured")

# ========================================
# CALCULATE STATISTICS
# ========================================

print("\n========================================")
print("Calculating Statistics...")
print("========================================")
print("This will trigger the actual computation...")

# Get the geometry for statistics (use the observation raster extent)
geometry = obs_raster.geometry()

# Reduce region to get pixel counts
# Note: This computation happens in the cloud
print("  Computing agricultural pixel count...")
ag_count = agricultural_mask.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=geometry,
    scale=OUTPUT_SCALE,
    maxPixels=1e13,
    bestEffort=True
).getInfo()

print("  Computing not covered pixel count...")
not_cov_count = not_covered_mask.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=geometry,
    scale=OUTPUT_SCALE,
    maxPixels=1e13,
    bestEffort=True
).getInfo()

print("  Computing gaps pixel count...")
gaps_count = gaps_image.reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=geometry,
    scale=OUTPUT_SCALE,
    maxPixels=1e13,
    bestEffort=True
).getInfo()

# Extract values (handle potential different band names)
ag_value = list(ag_count.values())[0] if ag_count else 0
not_cov_value = list(not_cov_count.values())[0] if not_cov_count else 0
gaps_value = list(gaps_count.values())[0] if gaps_count else 0

print("\n========================================")
print("Results:")
print("========================================")
print(f"  Agricultural pixels: {ag_value:,.0f}")
print(f"  Not covered pixels: {not_cov_value:,.0f}")
print(f"  Agricultural gaps: {gaps_value:,.0f}")

if ag_value > 0:
    percentage = 100 * gaps_value / ag_value
    print(f"  Percentage of agricultural land without coverage: {percentage:.2f}%")

computation_time = time.time() - start_time
print(f"\n✓ Statistics computed in {computation_time:.1f} seconds")

# ========================================
# EXPORT CONFIGURATION
# ========================================

print("\n========================================")
print("Configuring Export...")
print("========================================")

# Get CRS info for export
crs_info = obs_proj.getInfo()

# Export to Google Drive
task = ee.batch.Export.image.toDrive(
    image=gaps_image,
    description=OUTPUT_DESCRIPTION,
    folder=OUTPUT_FOLDER,
    fileNamePrefix='agricultural_gaps',
    region=geometry,
    scale=OUTPUT_SCALE,
    crs=crs_info['crs'],
    maxPixels=1e13,
    fileFormat='GeoTIFF',
    formatOptions={
        'cloudOptimized': True
    }
)

# Start the export task
print("Starting export task...")
task.start()

print("\n✓ Export task started!")
print(f"  Task ID: {task.id}")
print(f"  Description: {OUTPUT_DESCRIPTION}")
print(f"  Destination: Google Drive/{OUTPUT_FOLDER}/")

# ========================================
# MONITOR EXPORT PROGRESS
# ========================================

print("\n========================================")
print("Monitoring Export Progress...")
print("========================================")
print("You can:")
print("  1. Wait here for completion (script will monitor)")
print("  2. Or press Ctrl+C to exit (task continues in background)")
print("  3. Check status at: https://code.earthengine.google.com/tasks")
print("========================================\n")

try:
    while True:
        status = task.status()
        state = status['state']
        
        if state == 'COMPLETED':
            print(f"✓ Export completed successfully!")
            print(f"  Download from: Google Drive/{OUTPUT_FOLDER}/agricultural_gaps.tif")
            break
        elif state == 'FAILED':
            print(f"✗ Export failed: {status.get('error_message', 'Unknown error')}")
            break
        elif state == 'CANCELLED':
            print("⚠ Export was cancelled")
            break
        else:
            print(f"  Status: {state}... (waiting 30 seconds)")
            time.sleep(30)
            
except KeyboardInterrupt:
    print("\n⚠ Monitoring stopped (task continues in background)")
    print(f"  Check status at: https://code.earthengine.google.com/tasks")
    print(f"  Task ID: {task.id}")

# ========================================
# SUMMARY
# ========================================

total_time = time.time() - start_time

print("\n========================================")
print("Summary")
print("========================================")
print(f"  Total time: {total_time/60:.1f} minutes")
print(f"  Agricultural pixels processed: {ag_value:,.0f}")
print(f"  Gaps identified: {gaps_value:,.0f}")
print(f"  Output: Google Drive/{OUTPUT_FOLDER}/agricultural_gaps.tif")
print("========================================")

print("\n✓ Script complete!")
print("\nNext steps:")
print("  1. Wait for export to complete (check Google Drive)")
print("  2. Download agricultural_gaps.tif")
print("  3. Use in your GIS software or further analysis")
print("\nNote: GEE processing is MUCH faster than local processing!")
print(f"      This took ~{computation_time:.1f}s vs hours locally")


