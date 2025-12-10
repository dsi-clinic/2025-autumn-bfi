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

- [Docker](https://www.docker.com/)
- [Git](https://git-scm.com/)
- Windows PowerShell, macOS, or Linux terminal
- [Make](https://www.gnu.org/software/make/) for launching application

### Quick Start

#### 1. Start Docker
Before doing anything else, download and open Docker Desktop on your computer.

Mac/Windows: Click the Docker "Whale" icon in your applications folder.

Verification: Wait until the icon stops animating or says "Engine Running" (usually a green light) in the Docker Desktop window.

*Tip: You can use the Docker app to manage Docker images and containers, as well as delete them*

#### 2. Clone the Repository
Open your Terminal (Mac) or Command Prompt/PowerShell (Windows) and run:
```bash
git clone https://github.com/dsi-clinic/2025-autumn-bfi.git

# Set working directory to this repo
cd 2025-autumn-bfi
```

### 3. Configuration
```bash
# Copy the example file
cp .env.example .env

# If there are issues, edit .env to set your data directory path
# Example: DATA_DIR=/Users/yourname/project/data
```

### 4. Run Docker and Start Dashboard
Type the following command to download the dependencies, build the Docker container, and start the app. *Note: This may take 5–10 minutes the first time you run it as it downloads and processes large files.*

The Docker container must be first built before the app can be run. To build the container AND run the app, run:
```bash
make build-run
```

Once the container is built, there is no need to build it again. To run the app after the container has been built, run:
```bash
make run-only
```
for faster load times.

Alternatively, to build the container only, run:
```bash
make build-only
```
Afterwards, running
```bash
make run-only
```
will activate the app.

If successful, the dashboard will be accessible at **http://localhost:8501** on your local browser.

### 5. Closing the App
When done with the application, you can close it by navigating back to your Terminal(Mac)/PowerShell(Windows) window and pressing `Ctrl + C`.

### 6. Cleaning up
If desired, empty containers or images can be purged to save disk space.

#### Quick Clean
Removes running containers and networks.
Use this if the app is stuck or you want to stop the background process.
Does NOT delete the large Docker image.
```bash
make quick-clean
```

To restart the app, run:
```bash
make run-only
```

#### Deep Clean (Frees Disk Space)
Removes containers AND the heavy Docker images.
Use this to free up disk space when you are done with the app.
```bash
make deep-clean
```

The container now must be rebuilt before the app can be run:
```bash
make build-run
```
or
```bash
make build-only
```

---
## Project Structure

```
2025-autumn-bfi/
.
├── data/                                   # Main data storage
│   ├── raw_data/                           # Stores raw supplementary data from source *
|   │   ├── cbsatocountycrosswalk.csv       # MSA to county crosswalk *
|   │   ├── labor_1980.csv                  # 1980 labor/employment data *
|   │   ├── labor_2022.csv                  # 2022 labor/employment data *
|   │   ├── pop_1980.csv                    # 1980 demographic data *
|   │   └── pop_2022.csv                    # 2022 demographic data *
│   ├── combined_US_regions_auto.geojson    # Processed map geometry (States + MSAs) *
│   ├── merged_bfi.csv                      # Final merged dataset for analysis *
│   ├── merged_healthcare_jobs_with_gdp.csv # Intermediate dataset linking Jobs to GDP *
│   ├── msa_gdp_percent_change.csv          # Calculated GDP growth metrics *
│   └── the_rise_of_healthcare_jobs...csv   # Original BFI working paper dataset
├── docs/                                   # Project documentation
│   ├── Codebook.xlsx                       # Variable definitions for merged_bfi.csv
│   └── DataDictionary.pdf                  # Variable definitions for original BFI data
├── gt_utilities/                           # Custom Python package for app logic
│   ├── __init__.py                         # Package initialization and logging setup
│   ├── build_census_bea_resources.py       # (Builder) Logic to aggregate final analytical tables
│   ├── census_bea_pipeline.py              # (Orchestrator) Main pipeline controller script
│   ├── charts.py                           # Altair chart generation functions
│   ├── clean_census_bea_data.py            # (Cleaner) Logic to clean raw Census/BLS data
│   ├── config.py                           # Global file paths, URLs, and constants
│   ├── dataprep_utils.py                   # Helpers for Shapefiles and GDP API interaction
│   ├── demographics.py                     # Logic for demographic comparison tables
│   ├── get_census_bea_data.py              # (Getter) Functions to download raw data
│   ├── loaders.py                          # Data loading/caching for Streamlit
│   ├── map_visualization_helper.py         # Plotly map and scatterplot generation
│   └── merge_census_bea_data.py            # (Merger) Logic to join datasets together
├── pages/                                  # Streamlit Multipage App Sub-pages
│   ├── 1_Guided_Tour.py                    # The narrative/storytelling dashboard page
│   └── 2_Freeroam.py                       # The interactive explorer dashboard page
├── dataprep.py                             # Entry point script to run the full data pipeline
├── docker-compose.yaml                     # Defines services, volumes, and ports for Docker
├── Dockerfile                              # Instructions to build the Python environment
├── Homepage.py                             # Main Entry Point for the Streamlit App
├── LICENSE                                 # MIT License file
├── Makefile                                # Shortcuts for building/running (e.g., `make build-run`)
├── pyproject.toml                          # Python project configuration and dependencies
└── README.md                               # This file
```
#### * Created when container is built
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
See [Codebook](/docs/Codebook.xlsx) for complete variable definitions and descriptions.

### Data Access & Privacy
All data handling follows the Data Science Clinic guidelines. Confidential data should only be used within the project context and stored securely on encrypted drives.

```

Builds an image with:
- Python 3.12 base
- System dependencies (GDAL, spatial indexing libraries)
- Python packages (via uv)
- Data preprocessing (runs `dataprep.py` automatically)

### Container Ports
- **8501**: Streamlit dashboard

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

Student Contributors:
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

**Last Updated**: December 10, 2025