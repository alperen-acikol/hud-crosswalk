# Methodology — ZIP to County Crosswalk

## The Problem

Survey data is frequently collected at the ZIP code level, while administrative 
and census data — such as NOAA storm event records or the FEMA National Risk Index — 
are organized at the county level. This makes it challenging to directly match survey 
responses to county level administrative records.

This mismatch is not simply a technical inconvenience. The U.S. Postal Service designed 
ZIP codes for mail delivery efficiency rather than to reflect social, economic, or 
political boundaries, meaning they do not necessarily correspond to meaningful geographic 
or administrative units (Wilson & Din, 2018). ZIP code boundaries frequently cross county 
lines, creating a structural misalignment between the unit in which survey data is 
collected and the unit in which administrative data is organized.

This misalignment carries real analytical consequences. Sadler (2019) found that in 
Michigan, 49% of the population was misclassified at the municipal level when ZIP codes 
were used as the geographic unit of analysis. The Flint water crisis provides a clear 
illustration: state officials initially used ZIP code boundaries to identify the area of 
lead exposure, but the affected water system actually aligned more closely with the 
municipal boundary than with any ZIP code boundary. Using ZIP codes in that case led to 
an underestimation of the geographic extent of the crisis (Sadler, 2019). Wilson & Din 
(2018) similarly highlight that aggregating data by ZIP codes can obscure or distort 
patterns at more detailed geographic levels.

---

## The Solution — HUD USPS Crosswalk File

To address this misalignment, this toolkit uses the crosswalk file provided by the 
U.S. Department of Housing and Urban Development (HUD). The HUD USPS Crosswalk file 
provides allocation ratios that specify the share of residential addresses in each 
county for ZIP codes that span multiple counties.

This approach is more accurate than centroid-based methods, which assign a ZIP code 
to whichever county its geographic center falls in. Centroid-based approaches risk 
misassigning entire populations if a ZIP code's center lies just across a county line 
(Wilson & Din, 2018). The HUD residential address ratio instead grounds the assignment 
in where people actually live.

For ZIP codes that cross multiple counties, HUD recommends assigning each ZIP code to 
the county with the majority of residential addresses. This toolkit implements that 
recommendation — each ZIP code is assigned to the county where the largest share of 
residential addresses are located, based on the allocation ratios in the HUD crosswalk 
file.

---

## Implementation

The toolkit handles the ZIP to county assignment in the following steps:

**1. Standardize ZIP and FIPS codes**
ZIP codes and FIPS codes contain leading zeros that are dropped when read as integers 
by pandas. All columns are converted to string and zero filled to 5 digits before 
any merging takes place to ensure correct matching.

**2. Build ZIP to county mapping**
A dictionary is built from the HUD crosswalk data mapping each ZIP code to a list 
of all counties it intersects with. This captures the full picture for ZIP codes 
that span multiple counties.

**3. Assign counties to survey data**
The mapping dictionary is used to assign county FIPS codes to each survey respondent 
based on their ZIP code. For ZIP codes that map to only one county, that county is 
assigned directly.

**4. Resolve multi-county ZIP codes**
For ZIP codes that span multiple counties, a nested dictionary is built mapping each 
ZIP code to its intersecting counties along with the corresponding residential address 
ratios. Each ZIP code is then assigned to the county with the highest residential 
address ratio — the county where the majority of residential addresses are located.

---

## Limitations

### Sampling Design
The residential address ratio approach works best with random samples, where respondents 
within a ZIP code are likely distributed across counties in proportion to their 
residential shares. In this case, assigning a ZIP code to the county with the most 
addresses reflects a reasonable probability that a randomly selected respondent lives 
in that county.

For quota or convenience samples, this assumption falls short. A respondent from a 
ZIP code that spans two counties could reside in either, and assigning them to the 
county with the most addresses may be inaccurate for any given individual. Researchers 
using non-random sampling designs should account for this potential misclassification 
when interpreting results.

### Temporal Coverage
The HUD crosswalk file is updated quarterly. ZIP code boundaries and residential 
address distributions change over time. Researchers should use the crosswalk file 
that corresponds to the time period of their data collection to minimize misclassification.

### Unmatched ZIP Codes
Some ZIP codes in survey data may not appear in the HUD crosswalk file. This is 
common for PO box ZIP codes, which are used for mail delivery only and do not 
correspond to residential addresses. Researchers should inspect and document any 
unmatched ZIP codes before dropping them from the analysis.

### Version Coverage
This toolkit currently covers ZIP to county crosswalk only (Type 2 in the HUD API). 
Other crosswalk types such as ZIP to Census Tract (Type 1) or ZIP to CBSA (Type 3) 
are not supported in this version.

---

## References

Sadler, R. C. (2019). Misalignment between ZIP codes and municipal boundaries: 
A problem for public health.

Wilson, R., & Din, A. (2018). Understanding and enhancing the U.S. Department of 
Housing and Urban Development's ZIP code crosswalk files.

HUD USPS Crosswalk API documentation:
https://www.huduser.gov/portal/dataset/uspszip-api.html
