// Provenance: copied from `Final Dataset/Coverage Maps/agricultural_gaps_gee.js` (last modified 2025-11-14) into the
// Citizen Science on the Farm replication package, September 2026.
// Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
// ========================================
// Agricultural Gaps Analysis - Google Earth Engine
// ========================================
// This script identifies agricultural land without observational coverage
// Processing time: 2-5 minutes (vs hours locally)
// Run in: https://code.earthengine.google.com/

// ========================================
// CONFIGURATION - UPDATE THESE PATHS
// ========================================

// Replace YOUR_USERNAME with your actual GEE username
var AG_ASSET = 'users/YOUR_USERNAME/ag_raster';
var OBS_ASSET = 'users/YOUR_USERNAME/obs_1km_raster';

// Output settings
var OUTPUT_DESCRIPTION = 'agricultural_gaps';
var OUTPUT_FOLDER = 'GEE_Outputs';  // Folder in your Google Drive
var OUTPUT_SCALE = 30;  // 30 meters (matches your input resolution)

// ========================================
// LOAD DATA
// ========================================

print('========================================');
print('Loading Assets...');
print('========================================');

var agRaster = ee.Image(AG_ASSET);
var obsRaster = ee.Image(OBS_ASSET);

print('Agriculture Raster:', agRaster);
print('Observation Raster:', obsRaster);

// Get projections
var agProj = agRaster.projection();
var obsProj = obsRaster.projection();

print('Agriculture CRS:', agProj);
print('Observation CRS:', obsProj);

// ========================================
// REPROJECT AGRICULTURE RASTER
// ========================================

print('\n========================================');
print('Reprojecting Agriculture Raster...');
print('========================================');
print('Reprojecting to match observation raster...');
print('Using smaller tiles to avoid memory limits...');

// Reproject agriculture raster to match observation raster
// CRITICAL: Use explicit tileSize to avoid "output too large" errors
// For very large rasters, we need to force smaller tiles (256x256)
var agReprojected = agRaster.reproject({
  crs: obsProj,
  scale: OUTPUT_SCALE,
  tileScale: 1  // Use smaller tiles (1 = 256x256, 2 = 512x512, etc.)
});

// Alternative approach: Use resample if reproject still fails
// This forces pixel-by-pixel resampling which is more memory efficient
// Uncomment the line below and comment out the reproject above if needed:
// var agReprojected = agRaster.resample('near').reproject({
//   crs: obsProj,
//   scale: OUTPUT_SCALE,
//   tileScale: 1
// });

print('✓ Reprojection configured with tileScale=1 (256x256 tiles)');
print('  This prevents "output too large" errors for big rasters');

// ========================================
// IDENTIFY GAPS
// ========================================

print('\n========================================');
print('Identifying Agricultural Gaps...');
print('========================================');

// Create masks using vectorized operations
// Agricultural land = 1
var agriculturalMask = agReprojected.eq(1);

// Not covered = 0 or null
var notCoveredMask = obsRaster.eq(0).or(obsRaster.mask().not());

// Gaps = agricultural AND not covered
var gapsImage = agriculturalMask.and(notCoveredMask);

// Convert to float for proper output
gapsImage = gapsImage.toFloat();

// Mask out areas where both inputs are null
var bothNull = agReprojected.mask().not().and(obsRaster.mask().not());
gapsImage = gapsImage.updateMask(bothNull.not());

print('✓ Gap analysis configured');

// ========================================
// CALCULATE STATISTICS
// ========================================

print('\n========================================');
print('Calculating Statistics...');
print('========================================');
print('This will trigger the actual computation...');

// Get the geometry for statistics (use the observation raster extent)
var geometry = obsRaster.geometry();

// Reduce region to get pixel counts
// Note: This computation happens in the cloud
var stats = ee.Dictionary({
  agricultural: agriculturalMask.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    scale: OUTPUT_SCALE,
    maxPixels: 1e13,
    bestEffort: true
  }),
  notCovered: notCoveredMask.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    scale: OUTPUT_SCALE,
    maxPixels: 1e13,
    bestEffort: true
  }),
  gaps: gapsImage.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    scale: OUTPUT_SCALE,
    maxPixels: 1e13,
    bestEffort: true
  })
});

// Print statistics (this will take a moment to compute)
stats.evaluate(function(statsDict) {
  print('\n========================================');
  print('Results:');
  print('========================================');
  
  var agCount = statsDict.agricultural.remapped || statsDict.agricultural;
  var notCovCount = statsDict.notCovered.remapped || statsDict.notCovered;
  var gapsCount = statsDict.gaps.remapped || statsDict.gaps;
  
  print('Agricultural pixels:', agCount);
  print('Not covered pixels:', notCovCount);
  print('Agricultural gaps:', gapsCount);
  
  if (agCount > 0) {
    var percentage = 100 * gapsCount / agCount;
    print('Percentage of agricultural land without coverage:', percentage.toFixed(2) + '%');
  }
});

// ========================================
// VISUALIZATION
// ========================================

print('\n========================================');
print('Visualization Setup...');
print('========================================');

// Center map on the data
Map.centerObject(geometry, 5);

// For visualization, we need to use a coarser scale to avoid tile errors
// The export will still use full resolution (30m)
var VISUALIZATION_SCALE = 100;  // 100m for display (faster, no errors)

// Create visualization versions at coarser scale
var agReprojectedViz = agReprojected.reproject({
  crs: obsProj,
  scale: VISUALIZATION_SCALE,
  tileScale: 1
});

var gapsImageViz = gapsImage.reproject({
  crs: obsProj,
  scale: VISUALIZATION_SCALE,
  tileScale: 1
});

// Add layers to map (using visualization versions)
Map.addLayer(agReprojectedViz, {min: 0, max: 1, palette: ['000000', '00FF00']}, 
             'Agriculture (green, 100m preview)', false);
Map.addLayer(obsRaster, {min: 0, max: 1, palette: ['000000', '0000FF']}, 
             'Observations (blue)', false);
Map.addLayer(gapsImageViz, {min: 0, max: 1, palette: ['000000', 'FF0000']}, 
             'Agricultural Gaps (red, 100m preview)', true);

print('✓ Layers added to map');
print('  - Agriculture: Green (100m preview)');
print('  - Observations: Blue');
print('  - Gaps: Red (100m preview)');
print('  NOTE: Map shows 100m preview for speed');
print('  Export will use full 30m resolution');

// ========================================
// EXPORT CONFIGURATION
// ========================================

print('\n========================================');
print('Export Setup...');
print('========================================');
print('To export the results:');
print('1. Click "Tasks" tab in the top right');
print('2. Click "Run" next to "' + OUTPUT_DESCRIPTION + '"');
print('3. Adjust settings if needed (defaults are good)');
print('4. Click "Run" in the dialog');
print('5. Wait 5-15 minutes for export to complete');
print('6. Download from Google Drive/' + OUTPUT_FOLDER);
print('========================================');

// Export to Google Drive
Export.image.toDrive({
  image: gapsImage,
  description: OUTPUT_DESCRIPTION,
  folder: OUTPUT_FOLDER,
  fileNamePrefix: 'agricultural_gaps',
  region: geometry,
  scale: OUTPUT_SCALE,
  crs: obsProj.getInfo().crs,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF',
  formatOptions: {
    cloudOptimized: true
  }
});

print('\n✓ Export task configured!');
print('  Check the Tasks tab to run the export.');

// ========================================
// ALTERNATIVE: Export to Cloud Storage
// ========================================
// Uncomment this if you prefer to export to Google Cloud Storage
// You'll need a GCS bucket first

/*
Export.image.toCloudStorage({
  image: gapsImage,
  description: OUTPUT_DESCRIPTION + '_GCS',
  bucket: 'YOUR_BUCKET_NAME',
  fileNamePrefix: 'agricultural_gaps',
  region: geometry,
  scale: OUTPUT_SCALE,
  crs: obsProj.getInfo().crs,
  maxPixels: 1e13,
  fileFormat: 'GeoTIFF',
  formatOptions: {
    cloudOptimized: true
  }
});
*/

// ========================================
// QUALITY CHECKS
// ========================================

print('\n========================================');
print('Quality Checks...');
print('========================================');

// Sample some points to verify results
var samplePoints = gapsImage.sample({
  region: geometry,
  scale: OUTPUT_SCALE,
  numPixels: 100,
  geometries: true
});

print('Sample of 100 pixels:', samplePoints.limit(10));
print('  (Showing first 10 samples)');

print('\n========================================');
print('Script Complete!');
print('========================================');
print('Next steps:');
print('1. Review the map visualization');
print('2. Check the statistics above');
print('3. Go to Tasks tab and click RUN to export');
print('========================================');


