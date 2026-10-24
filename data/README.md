# Data

The raw data is **not** stored in this repository. It is public and can be downloaded from
Mexico City's Environment Department (SEDEMA, *Secretaría del Medio Ambiente*) through the
Atmospheric Monitoring System (SIMAT) portal: <http://www.aire.cdmx.gob.mx>, section
*Bases de datos* → hourly concentrations (*concentraciones horarias*), one Excel file per
pollutant and year.

## Expected files

Save the files in `data/raw/` with SEDEMA's original naming, `{YEAR}{POLLUTANT}.xls`:

| Pollutant | Unit | Files |
|---|---|---|
| CO (carbon monoxide) | ppm | `2020CO.xls` … `2025CO.xls` |
| NO (nitric oxide) | ppb | `2020NO.xls` … `2025NO.xls` |
| NO2 (nitrogen dioxide) | ppb | `2020NO2.xls` … |
| NOX (nitrogen oxides) | ppb | `2020NOX.xls` … |
| O3 (ozone) | ppb | `2020O3.xls` … |
| PM10 (particles < 10 µm) | µg/m³ | `2020PM10.xls` … |
| PM25 (particles < 2.5 µm) | µg/m³ | `2020PM25.xls` … |
| PMCO (coarse particles) | µg/m³ | `2020PMCO.xls` … |
| SO2 (sulfur dioxide) | ppb | `2020SO2.xls` … |

Notebook `01` only needs the 2025 files; notebook `02` needs 2020 to 2025 (54 files, about 110 MB).

## Format

Each file has one row per hour and one column per monitoring station:

| FECHA | HORA | ACO | AJM | … |
|---|---|---|---|---|
| 2025-01-01 | 1 | -99 | 46 | … |

* `HORA` runs from 1 to 24 (hour ending), so hour 24 is midnight of the following day.
* `-99` marks a missing reading.

`cdmx_air.data.load_years()` reads these files, reshapes them to one row per station-hour and
converts the missing-value codes to `NaN`.
