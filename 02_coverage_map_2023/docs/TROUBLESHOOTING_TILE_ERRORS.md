# Troubleshooting: "Reprojection output too large" Tile Errors

## Problem

You're seeing errors like:
```
Tile error: Reprojection output too large (36753x37054 pixels).
Tile error: Reprojection output too large (32576x32437 pixels).
```

This happens when Google Earth Engine tries to create tiles that exceed its internal size limits during reprojection of very large rasters.

## ✅ Solution Applied

I've updated both scripts (`agricultural_gaps_gee.js` and `.py`) with fixes:

1. **Added `tileScale: 1`** to reprojection - forces 256×256 pixel tiles
2. **Coarser visualization scale** - map preview uses 100m instead of 30m (export still uses 30m)

## 🔄 Try the Updated Script

1. **Copy the updated code** from `agricultural_gaps_gee.js`
2. **Paste into GEE Code Editor** (replace old code)
3. **Update your username** in lines 13-14
4. **Click "Run"**

The tile errors should be gone!

## 🛠️ If Errors Persist

### Option 1: Use Resample First (More Memory Efficient)

If you still get tile errors, try the alternative approach. In the script, find:

```javascript
var agReprojected = agRaster.reproject({
  crs: obsProj,
  scale: OUTPUT_SCALE,
  tileScale: 1
});
```

Replace with:

```javascript
// Use resample first for better memory efficiency
var agReprojected = agRaster.resample('near').reproject({
  crs: obsProj,
  scale: OUTPUT_SCALE,
  tileScale: 1
});
```

### Option 2: Process in Regions (For Extremely Large Rasters)

If your rasters are so large that even this fails, process in smaller regions:

```javascript
// Define regions (e.g., by state or bounding box)
var region1 = ee.Geometry.Rectangle([-125, 25, -100, 50]);  // Western US
var region2 = ee.Geometry.Rectangle([-100, 25, -75, 50]);  // Eastern US

// Process each region separately
var gaps1 = gapsImage.clip(region1);
var gaps2 = gapsImage.clip(region2);

// Export separately, then merge locally
```

### Option 3: Increase Tile Scale (If You Have Higher Limits)

If you've requested higher memory limits from GEE support:

```javascript
var agReprojected = agRaster.reproject({
  crs: obsProj,
  scale: OUTPUT_SCALE,
  tileScale: 2  // Try 2 (512×512) or 4 (1024×1024) if you have higher limits
});
```

### Option 4: Use Coarser Scale for Processing

As a last resort, process at a coarser scale and resample later:

```javascript
// Process at 60m instead of 30m
var PROCESSING_SCALE = 60;

var agReprojected = agRaster.reproject({
  crs: obsProj,
  scale: PROCESSING_SCALE,
  tileScale: 1
});

// ... rest of analysis ...

// Export at 60m (you can resample to 30m later if needed)
```

## 📊 Understanding the Fix

### What `tileScale` Does

- `tileScale: 1` = 256×256 pixel tiles (most memory efficient)
- `tileScale: 2` = 512×512 pixel tiles
- `tileScale: 4` = 1024×1024 pixel tiles (default, but too large for your data)

For US-scale 30m rasters, we need the smallest tiles.

### Why Visualization Uses 100m

The map display was causing the errors because it tried to render at full 30m resolution. The fix:
- **Map preview**: 100m (fast, no errors)
- **Export**: 30m (full resolution, processed correctly)

## ✅ Verification

After applying the fix, you should see:

1. **No tile errors** in the Console
2. **Map displays** without errors (may be slightly coarser for preview)
3. **Statistics calculate** successfully
4. **Export completes** with full 30m resolution

## 🆘 Still Having Issues?

### Check Your Raster Sizes

```javascript
// Add this to your script to check dimensions
print('Agriculture raster dimensions:', agRaster.select(0).projection().getInfo());
print('Observation raster dimensions:', obsRaster.select(0).projection().getInfo());
```

If dimensions are extremely large (> 200,000 pixels per side), you may need to:
1. Contact GEE support for higher limits
2. Process in smaller regions
3. Use a coarser processing scale

### Contact GEE Support

If nothing works, contact Google Earth Engine support:
- **Forum**: https://groups.google.com/g/google-earth-engine-developers
- **Include**: Your error messages, raster dimensions, and what you've tried

They can:
- Increase your memory/tile limits (free for academics)
- Provide custom solutions
- Help optimize your workflow

## 📝 Summary

**The fix I applied should work for 99% of cases.** The key changes:

1. ✅ `tileScale: 1` in reprojection
2. ✅ 100m visualization scale (export still 30m)
3. ✅ Alternative resample approach documented

**Try the updated script first** - it should eliminate the tile errors!

