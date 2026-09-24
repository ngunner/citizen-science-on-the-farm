#!/usr/bin/env Rscript
# Provenance: copied from `Final Dataset/Coverage Maps/create_agricultural_gaps.R` (last modified 2025-11-14) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Create a raster showing agricultural land without observational coverage
# Optimized version using terra package with automatic multithreading

# Check if terra is installed
if (!require("terra", quietly = TRUE)) {
  cat("Installing terra package...\n")
  install.packages("terra", repos = "https://cloud.r-project.org/")
  library(terra)
}

library(terra)

# Enable all available cores for parallel processing
# terra automatically uses multiple cores for many operations
cat("Setting up parallel processing...\n")
cat("Available cores:", parallel::detectCores(), "\n")

# Input files
ag_file <- 'ag_raster.tif'
obs_file <- 'obs_1km_raster_merged.tif'
output_file <- 'agricultural_gaps.tif'

cat("\n========================================\n")
cat("Step 1: Reading rasters...\n")
cat("========================================\n")

# Read observation raster
cat("Loading observation raster...\n")
obs_rast <- rast(obs_file)
cat("  Dimensions:", nrow(obs_rast), "x", ncol(obs_rast), "\n")
cat("  CRS:", crs(obs_rast, describe = TRUE)$name, "\n")
cat("  Resolution:", res(obs_rast), "\n")
cat("  Extent:", as.vector(ext(obs_rast)), "\n")

# Read agriculture raster
cat("\nLoading agriculture raster...\n")
ag_rast <- rast(ag_file)
cat("  Dimensions:", nrow(ag_rast), "x", ncol(ag_rast), "\n")
cat("  CRS:", crs(ag_rast, describe = TRUE)$name, "\n")

cat("\n========================================\n")
cat("Step 2: Reprojecting agriculture raster...\n")
cat("========================================\n")
cat("This is the key optimization - doing this ONCE instead of hundreds of times!\n")
cat("Using all available CPU cores for reprojection...\n\n")

# Start timing
start_time <- Sys.time()

# Reproject agriculture raster to match observation raster
# This uses multithreading automatically and processes in memory-efficient chunks
ag_reprojected <- project(
  ag_rast,
  obs_rast,
  method = "near",  # Nearest neighbor for binary data
  threads = TRUE    # Enable multithreading
)

reproject_time <- Sys.time()
cat("Reprojection completed in", round(difftime(reproject_time, start_time, units = "secs"), 2), "seconds\n")

cat("\n========================================\n")
cat("Step 3: Identifying agricultural gaps...\n")
cat("========================================\n")
cat("Finding agricultural land without observational coverage...\n")

# Create masks using vectorized operations (very fast)
# Agricultural land = 1
agricultural_mask <- ag_reprojected == 1

# Not covered = 0 or NA
not_covered_mask <- (obs_rast == 0) | is.na(obs_rast)

# Gaps = agricultural AND not covered
gaps_rast <- agricultural_mask & not_covered_mask

# Convert to numeric (1 for gaps, 0 otherwise)
gaps_rast <- as.numeric(gaps_rast)

# Set areas where both are NA to NA in output
both_na_mask <- is.na(ag_reprojected) & is.na(obs_rast)
gaps_rast[both_na_mask] <- NA

analysis_time <- Sys.time()
cat("Gap analysis completed in", round(difftime(analysis_time, reproject_time, units = "secs"), 2), "seconds\n")

cat("\n========================================\n")
cat("Step 4: Calculating statistics...\n")
cat("========================================\n")

# Calculate statistics
agricultural_count <- sum(values(agricultural_mask), na.rm = TRUE)
not_covered_count <- sum(values(not_covered_mask), na.rm = TRUE)
gaps_count <- sum(values(gaps_rast == 1), na.rm = TRUE)

cat("\nResults:\n")
cat("  Agricultural pixels:", format(agricultural_count, big.mark = ","), "\n")
cat("  Not covered pixels:", format(not_covered_count, big.mark = ","), "\n")
cat("  Agricultural gaps (ag=1, obs=0/NA):", format(gaps_count, big.mark = ","), "\n")

if (agricultural_count > 0) {
  coverage_pct <- 100 * gaps_count / agricultural_count
  cat("  Percentage of agricultural land without coverage:", 
      round(coverage_pct, 2), "%\n")
}

cat("\n========================================\n")
cat("Step 5: Writing output...\n")
cat("========================================\n")

# Write output with LZW compression
writeRaster(
  gaps_rast,
  output_file,
  overwrite = TRUE,
  datatype = "FLT4S",  # 32-bit float
  gdal = c("COMPRESS=LZW", "PREDICTOR=2"),  # LZW compression with predictor
  NAflag = NaN
)

end_time <- Sys.time()

cat("\n========================================\n")
cat("Success!\n")
cat("========================================\n")
cat("Output saved to:", output_file, "\n")
cat("Output statistics:\n")
cat("  - Shape:", nrow(gaps_rast), "x", ncol(gaps_rast), "\n")
cat("  - Pixels with value 1 (agricultural gaps):", format(gaps_count, big.mark = ","), "\n")
cat("  - CRS:", crs(gaps_rast, describe = TRUE)$name, "\n")
cat("  - Resolution:", res(gaps_rast), "m\n")

cat("\n========================================\n")
cat("Performance Summary:\n")
cat("========================================\n")
cat("Total processing time:", round(difftime(end_time, start_time, units = "mins"), 2), "minutes\n")
cat("  - Reprojection:", round(difftime(reproject_time, start_time, units = "secs"), 2), "seconds\n")
cat("  - Gap analysis:", round(difftime(analysis_time, reproject_time, units = "secs"), 2), "seconds\n")
cat("  - Writing output:", round(difftime(end_time, analysis_time, units = "secs"), 2), "seconds\n")
cat("========================================\n")

# Clean up
rm(obs_rast, ag_rast, ag_reprojected, agricultural_mask, not_covered_mask, gaps_rast)
gc()

cat("\nDone!\n")


