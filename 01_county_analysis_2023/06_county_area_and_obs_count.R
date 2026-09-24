# Provenance: copied from `Raw Data/Bridging Gaps Dataset/create_county_area_obs_standalone.R` (last modified 2025-09-17) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Output: county_area_obs_data.csv (AREA_KM2, total observation count, observation density).
# Create County Dataset with Area and Observation Count
# Standalone script that imports data from neighboring files
# Run this script from the "Bridging Gaps Dataset" directory

# Load required libraries
library(terra)
library(sf)
library(dplyr)
library(exactextractr)
library(arrow)

cat("=== Creating County Dataset with Area and Observation Count ===\n\n")

# Load counties data
cat("Loading counties data...\n")
counties_sf <- st_read("../US_Counties/US_Counties_SocioEconomics.gpkg",
                       layer = "US_Counties_Data") %>%
  st_transform(5070)

# Load observation raster
cat("Loading observation raster...\n")
obs_raster <- rast("../NLCD2023/obs_raster.tif")

# Ensure counties are in the same CRS as the raster
counties_sf <- st_transform(counties_sf, crs(obs_raster))

cat("Data loaded successfully.\n\n")

# Calculate county areas
cat("Calculating county areas...\n")
counties_sf$area_m2 <- st_area(counties_sf)
counties_sf$area_km2 <- as.numeric(counties_sf$area_m2) / 1e6  # Convert to km²
counties_sf$area_ha <- as.numeric(counties_sf$area_m2) / 1e4   # Convert to hectares

# Calculate total observation count per county
cat("Calculating observation counts per county...\n")
obs_count <- exact_extract(obs_raster, counties_sf, 'sum', progress = TRUE)
counties_sf$total_obs_count <- obs_count

# Calculate observation density (observations per km²)
counties_sf$obs_density_km2 <- counties_sf$total_obs_count / counties_sf$area_km2

# Display summary statistics
cat("\n=== Summary Statistics ===\n")
cat("Number of counties:", nrow(counties_sf), "\n")
cat("Total area (km²):", sum(counties_sf$area_km2, na.rm = TRUE), "\n")
cat("Total observations:", sum(counties_sf$total_obs_count, na.rm = TRUE), "\n")
cat("Mean county area (km²):", mean(counties_sf$area_km2, na.rm = TRUE), "\n")
cat("Mean observations per county:", mean(counties_sf$total_obs_count, na.rm = TRUE), "\n")
cat("Mean observation density (obs/km²):", mean(counties_sf$obs_density_km2, na.rm = TRUE), "\n")

# Create a simplified dataset with area and observation metrics
cat("\nCreating simplified dataset...\n")
county_area_obs_data <- counties_sf %>%
  select(
    FIPS,
    STATE,
    COUNTYNAME,
    area_km2,
    area_ha,
    total_obs_count,
    obs_density_km2,
    geometry
  )

# Display first few rows
cat("\n=== First 10 counties with area and observation data ===\n")
print(head(st_drop_geometry(county_area_obs_data), 10))

# Save the new county dataset with area and observation count
cat("\n=== Saving datasets ===\n")

# Save as CSV (non-spatial)
county_area_obs_csv <- st_drop_geometry(county_area_obs_data)
write.csv(county_area_obs_csv, "county_area_obs_data.csv", row.names = FALSE)
cat("✅ Saved county_area_obs_data.csv\n")

# Save as GeoJSON (spatial)
st_write(county_area_obs_data, "county_area_obs_data.geojson", delete_dsn = TRUE)
cat("✅ Saved county_area_obs_data.geojson\n")

# Save as Parquet for efficient storage
write_parquet(county_area_obs_csv, "county_area_obs_data.parquet")
cat("✅ Saved county_area_obs_data.parquet\n")

cat("\n🎉 County dataset with area and observation count created successfully!\n")
cat("Files created:\n")
cat("- county_area_obs_data.csv (CSV format)\n")
cat("- county_area_obs_data.geojson (GeoJSON format)\n")
cat("- county_area_obs_data.parquet (Parquet format)\n")

cat("\n=== Dataset Structure ===\n")
cat("Columns in the dataset:\n")
cat("- FIPS: County FIPS code\n")
cat("- STATE: State abbreviation\n")
cat("- COUNTYNAME: County name\n")
cat("- area_km2: County area in square kilometers\n")
cat("- area_ha: County area in hectares\n")
cat("- total_obs_count: Total number of GBIF observations in the county\n")
cat("- obs_density_km2: Observation density (observations per km²)\n")
cat("- geometry: Spatial geometry (in GeoJSON format only)\n")
