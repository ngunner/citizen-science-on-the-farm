# Provenance: copied from `Raw Data/Bridging Gaps Dataset/calculate_landcover_percentages_optimized.R` (last modified 2025-09-17) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Output: counties_landcover_percentages_optimized.csv (percent developed / forest / water per county).
# Optimized script to calculate land cover percentages by county from NLCD 2023 data
# Author: AI Assistant
# Date: Generated for land cover analysis
# Approach: Memory-efficient processing with multi-threading

# Load required libraries
library(terra)
library(sf)
library(dplyr)
library(parallel)
library(doParallel)
library(foreach)

# Set working directory
# Load the NLCD 2023 raster
cat("Loading NLCD 2023 raster...\n")
nlcd <- rast("../NLCD2023/Annual_NLCD_LndCov_2023_CU_C1V0.tif")

# Load counties data
cat("Loading counties data...\n")
counties_sf <- st_read("../US_Counties/US_Counties_SocioEconomics.gpkg",
                       layer = "US_Counties_Data") %>%
  st_transform(crs(nlcd))

cat("Counties loaded:", nrow(counties_sf), "\n")

# Memory-efficient function to analyze land cover for a single county
analyze_county_landcover_optimized <- function(county_index, counties_sf, nlcd_path) {
  # Load the county and raster fresh in each worker
  county <- counties_sf[county_index, ]
  fips <- county$FIPS
  
  tryCatch({
    # Load raster fresh to avoid memory issues
    nlcd_raster <- rast(nlcd_path)
    
    # Crop the NLCD raster to the county extent
    county_nlcd <- crop(nlcd_raster, county)
    
    # Mask to the county boundary
    county_nlcd <- mask(county_nlcd, county)
    
    # Get all values in the county
    values <- values(county_nlcd)
    values <- values[!is.na(values)]
    
    # Clean up memory
    rm(county_nlcd)
    gc()
    
    if (length(values) == 0) {
      return(data.frame(
        FIPS = fips,
        PERCENT_DEVELOPED = NA,
        PERCENT_FOREST = NA,
        PERCENT_WATER = NA,
        TOTAL_PIXELS = 0
      ))
    }
    
    # Calculate percentages
    total_pixels <- length(values)
    
    # Developed land (codes 21-24)
    developed_pixels <- sum(values %in% c(21, 22, 23, 24))
    percent_developed <- developed_pixels / total_pixels
    
    # Forest land (codes 41-43)
    forest_pixels <- sum(values %in% c(41, 42, 43))
    percent_forest <- forest_pixels / total_pixels
    
    # Water (code 11)
    water_pixels <- sum(values == 11)
    percent_water <- water_pixels / total_pixels
    
    return(data.frame(
      FIPS = fips,
      PERCENT_DEVELOPED = percent_developed,
      PERCENT_FOREST = percent_forest,
      PERCENT_WATER = percent_water,
      TOTAL_PIXELS = total_pixels
    ))
    
  }, error = function(e) {
    cat("Error processing county", fips, ":", e$message, "\n")
    return(data.frame(
      FIPS = fips,
      PERCENT_DEVELOPED = NA,
      PERCENT_FOREST = NA,
      PERCENT_WATER = NA,
      TOTAL_PIXELS = 0
    ))
  })
}

# Set up parallel processing
cat("Setting up parallel processing...\n")
n_cores <- min(detectCores() - 1, 6)  # Conservative core usage
cat("Using", n_cores, "cores for parallel processing\n")

# Register parallel backend
cl <- makeCluster(n_cores)
registerDoParallel(cl)

# Export necessary objects to workers
clusterExport(cl, c("counties_sf"), envir = environment())

# Get number of counties
n_counties <- nrow(counties_sf)
cat("Processing", n_counties, "counties in parallel...\n")

# Process counties in parallel with progress tracking
cat("Starting parallel processing...\n")
start_time <- Sys.time()

# Process in smaller chunks for better memory management
chunk_size <- max(1, floor(n_counties / (n_cores * 2)))
chunks <- split(1:n_counties, ceiling(seq_along(1:n_counties) / chunk_size))

cat("Processing", length(chunks), "chunks of approximately", chunk_size, "counties each\n")

all_results <- list()
for (chunk_idx in 1:length(chunks)) {
  chunk_indices <- chunks[[chunk_idx]]
  cat("Processing chunk", chunk_idx, "of", length(chunks), 
      "(", length(chunk_indices), "counties)...\n")
  
  chunk_results <- foreach(i = chunk_indices, 
                         .combine = rbind,
                         .packages = c("terra", "sf"),
                         .errorhandling = "pass") %dopar% {
    analyze_county_landcover_optimized(i, counties_sf, "../NLCD2023/Annual_NLCD_LndCov_2023_CU_C1V0.tif")
  }
  
  all_results[[chunk_idx]] <- chunk_results
  
  # Force garbage collection between chunks
  gc()
}

# Combine all results
results <- do.call(rbind, all_results)

# Stop parallel cluster
stopCluster(cl)

end_time <- Sys.time()
processing_time <- end_time - start_time
cat("Parallel processing completed in", round(as.numeric(processing_time, units = "mins"), 2), "minutes\n")

# Check results
cat("Results summary:\n")
cat("Successfully processed:", sum(!is.na(results$PERCENT_DEVELOPED)), "counties\n")
cat("Failed to process:", sum(is.na(results$PERCENT_DEVELOPED)), "counties\n")

# Add the new columns to the counties data
counties_sf$PERCENT_DEVELOPED <- results$PERCENT_DEVELOPED
counties_sf$PERCENT_FOREST <- results$PERCENT_FOREST  
counties_sf$PERCENT_WATER <- results$PERCENT_WATER

# Display summary statistics
cat("\nLand Cover Summary Statistics:\n")
cat("Mean % developed:", round(mean(results$PERCENT_DEVELOPED, na.rm = TRUE) * 100, 2), "%\n")
cat("Mean % forest:", round(mean(results$PERCENT_FOREST, na.rm = TRUE) * 100, 2), "%\n")
cat("Mean % water:", round(mean(results$PERCENT_WATER, na.rm = TRUE) * 100, 2), "%\n")

# Show some examples
cat("\nFirst 10 counties with land cover percentages:\n")
example_data <- counties_sf %>%
  select(FIPS, STATE, COUNTYNAME, PERCENT_DEVELOPED, PERCENT_FOREST, PERCENT_WATER) %>%
  st_drop_geometry() %>%
  head(10)

print(example_data)

# Save the updated counties data
cat("\nSaving updated counties data...\n")
st_write(counties_sf, "counties_with_landcover_optimized.geojson", delete_dsn = TRUE)

# Also create a CSV version for easy merging
counties_csv <- counties_sf %>%
  select(FIPS, STATE, COUNTYNAME, PERCENT_DEVELOPED, PERCENT_FOREST, PERCENT_WATER) %>%
  st_drop_geometry()

write.csv(counties_csv, "counties_landcover_percentages_optimized.csv", row.names = FALSE)

cat("✅ Analysis complete!\n")
cat("Files created:\n")
cat("- counties_with_landcover_optimized.geojson (spatial data with land cover percentages)\n")
cat("- counties_landcover_percentages_optimized.csv (CSV for merging)\n")

# Display summary by state
cat("\nLand cover summary by state (top 10 by mean % developed):\n")
state_summary <- counties_sf %>%
  st_drop_geometry() %>%
  group_by(STATE) %>%
  summarise(
    mean_developed = mean(PERCENT_DEVELOPED, na.rm = TRUE) * 100,
    mean_forest = mean(PERCENT_FOREST, na.rm = TRUE) * 100,
    mean_water = mean(PERCENT_WATER, na.rm = TRUE) * 100,
    n_counties = n(),
    .groups = 'drop'
  ) %>%
  arrange(desc(mean_developed)) %>%
  head(10)

print(state_summary)
