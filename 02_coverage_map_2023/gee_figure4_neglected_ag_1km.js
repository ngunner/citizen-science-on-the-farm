// Provenance: copied from `Figures/Neglected Ag/gee.js` (last modified 2025-11-17) into the
// Citizen Science on the Farm replication package, September 2026.
// Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
// This is the Earth Engine script used for the published Figure 4 (1 km grid; EPSG:3857).
/**
 * GEE Script to Identify Gaps in Observation Coverage
 * * Goal: Find pixels that are Agricultural (value 1) AND NOT Observationally Covered (value 0).
 * * Verified: Agricultural raster uses 1.0 for agriculture, 0.0 for non-agriculture
 * * Verified: Observation raster uses 0.0 for not observed, 1.0 for observed
 */

// --- 1. Define Assets and Parameters ---

// Define the asset paths from your previous interaction (IMPORTING FROM ASSETS)
// var raster1 = ee.Image('projects/nicholas-gunner/assets/ag_raster'); // Agricultural Raster
// var raster2 = ee.Image('projects/nicholas-gunner/assets/obs_1km_raster_merged'); // Observation Raster

// Define standard parameters
// FIXED: Use EPSG:3857 (Web Mercator) which uses meters, so 1000 = 1000 meters
// Alternative: Use EPSG:4326 with scale: 0.009 (~1km in degrees at equator)
var targetResolution = 1000; // meters
var targetCRS = 'EPSG:3857'; // Web Mercator (meters-based projection)
var agriculturalValue = 1; // FIXED: The agricultural raster uses 1.0 (not 3) to represent agriculture

// --- 2. Reprojection and Resampling ---

// Reproject Raster 1 (Agricultural)
var reprojected1 = raster1.reproject({
  crs: targetCRS,
  scale: targetResolution,
}).rename('AgRaster_3857'); 

// Reproject Raster 2 (Observation Coverage)
var reprojected2 = raster2.reproject({
  crs: targetCRS,
  scale: targetResolution,
}).rename('ObsRaster_3857');


// --- 2.5. Value Inspection (Debug) ---
// Check actual value ranges to verify data matches assumptions
print('=== Value Inspection ===');
print('Agricultural Raster - Unique values:', reprojected1.reduceRegion({
  reducer: ee.Reducer.frequencyHistogram(),
  scale: targetResolution,
  maxPixels: 1e9
}));
print('Observation Raster - Unique values:', reprojected2.reduceRegion({
  reducer: ee.Reducer.frequencyHistogram(),
  scale: targetResolution,
  maxPixels: 1e9
}));


// --- 3. Binary Thresholding and Logical Analysis (The Key Step) ---

// A. Create Binary Mask for Agricultural Pixels
var is_agricultural = reprojected1.eq(agriculturalValue)
  .rename('Is_Ag');

// B. Create Binary Mask for *NOT* Observationally Covered Pixels
// If the observation count is ZERO, then it is NOT covered.
// This is the Logical NOT operation.
var is_NOT_covered = reprojected2.eq(0)
  .rename('Is_NOT_Covered');

// C. Logical AND Operation (Intersection of Ag AND Not Observed)
// Multiply the two binary masks to find areas where BOTH conditions are met.
// This is equivalent to: (A AND NOT B)
var gap_mask = is_agricultural.multiply(is_NOT_covered)
    .rename('Ag_BUT_NOT_Observed'); 


// --- 4. Visualization and Map Display ---

// Set the map center to a good view of the US
Map.setCenter(-100, 40, 4); 

// --- 4.1. Debug Layers (for troubleshooting) ---
// Add intermediate layers to inspect each step (set to false to hide by default)
// Note: Agricultural raster is binary (0 or 1), Observation raster is binary (0 or 1)
Map.addLayer(reprojected1, {min: 0, max: 1, palette: ['white', 'green']}, '1. Agricultural Raster (Debug)', false);
Map.addLayer(reprojected2, {min: 0, max: 1, palette: ['white', 'blue']}, '2. Observation Raster (Debug)', false);
Map.addLayer(is_agricultural, {min: 0, max: 1, palette: ['black', 'green']}, '3. Is Agricultural (Debug)', false);
Map.addLayer(is_NOT_covered, {min: 0, max: 1, palette: ['black', 'yellow']}, '4. Is NOT Covered (Debug)', false);

// --- 4.2. Final Visualization ---
// Visualization Parameters: Highlight the gap areas in a distinct color (e.g., Red)
var gapVis = {
  min: 0, 
  max: 1, 
  palette: ['black', 'red'] // Pixels in red are the target gap areas
};

// FIXED: Removed redundant updateMask - show gap_mask directly
// Only show pixels where gap_mask > 0 (i.e., actual gap areas)
Map.addLayer(gap_mask.updateMask(gap_mask.gt(0)), gapVis, 'Agricultural BUT NOT Observed (GAP)');

// Optional: Add the original observation layer to provide context
Map.addLayer(reprojected2, {min: 0, max: 1, palette: ['white', 'blue']}, 'Observation Coverage (Context)', false);


// --- 5. Export (Optional) ---
/* Export the final gap mask as a compressed, tiled GeoTIFF. */
Export.image.toDrive({
  image: gap_mask,
  description: 'Ag_Gap_Mask_1km',
  folder: 'GEE_Exports',
  fileNamePrefix: 'Ag_Gap_Mask',
  scale: targetResolution, // Now correctly in meters (1000m = 1km)
  region: reprojected1.geometry().bounds(), 
  crs: targetCRS, // Explicitly set CRS for export
  fileFormat: 'GeoTIFF',
  formatOptions: {
    cloudOptimized: true 
  }
});