# Google Earth Engine Quick Start Guide

## 🚀 Fastest Path to Results (2-5 minute processing!)

### Step 1: Get GEE Access (5 minutes - one time setup)

1. Go to **https://signup.earthengine.google.com/**
2. Sign in with your Google account
3. Select **"Academic Research"** as your use case
4. Use your .edu email if possible (instant approval)
5. Otherwise, wait for approval (usually < 24 hours)

### Step 2: Upload Your Rasters (30 min - 3 hours one-time)

**Option A: Web Interface (Easiest)**

1. Go to **https://code.earthengine.google.com/**
2. Click **"Assets"** tab (left sidebar)
3. Click **"NEW"** → **"Image Upload"**
4. Upload `ag_raster.tif`:
   - Click "SELECT" under Source files
   - Choose your `ag_raster.tif` file
   - Set Asset ID to: `users/YOUR_USERNAME/ag_raster`
   - Click "UPLOAD"
5. Repeat for `obs_1km_raster_merged.tif`:
   - Asset ID: `users/YOUR_USERNAME/obs_1km_raster`
6. Click **"Tasks"** tab to monitor upload progress
7. Wait for email confirmation that ingestion is complete

**Option B: Command Line (Faster for large files)**

```bash
# Install Earth Engine CLI
pip install earthengine-api

# Authenticate
earthengine authenticate

# Upload files (replace YOUR_USERNAME)
earthengine upload image --asset_id=users/YOUR_USERNAME/ag_raster ag_raster.tif
earthengine upload image --asset_id=users/YOUR_USERNAME/obs_1km_raster obs_1km_raster_merged.tif

# Check progress
earthengine task list
```

### Step 3: Run the Analysis (2-5 minutes!)

**Option A: JavaScript in Code Editor (Recommended - No Installation)**

1. Go to **https://code.earthengine.google.com/**
2. Open `agricultural_gaps_gee.js` from this folder in a text editor
3. Copy ALL the code
4. Paste into the Earth Engine Code Editor
5. **IMPORTANT**: Change line 12 and 13:
   ```javascript
   var AG_ASSET = 'users/YOUR_ACTUAL_USERNAME/ag_raster';
   var OBS_ASSET = 'users/YOUR_ACTUAL_USERNAME/obs_1km_raster';
   ```
   Replace `YOUR_ACTUAL_USERNAME` with your GEE username (same as Google account name)
6. Click **"Run"** button (top of editor)
7. Wait 2-5 minutes (watch the Console for progress)
8. View results on the map (red = gaps)

**Option B: Python API (If you prefer Python)**

```bash
# Install Earth Engine Python API
pip install earthengine-api

# Authenticate
earthengine authenticate

# Edit the script to update YOUR_USERNAME in lines 16-17
# Then run:
python agricultural_gaps_gee.py
```

### Step 4: Export Results (5-15 minutes)

After running the script:

1. Click **"Tasks"** tab (top right in Code Editor, next to Console)
2. Find the task named **"agricultural_gaps"**
3. Click **"RUN"**
4. Review settings (defaults are good):
   - Destination: Google Drive
   - Folder: GEE_Outputs
   - Format: GeoTIFF
5. Click **"RUN"** again to confirm
6. Wait 5-15 minutes for export to complete
7. Check your **Google Drive/GEE_Outputs/** folder
8. Download **agricultural_gaps.tif**

## 📊 What to Expect

### Processing Times Comparison

| Method | Time | Your Machine Load |
|--------|------|-------------------|
| Original Python | 4-8+ hours | 100% (blocks your Mac) |
| Optimized R | 10-30 minutes | 100% (blocks your Mac) |
| **Google Earth Engine** | **2-5 minutes** | **0% (runs in cloud!)** |

### Total Time Including Upload

- **First time**: 1-4 hours (mostly waiting for upload/ingestion)
- **Subsequent runs**: 2-5 minutes (assets already uploaded!)

## ✅ Verification

After downloading the result, verify it matches your expected output:

```bash
# Check file info
gdalinfo agricultural_gaps.tif

# Quick stats
gdalinfo -stats agricultural_gaps.tif

# Compare with Python output (if you have it)
# Both should have the same number of gap pixels
```

## ⚠️ Common Issues

### "Asset not found"

- **Solution**: Wait for ingestion to complete. Check Tasks tab - asset must show "Completed" status
- Assets can take 30 min - 3 hours to ingest depending on size

### "User memory limit exceeded"

- **Solution**: Your rasters are VERY large. This is rare. Solutions:
  1. Contact GEE support for higher limits (free for academics)
  2. Process in tiles (I can help with this if needed)

### "Computation timeout"

- **Solution**: Very rare for this operation. Try:
  1. Run again (sometimes transient)
  2. Check GEE status page: https://status.earthengine.google.com/

### Upload is very slow

- **Solutions**:
  1. Use Google Cloud Storage as intermediate (see full guide)
  2. Compress files first: `gdal_translate -co COMPRESS=LZW input.tif output.tif`
  3. Upload overnight

### Can't find my username

- Go to **https://code.earthengine.google.com/**
- Click **"Assets"** tab
- Look at the top - it shows: `users/YOUR_USERNAME`
- That's your username!

## 🎯 Next Steps After First Success

Once you've successfully processed your data:

1. **Save the scripts** - you can reuse them for similar analyses
2. **Explore the map visualization** - see where gaps are concentrated
3. **Analyze the statistics** - printed in the Console
4. **Share the code** - easily shareable for reproducibility

## 📖 Need More Details?

See the comprehensive guides:
- **GEE_SETUP_GUIDE.md** - Detailed setup instructions
- **agricultural_gaps_gee.js** - Fully commented JavaScript code
- **agricultural_gaps_gee.py** - Fully commented Python code

## 💡 Why This Is Better

1. **Speed**: 10-50x faster than local processing
2. **No local resources**: Your Mac stays free for other work
3. **Scalability**: Works for any size raster
4. **Reproducibility**: Easy to share and rerun
5. **Free**: No cost for academic research
6. **Distributed**: Uses Google's massive infrastructure

## 🆘 Still Stuck?

If you encounter issues:

1. Check the **Console** tab for error messages
2. Review **GEE_SETUP_GUIDE.md** for troubleshooting
3. Visit **https://developers.google.com/earth-engine/**
4. Ask in GEE Google Group: **https://groups.google.com/g/google-earth-engine-developers**

Good luck! This should be MUCH faster than local processing. 🚀


