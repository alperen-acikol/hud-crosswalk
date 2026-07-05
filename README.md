# HUD USPS ZIP Crosswalk Toolkit
### v0.1 — ZIP to County Crosswalk

A Python toolkit for social scientists and researchers working with geographic data.
Provides a simple interface for retrieving ZIP to county crosswalk data from the HUD 
USPS Crosswalk API, profiling and validating ZIP code data quality, and merging survey 
or administrative datasets by mapping ZIP codes to county FIPS codes.

> **Note:** This is v0.1 and currently covers ZIP to county crosswalk only (Type 2). 
> Support for other crosswalk types (ZIP to tract, ZIP to CBSA, etc.) is planned for 
> future versions.

---

## Why This Toolkit

Survey data is often collected at the ZIP code level while administrative and census 
data is organized at the county level. This mismatch is not just a technical nuisance — 
it has real analytical consequences. The U.S. Postal Service designed ZIP codes for 
mail delivery efficiency rather than to reflect administrative or political boundaries, 
meaning they frequently cross county lines (Wilson & Din, 2018). Sadler (2019) found 
that in Michigan, 49% of the population was misclassified at the municipal level when 
ZIP codes were used as the geographic unit of analysis.

This toolkit uses the HUD USPS Crosswalk file to bridge that gap. The HUD file provides 
residential address ratios that describe the share of addresses in each ZIP code that 
fall within each county. For ZIP codes that span multiple counties, each ZIP is assigned 
to the county where the majority of residential addresses are located — a more accurate 
approach than centroid-based methods, which risk misassigning entire populations if a 
ZIP code's center falls just across a county line (Wilson & Din, 2018).

For a detailed discussion of the methodology and its limitations see 
`notebooks/methodology.md`.

---

## Known Limitations

The residential address ratio approach works best with random samples, where respondents 
within a ZIP code are likely distributed across counties in proportion to their residential 
shares. For quota or convenience samples, some geographic misclassification may still 
occur since the actual location of a respondent within a multi-county ZIP code cannot 
be determined from the ZIP code alone. Researchers should account for this when 
interpreting results. See `notebooks/methodology.md` for a full discussion.

---

## Installation

Clone the repository and install the required packages:

```bash
git clone https://github.com/yourusername/hud-crosswalk.git
cd hud-crosswalk
pip install -r requirements.txt
```

---

## Requirements

- Python 3.10+
- pandas
- requests
- openpyxl
- tabulate

A HUD API token is required to retrieve data from the HUD USPS Crosswalk API.
Register for a free token at: https://www.huduser.gov/portal/dataset/uspszip-api.html

---

## Project Structure

```
hud_crosswalk/
│
├── src/
│   └── hud_crosswalk/
│       ├── __init__.py
│       ├── dataload.py           # DataLoad class — API calls and file loading
│       ├── dataprocessing.py     # DataProcessing class — ZIP code profiling and validation
│       └── datamerge.py          # DataMerge class — ZIP to county mapping
│
├── notebooks/
│   ├── demo.ipynb                # Usage walkthrough
│   └── methodology.md            # Detailed methodology and limitations
│
├── requirements.txt
└── README.md
```

---

## Classes

### DataLoad
Handles data retrieval from the HUD USPS Crosswalk API and local file loading.
Supports CSV and XLSX formats. The API token is passed explicitly to `api_call()` 
rather than stored as an instance attribute to avoid silent failures when working 
with multiple datasets.

**Key methods:**
- `huds_url_modifier()` — builds query parameters for the API request
- `api_call()` — makes the API request and returns a DataFrame
- `data_load()` — loads a local CSV or XLSX file by partial filename match

### DataProcessing
Profiles and validates ZIP code columns before merging. Identifies missing values,
non-numeric characters, and incorrect character length. Returns a summary of issues
and a filtered DataFrame of problematic rows for the researcher to inspect and resolve.

**Key methods:**
- `data_profile()` — profiles a ZIP code column and returns a summary of issues
- `data_filter()` — returns a DataFrame of rows that failed one or more checks

### DataMerge
Handles merging ZIP code data with county level data using the HUD crosswalk.
Resolves ZIP codes that span multiple counties using residential address ratios.
HUD column names default to standard API naming but can be overridden at initialization.

**Key methods:**
- `run()` — full pipeline in one call (recommended)
- `zip_to_location()` — builds ZIP to geoid mapping dictionary from HUD data
- `assign_geoid_main_dataframe()` — maps geoids onto the main dataframe
- `expand_geoid_columns()` — expands multi-county ZIP codes into separate columns
- `resolve_multi_county_zip()` — resolves multi-county ZIPs using residential ratios

---

## Usage

### 1. Retrieve Data from the HUD API

```python
from hud_crosswalk import DataLoad

dl = DataLoad()
params = dl.huds_url_modifier(2, query='All', year=2022, quarter=3)
huds_df = dl.api_call('your_api_token', params)
```

### 2. Profile and Validate ZIP Codes

Before merging, profile the ZIP code column in your survey data to check for 
data quality issues. If issues are found, the method returns both a summary 
dictionary and a DataFrame of problematic rows for the researcher to inspect.

```python
from hud_crosswalk import DataProcessing

dp = DataProcessing()
result = dp.data_profile(survey_df, 'zip')

# if issues found — unpack the tuple
if isinstance(result, tuple):
    profile, problems = result
    print(problems)  # inspect and resolve before merging
```

### 3. Merge ZIP Codes with County FIPS Codes

```python
from hud_crosswalk import DataMerge

dm = DataMerge()
merged = dm.run(survey_df, huds_df, df_zip='zip')
```

### Custom HUD Column Names
By default `DataMerge` assumes standard HUD column names (`zip`, `geoid`, `res_ratio`). 
If your HUD data has different column names, override them at initialization:

```python
dm = DataMerge(huds_zip='zipcode', huds_geoid='fips', huds_res_ratio='ratio')
```

---

## Recommended Workflow

```python
from hud_crosswalk import DataLoad, DataProcessing, DataMerge

# 1. load HUD crosswalk data from API
dl = DataLoad()
params = dl.huds_url_modifier(2, query='All', year=2022, quarter=3)
huds_df = dl.api_call('your_api_token', params)

# 2. profile ZIP codes in survey data
dp = DataProcessing()
result = dp.data_profile(survey_df, 'zip')

# 3. resolve any issues before merging
if isinstance(result, tuple):
    profile, problems = result
    print(problems)  # inspect and resolve

# 4. merge survey data with county FIPS codes
dm = DataMerge()
merged = dm.run(survey_df, huds_df, df_zip='zip')
```

---

## Notes

### API Parameters
The HUD API supports 12 crosswalk types. This toolkit currently supports Type 2 
(ZIP to County). The most common types for social science research are:
- Type 1 — ZIP to Census Tract
- Type 2 — ZIP to County ← supported in this version
- Type 7 — County to ZIP

For a full list of crosswalk types and query parameters see:
https://www.huduser.gov/portal/dataset/uspszip-api.html

### Leading Zeros
ZIP codes and FIPS codes contain leading zeros that are dropped when read as integers 
by pandas. This toolkit handles zero filling automatically — all ZIP and geoid columns 
are standardized to 5 digits before merging.

---

## References

Sadler, R. C. (2019). Misalignment between ZIP codes and municipal boundaries: 
A problem for public health.

Wilson, R., & Din, A. (2018). Understanding and enhancing the U.S. Department of 
Housing and Urban Development's ZIP code crosswalk files.

---

## License
MIT License
