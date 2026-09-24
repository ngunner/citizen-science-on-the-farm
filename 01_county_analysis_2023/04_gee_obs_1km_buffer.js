// Provenance: copied from `Raw Data/Bridging Gaps Dataset/Bridging Gaps.Rmd` (last modified 2025-09-17) into the
// Citizen Science on the Farm replication package, September 2026.
// Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
// Extracted verbatim from the '# Google Earth Engine Code' section of the notebook (run in code.earthengine.google.com).
// Input asset: obs_raster.tif (30 m observation-count raster from step 03) uploaded as an Earth Engine asset.
// Output: obs_1km_raster tiles (1 = within 1 km of >=1 observation), exported to Drive, merged back in step 03.
// Load your uploaded GBIF observation raster
var obs_raster = ee.Image("projects/nicholas-gunner/assets/obs_raster");

// Create binary presence/absence
var obs_binary = obs_raster.gt(0);

// Distance to nearest observation
var distance = obs_binary.fastDistanceTransform(30).sqrt().multiply(30);

// Create binary 1km proximity raster
var obs_1km = distance.lte(1000).selfMask();

// Load NLCD 2021 (same grid as your ag_raster / NLCD 2023)
var nlcd = ee.Image("USGS/NLCD_RELEASES/2021_REL/NLCD/2021").select('landcover');

var projection = nlcd.projection();

// --- Manually set CRS because .crs() fails ---
var crs = 'EPSG:5070';

// Extract transform (this still works fine)
var transform = projection.getInfo().transform;

// Get region
var region = nlcd.geometry();

// Export snapped to NLCD grid
Export.image.toDrive({
  image: obs_1km,
  description: 'obs_1km_raster',
  folder: 'EarthEngineExports',
  scale: 30,
  crs: crs,
  crsTransform: transform,
  region: region,
  maxPixels: 1e13
