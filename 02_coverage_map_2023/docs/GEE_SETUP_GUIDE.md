# Google Earth Engine Setup Guide for Agricultural Gaps Analysis

## Why Google Earth Engine?

For US-scale 30m rasters (~130,000 x 80,000 pixels = 10+ billion pixels), Google Earth Engine offers:

- **Processing time**: 2-5 minutes (vs hours locally)
- **No local resources needed**: All computation happens in Google's cloud
- **Automatic parallelization**: Distributed across Google's infrastructure
- **No memory limitations**: Can handle any size raster

## Prerequisites

### 1. Create a Google Earth Engine Account (Free)

1. Go to https://earthengine.google.com/
2. Click "Sign Up" in the top right
3. Sign in with your Google account
4. Register for Earth Engine access (usually approved within 1-2 days for academic use)
5. Indicate this is for "Academic Research" - approval is typically instant for .edu emails

### 2. Install Google Earth Engine Tools

#### Option A: Use Earth Engine Code Editor (Easiest - No Installation)
- Go to https://code.earthengine.google.com/
- This is a web-based IDE, no installation needed
- Use JavaScript API (provided script)

#### Option B: Use Python API (For Local Development)
```bash
pip install earthengine-api
```

Then authenticate:
```bash
earthengine authenticate
```

## Uploading Your Rasters to Google Earth Engine

Since your rasters are local files, you need to upload them as Earth Engine assets.

### Method 1: Using the Web Interface (Recommended for First-Time Users)

1. **Go to the Earth Engine Asset Manager**
   - Navigate to https://code.earthengine.google.com/
   - Click on "Assets" tab in the left panel

2. **Upload Your Rasters**
   - Click "NEW" button → "Image Upload"
   - For **Source files**, click "SELECT" and choose your files:
     - `ag_raster.tif`
     - `obs_1km_raster_merged.tif`
   - For **Asset ID**, name them:
     - `users/YOUR_USERNAME/ag_raster`
     - `users/YOUR_USERNAME/obs_1km_raster`
   - Click "UPLOAD"

3. **Wait for Upload and Ingestion**
   - Large files may take 30 minutes to several hours to upload and process
   - You'll receive an email when complete
   - Check progress in the "Tasks" tab

### Method 2: Using Command Line (For Advanced Users)

```bash
# Install gcloud CLI first (if not already installed)
# Download from: https://cloud.google.com/sdk/docs/install

# Authenticate
earthengine authenticate

# Upload agriculture raster
earthengine upload image --asset_id=users/YOUR_USERNAME/ag_raster ag_raster.tif

# Upload observation raster
earthengine upload image --asset_id=users/YOUR_USERNAME/obs_1km_raster obs_1km_raster_merged.tif

# Check upload status
earthengine task list
```

### Method 3: Using Google Cloud Storage (For Very Large Files > 10GB)

If your files are very large:

1. **Upload to Google Cloud Storage first**
   ```bash
   # Install gsutil
   pip install gsutil
   
   # Upload to GCS bucket
   gsutil cp ag_raster.tif gs://your-bucket-name/
   gsutil cp obs_1km_raster_merged.tif gs://your-bucket-name/
   ```

2. **Then ingest to Earth Engine**
   ```bash
   earthengine upload image --asset_id=users/YOUR_USERNAME/ag_raster \
     gs://your-bucket-name/ag_raster.tif
   
   earthengine upload image --asset_id=users/YOUR_USERNAME/obs_1km_raster \
     gs://your-bucket-name/obs_1km_raster_merged.tif
   ```

## Verify Your Assets

Once uploaded, verify in the Code Editor:

```javascript
// Load your assets
var agRaster = ee.Image('users/YOUR_USERNAME/ag_raster');
var obsRaster = ee.Image('users/YOUR_USERNAME/obs_1km_raster');

// Print information
print('Agriculture Raster:', agRaster);
print('Observation Raster:', obsRaster);

// Display on map
Map.addLayer(agRaster, {min: 0, max: 1}, 'Agriculture');
Map.addLayer(obsRaster, {min: 0, max: 1}, 'Observations');
Map.centerObject(agRaster, 5);
```

## Running the Analysis

### Option 1: JavaScript in Code Editor (Recommended)

1. Open https://code.earthengine.google.com/
2. Copy the contents of `agricultural_gaps_gee.js` into the editor
3. Update the asset paths with your username
4. Click "Run"
5. Export the result (follows the script instructions)

### Option 2: Python API

1. Use the `agricultural_gaps_gee.py` script
2. Update asset paths in the script
3. Run: `python agricultural_gaps_gee.py`

## Expected Timeline

| Step | Time |
|------|------|
| Account approval | Instant - 2 days (usually instant for .edu) |
| Upload rasters | 30 min - 3 hours (depends on file size & internet) |
| Run analysis | 2-5 minutes |
| Export result | 5-15 minutes |
| **Total** | **~1-4 hours (mostly unattended)** |

Compare to:
- Python (original): 4-8+ hours of active processing
- R (optimized): 10-30 minutes (but still uses your local machine)

## Troubleshooting

### "User memory limit exceeded"
Your rasters might be extremely large. Solutions:
- Process in tiles using `.reproject()` with specific scale
- Contact GEE to request higher limits (free for academic users)

### "Asset not found"
- Make sure asset ingestion is complete (check Tasks tab)
- Verify the asset path matches your username exactly
- Asset paths are case-sensitive

### "Computation timeout"
- Add `.reproject()` with explicit scale to force lazy evaluation
- Break into smaller regions using `.clip()`

## Cost

Google Earth Engine is **FREE for:**
- Academic research
- Education
- Non-profit organizations
- Non-commercial use

Your use case (PhD research) qualifies for free access with high quotas.

## Next Steps

1. **Register for GEE** (if not already done)
2. **Upload your rasters** using Method 1
3. **Run the provided scripts** (`agricultural_gaps_gee.js` or `.py`)
4. **Export and download** the result

The processing itself will take only 2-5 minutes once your assets are uploaded!


