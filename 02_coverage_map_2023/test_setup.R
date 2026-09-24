#!/usr/bin/env Rscript
# Provenance: copied from `Final Dataset/Coverage Maps/test_setup.R` (last modified 2025-11-14) into the
# Citizen Science on the Farm replication package, September 2026.
# Edits at packaging: hard-coded machine paths/credentials removed; logic unchanged.
# Quick test script to verify R setup and terra package installation
# This does NOT process the full rasters - just checks that everything is ready

cat("========================================\n")
cat("R Environment Setup Test\n")
cat("========================================\n\n")

# Check R version
cat("R Version:", R.version.string, "\n")

# Check if terra is available
cat("\nChecking for terra package...\n")
if (require("terra", quietly = TRUE)) {
  cat("✓ terra package is installed\n")
  cat("  Version:", as.character(packageVersion("terra")), "\n")
} else {
  cat("✗ terra package is NOT installed\n")
  cat("  Installing now...\n")
  install.packages("terra", repos = "https://cloud.r-project.org/")
  library(terra)
  cat("✓ terra package installed successfully\n")
}

# Check parallel capabilities
cat("\nSystem Information:\n")
cat("  Available CPU cores:", parallel::detectCores(), "\n")
cat("  Operating system:", Sys.info()["sysname"], "\n")
cat("  Machine:", Sys.info()["machine"], "\n")

# Check if input files exist
cat("\nChecking for input files...\n")
ag_file <- 'ag_raster.tif'
obs_file <- 'obs_1km_raster_merged.tif'

if (file.exists(ag_file)) {
  cat("✓ Found:", ag_file, "\n")
  cat("  Size:", format(file.info(ag_file)$size / 1024^3, digits = 2), "GB\n")
} else {
  cat("✗ Missing:", ag_file, "\n")
}

if (file.exists(obs_file)) {
  cat("✓ Found:", obs_file, "\n")
  cat("  Size:", format(file.info(obs_file)$size / 1024^3, digits = 2), "GB\n")
} else {
  cat("✗ Missing:", obs_file, "\n")
}

# Try to read raster headers (fast, doesn't load data)
if (file.exists(obs_file) && file.exists(ag_file)) {
  cat("\nTesting raster read (headers only, no data loaded)...\n")
  tryCatch({
    obs_test <- rast(obs_file)
    cat("✓ Observation raster:\n")
    cat("    Dimensions:", nrow(obs_test), "x", ncol(obs_test), "\n")
    cat("    Total pixels:", format(ncell(obs_test), big.mark = ","), "\n")
    cat("    CRS:", crs(obs_test, describe = TRUE)$name, "\n")
    
    ag_test <- rast(ag_file)
    cat("✓ Agriculture raster:\n")
    cat("    Dimensions:", nrow(ag_test), "x", ncol(ag_test), "\n")
    cat("    Total pixels:", format(ncell(ag_test), big.mark = ","), "\n")
    cat("    CRS:", crs(ag_test, describe = TRUE)$name, "\n")
    
    # Estimate processing time
    total_pixels <- ncell(obs_test)
    cat("\n========================================\n")
    cat("Estimated Processing Time:\n")
    cat("========================================\n")
    cat("Total pixels to process:", format(total_pixels, big.mark = ","), "\n")
    
    if (total_pixels > 1e9) {
      cat("Estimated time: 10-30 minutes (with optimization)\n")
      cat("Original Python would take: Several hours\n")
    } else if (total_pixels > 1e8) {
      cat("Estimated time: 5-15 minutes (with optimization)\n")
      cat("Original Python would take: 30-90 minutes\n")
    } else {
      cat("Estimated time: 1-5 minutes (with optimization)\n")
    }
    
  }, error = function(e) {
    cat("✗ Error reading rasters:", e$message, "\n")
  })
}

cat("\n========================================\n")
cat("Setup Status\n")
cat("========================================\n")

if (require("terra", quietly = TRUE) && file.exists(ag_file) && file.exists(obs_file)) {
  cat("✓ All checks passed!\n")
  cat("\nYou're ready to run the optimized script:\n")
  cat("  Rscript create_agricultural_gaps.R\n\n")
  cat("To compare with Python version:\n")
  cat("  time Rscript create_agricultural_gaps.R\n")
  cat("  time python3 create_agricultural_gaps.py\n")
} else {
  cat("✗ Setup incomplete. Please resolve issues above.\n")
}

cat("========================================\n")


