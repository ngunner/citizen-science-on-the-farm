# Agricultural Gaps Analysis - Processing Scripts

This directory contains multiple approaches for identifying agricultural land without observational coverage, optimized for different use cases.

## 📊 Your Data

- **Scale**: US-wide coverage at 30m resolution
- **Size**: ~130,000 × 80,000 pixels (10+ billion pixels)
- **Input files**:
  - `ag_raster.tif` - Agricultural land classification
  - `obs_1km_raster_merged.tif` - Observational coverage data
- **Output**: `agricultural_gaps.tif` - Areas where agriculture exists but observations don't

## 🚀 Quick Decision Guide

**Need results RIGHT NOW?**
→ Use `create_agricultural_gaps.R` (20 minutes)

**Want the fastest solution for repeated use?**
→ Use Google Earth Engine (2-5 minutes per run after setup)

**Just testing or learning?**
→ Use `create_agricultural_gaps.py` (original)

## 📁 Available Scripts

### 1. Original Python Script (Baseline)
- **File**: `create_agricultural_gaps.py`
- **Time**: 4-8 hours
- **Pros**: Simple, no setup
- **Cons**: Very slow, inefficient
- **Use when**: Testing small areas only

### 2. Optimized R Script (Fast Local Processing)
- **File**: `create_agricultural_gaps.R`
- **Time**: 10-30 minutes
- **Pros**: 10-50x faster than Python, uses all CPU cores
- **Cons**: Still blocks your machine
- **Use when**: Need results today, no GEE access

**Quick Start:**
```bash
Rscript create_agricultural_gaps.R
```

### 3. Google Earth Engine (Cloud Processing)
- **Files**: 
  - `agricultural_gaps_gee.js` (JavaScript - recommended)
  - `agricultural_gaps_gee.py` (Python API alternative)
- **Time**: 2-5 minutes (after one-time setup)
- **Pros**: Extremely fast, doesn't use your computer, scalable
- **Cons**: Requires setup and data upload first
- **Use when**: Large datasets, repeated analyses, production workflows

**Quick Start:**
See `QUICKSTART_GEE.md` for step-by-step instructions

## 📖 Documentation

- **QUICKSTART_GEE.md** - Fast-track guide for Google Earth Engine (START HERE for GEE)
- **GEE_SETUP_GUIDE.md** - Detailed GEE setup and troubleshooting
- **README_OPTIMIZATION.md** - Details on R optimization approach
- **PERFORMANCE_COMPARISON.md** - Comprehensive comparison of all methods

## ⚡ Performance Comparison

| Method | Processing Time | Your Machine | Best For |
|--------|----------------|--------------|----------|
| Python (original) | 4-8 hours | Blocked | Small tests |
| R (optimized) | 10-30 min | Blocked | Today's results |
| **Google Earth Engine** | **2-5 min** | **Free!** | **Your use case** |

## 🎯 Recommended Workflow for Your Situation

Given your large US-scale rasters:

### Option A: Get Results Today
```bash
# Install R if needed (from https://cran.r-project.org/)
# Then run:
Rscript create_agricultural_gaps.R

# Wait 10-30 minutes
# Output: agricultural_gaps.tif
```

### Option B: Best Long-Term Solution
```bash
# Day 1: Setup GEE (2-3 hours mostly unattended)
# Follow QUICKSTART_GEE.md

# Day 2+: Run analysis (2-5 minutes each time!)
# Use agricultural_gaps_gee.js in Earth Engine Code Editor
```

### Option C: Do Both (Recommended!)
```bash
# Today: Get results with R while GEE uploads in background
Rscript create_agricultural_gaps.R &

# Setup GEE in parallel (see QUICKSTART_GEE.md)
# Tomorrow: Use GEE for all future runs
```

## 🔧 Requirements

### Python Script
```bash
pip install rasterio numpy
```

### R Script
```r
# Script auto-installs terra package if needed
# Just have R installed
```

### Google Earth Engine
- Google account
- GEE access (free for academic use)
- See GEE_SETUP_GUIDE.md

## 📤 Output

All methods produce identical outputs:
- **Format**: GeoTIFF with LZW compression
- **Values**: 
  - `1` = Agricultural land without observational coverage (the gaps)
  - `0` = Other areas
  - `NaN` = No data
- **CRS**: Matches observation raster
- **Resolution**: 30m × 30m

## 🐛 Troubleshooting

### Python is too slow
→ Use R or GEE instead

### R script fails to install terra
```bash
# macOS: Install GDAL first
brew install gdal

# Then try R script again
```

### GEE upload failed
→ See troubleshooting in GEE_SETUP_GUIDE.md

### Out of memory errors
→ Use GEE (processes in cloud, no local memory limits)

## 📊 Statistics

All scripts calculate and report:
- Total agricultural pixels
- Total uncovered pixels  
- Agricultural gap pixels
- Percentage of agricultural land without coverage

## 🎓 Citation / Reproducibility

For reproducible research, we recommend:
1. **Document which method you used** in your paper
2. **Use GEE for reproducibility** - scripts can be easily shared via Earth Engine
3. **Include processing parameters** - all provided in script headers

## 📝 File Summary

```
Coverage Maps/
├── create_agricultural_gaps.py        # Original Python (slow)
├── create_agricultural_gaps.R         # Optimized R (fast local)
├── agricultural_gaps_gee.js          # GEE JavaScript (fastest)
├── agricultural_gaps_gee.py          # GEE Python API (alternative)
├── test_setup.R                      # Test R environment
│
├── README.md                         # This file - overview
├── QUICKSTART_GEE.md                # ⭐ Start here for GEE
├── GEE_SETUP_GUIDE.md               # Detailed GEE guide
├── README_OPTIMIZATION.md            # R optimization details
└── PERFORMANCE_COMPARISON.md         # Detailed comparison
```

## 💡 Tips for PhD Research

1. **Time Management**: Use GEE to free up your machine for other tasks
2. **Reproducibility**: GEE scripts are easier to share with collaborators
3. **Iterations**: If you need to test different parameters, GEE will save you days
4. **Publication**: Document processing time in methods - reviewers appreciate efficiency

## 🆘 Need Help?

1. **R issues**: Check README_OPTIMIZATION.md
2. **GEE issues**: Check GEE_SETUP_GUIDE.md and QUICKSTART_GEE.md
3. **Performance questions**: See PERFORMANCE_COMPARISON.md
4. **General GIS questions**: The scripts include detailed comments

## 🎉 Success Criteria

You'll know it worked when:
- ✓ Output file `agricultural_gaps.tif` is created
- ✓ File size is similar to input files
- ✓ Statistics show reasonable gap percentages
- ✓ Visual inspection shows gaps in expected locations

Good luck with your research! 🌾📊


