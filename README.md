# 2025-autumn-bfi

## Project Background

The Becker Friedman Institute for Economics (BFI) serves as a hub for cutting-edge analysis and research across the entire University of Chicago economics community, uniting researchers from the Booth School of Business, the Kenneth C. Griffin Department of Economics, the Harris School of Public Policy, and the Law School in an unparalleled effort to uncover new ways of thinking about economics. Inspired by Nobel Laureates Gary Becker and Milton Friedman, BFI works with the Chicago Economics community to turn evidence-based research into real-world impact by translating rigorous research into accessible and relevant formats and proactively disseminating it to key decision-makers around the world.

This project extends the recent BFI working paper ["The Rise of Healthcare Jobs"](https://bfi.uchicago.edu/wp-content/uploads/2025/03/BFI_WP_2025-42.pdf) by developing an interactive Streamlit dashboard that enables users to explore healthcare employment across 130 Metropolitan Statistical Areas from 1980–2022. Using a [dataset](data/the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv) covering roughly 75% of the U.S. population with 26 socioeconomic variables—including healthcare and manufacturing employment shares, education levels, earnings, demographics, and Medicare eligibility—the tool allows users to examine regional healthcare job growth in relation to manufacturing decline and other economic indicators. Built as a web-based interactive visualization platform, the dashboard will provide journalists, researchers, and policymakers with the ability to filter by region, compare metropolitan trends, and analyze correlations between healthcare employment and broader socioeconomic shifts, making complex labor market dynamics more accessible for research and policy analysis.

### Key Features
- **Interactive visualizations** of healthcare employment trends across 130 MSAs
- **Two data timeframes** (1980–2022) covering roughly 75% of the U.S. population
- **26 socioeconomic variables** including employment shares, education, earnings, demographics, and Medicare eligibility
- **Guided Tour mode** for first-time users
- **Free Roam mode** for exploratory analysis
- **Docker-based deployment** for consistent environments across machines

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [Git](https://git-scm.com/)
- Windows PowerShell, macOS, or Linux terminal
- *(Optional)* [Make](https://www.gnu.org/software/make/) for simplified commands

### Quick Start

#### 1. Clone the Repository
```bash
git clone https://github.com/dsi-clinic/2025-autumn-bfi.git

# Set working directory to this repo
cd 2025-autumn-bfi
```

### 2. Set Up Environment
```bash
# This project uses uv for Python package management inside Docker Container.
uv venv
uv sync

#Install additional packages (if needed)
uv pip install package_name

# Copy the example environment file
cp .env.example .env

# If there are issues, edit .env to set your data directory path
# Example: DATA_DIR=/Users/yourname/project/data
```

### 3. Pre-commit Setup (first time only)
```bash
# Inside container:
cd src
pre-commit install
exit
```

### 4. Start Dashboard
```bash
make run-interactive

# To run Python commands, always prefix with `uv run` inside the container:
# For example: To run the dashboard
uv run streamlit run Homepage.py
```

If successful, the dashboard will be accessible at **http://localhost:8501**.

---
## Project Structure

```
2025-autumn-bfi/
├── data/
│   ├── the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv.    # Original BFI dataset
│   ├── merged_bfi.csv                      # Merged supplementary and BFI dataset*
|   ├── raw_data/                        # Raw supplementary data*
|   │   ├── cbsatocountycrosswalk.csv       # CBSA to county crosswalk*
|   │   ├── labor_1980.csv                  # 1980 labor data*
|   │   ├── labor_2022.csv                  # 2022 labor data*
|   │   ├── pop_1980.csv                    # 1980 population data*
|   │   └── pop_2022.csv                    # 2022 population data*
├── docs/                                # Documentation
│   └── DataDictionary.pdf                  # Variable definitions for original BFI data
│   └── Codebook.xlsx                       # Variable definitions for merged_bfi.csv
├── gt_utilities/                        # Healthcare jobs analysis utilities
│   ├── build_census_bea_resources.py       # Build population and labor data tables
│   ├── census_bea_pipeline.py              # Produces merged_bfi.csv and MSA tables
|   ├── charts.py                           # Visualization functions
│   ├── clean_census_bea_data.py            # Cleans raw supplementary data
|   ├── config.py                           # Configuration file for MSA dashboard
│   ├── data_prep_utils.py                  # Functions for ZIP-based shapefile processing
│   ├── demographics.py                     # Demographics comparison for MSA dashboard
│   ├── get_census_bea_data.py              # Obtains raw supplementary data
│   ├── loaders.py                          # Data loading utilities for MSA dashboard
│   ├── map_visualization_helper.py         # Help visualize MSA data on MapLibre
│   ├── merge_census_bea_data.py            # Merges cleaned supplementary data with BFI
├── notebooks/                           # Jupyter notebooks for exploration
│   ├── Test.ipynb                          # Example demonstrating using file structure
│   └── codetesting.ipynb
├── pages/                              # Dashboard page configurations
│   ├── 1_Guided_Tour.py                    # Guided exploration mode
│   └── 2_Freeroam.py                       # Free exploration mode
├── .dockerignore                       # File types ignored by Docker
├── .env.example                        # Example of .env for user to copy
├── .gitattributes                      # Line ending normalization
├── .gitignore                          # File types ignord by git
├── .pre-commit-config.yaml             # Defines automated checks before committing code
├── DataPolicy.md                       # Data privacy and security information
├── Dockerfile                          # Docker configuration
├── Homepage.py                         # Main Streamlit entry point
├── LICENSE                             # Code license
├── Makefile                            # Build automation
├── README.md                           # This file
├── dataprep.py                         # Data preprocessing script
├── docker-compose.yaml                 # Container orchestration
├── pyproject.toml                      # Python dependencies (uv)
└── test_chart.html                     # Test chart
```
#### * Created once code is run
---

## Data

### Dataset Overview
- **File**: `data/the_rise_of_healthcare_jobs_disclosed_data_by_msa.csv`
- **Coverage**: 130 Metropolitan Statistical Areas (MSAs)
- **Time Period**: 1980–2022 (43 years)
- **Population Coverage**: ~75% of U.S. population
- **Variables**: 26 socioeconomic indicators

### Key Variables
- Healthcare employment share
- Manufacturing employment share
- Population
- Education levels
- Median earnings
- Age and race demographics
- Medicare eligibility rates

### Data Dictionary
See [insertcodebook] for complete variable definitions and descriptions.

### Data Access & Privacy
All data handling follows the [Data Science Clinic guidelines](DataPolicy.md). Confidential data should only be used within the project context and stored securely on encrypted drives.

```

Builds an image with:
- Python 3.12 base
- System dependencies (GDAL, spatial indexing libraries)
- Python packages (via uv)
- Data preprocessing (runs `dataprep.py` automatically)

### Container Ports
- **8501**: Streamlit dashboard
- **8888**: Jupyter Lab (when running with `make run-notebooks`)

### Volume Mounts
- Source code: Container `/project/` → Host repo root
- Data directory: Container `/project/data/` → Host `$DATA_DIR`
- Virtual environment: Created and maintained in container `/project/.venv/`

---

## Troubleshooting

### Port Already in Use
```bash
# Find and stop the container using port 8501
docker ps
docker stop <container_id>
```

### Docker Build Fails
```bash
# Clean up and rebuild
docker compose down --volumes
docker compose build --no-cache
```

### Data Directory Not Found
- Verify `.env` file exists and `DATA_DIR` is set correctly
- Ensure the directory exists on your machine
- Example: `DATA_DIR=/Users/yourname/2025-autumn-bfi/data`

### Streamlit Not Starting
```bash
# Check container logs
docker compose logs -f
```

---

## References

### Key Documents
- **BFI Working Paper**: [The Rise of Healthcare Jobs](https://bfi.uchicago.edu/working-papers/the-rise-of-healthcare-jobs/)
- **Codebook**: `docs/Codebook.xlsx`


### External Resources
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Guide](https://docker-curriculum.com/)
- [uv Package Manager](https://docs.astral.sh/uv/)

### Supplementary Data Sources
- [U.S. Census Bureau](https://www2.census.gov/programs-surveys/popest/)
- [U.S. Bureau of Labor Statistics](https://www.bls.gov/cew/downloadable-data-files.htm)
- [National Bureau of Economic Research](https://www.nber.org/research/data/census-core-based-statistical-area-cbsa-federal-information-processing-series-fips-county-crosswalk)

### Optional: Fetching New BEA GDP/Earnings Data via API

The project includes helper utilities that can automatically pull updated GDP and industry-level data from the Bureau of Economic Analysis (BEA).  
If you plan to regenerate or extend the dataset, you may create a free BEA API key and store it in your `.env` file:

1. Request a key here: https://apps.bea.gov/api/signup/  
2. Add it to `.env`:

## Project Team

**Data Science Clinic** - University of Chicago  
Collaboration with the **Becker Friedman Institute for Economics**

Students Contributors:
- Shumaila Abbasi (shumaila9467)
- Ryan Lee (Rjlee22)
- Nandi Xu (TGPD5)
- Cynthia Zeng (cyn-zeng)

TA:
- Jack Luo (Jack-Luo-6)

Mentor:
- Jonatas A Marques (jonadmark)

External BFI Mentors:
- Eric Hernandez
- Abigail Hiller

---

**Last Updated**: December 2025