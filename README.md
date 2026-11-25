# Layermap

A layered world colour map in plate carrée projection. Start from the whole world and **crack** it into continents, countries, regions and subdivisions, going as fine as US census tracts. You can **delete** pieces or **combine** them, then **colour** and label the result. The map can sit on top of satellite, elevation and settlement layers.

**Try it:** https://alejandrozu.github.io/layermap/ (GitHub Pages, built from `site/` on every push to `main`).

A second hosted version runs as a claude.ai artifact. It adds Save & share links and the sharpest satellite imagery.

Layermap still opens map files saved under its earlier name, Crackmap, and picks up maps and preferences saved in the browser by the old version. New exports and browser saves use the Layermap name.

## Features

- **Crack / delete / colour modes** for going down and back up the hierarchy (world → regions → countries → subdivisions → census tracts), with combined areas.
- **Data & legend panel** (P key or the top bar):
  - **Numbers on the map** show population, density or area, in metric (the default) or imperial units.
  - **Colouring by data** builds choropleths.
  - **Legend** has an editable title, editable entry labels and a choice of position. It can total population, density, area and subdivisions, in any combination or none.
  - **Subdivision counting rule:** a piece counts as a subdivision unless it is under 0.1 % of the average subdivision at the finest level shown, in both area and population.
- **Renaming:** click an area's name on the map to rename it. Combined areas can be named automatically after the place where most of their people live.
- **Layers:**
  - Sentinel-2 cloudless satellite imagery, down to about 60 m in big metro areas
  - ASTER elevation
  - GHSL urban / suburban / rural settlement classes
  - rivers and lakes
- **Save & share:** saved maps open from links of the form `#map-<id>`, which can be emailed through Gmail, Outlook or mailto. This needs the artifact host's shared database.
- **Picture download** with or without names, numbers and legend.

## Layout

```
site/                 the app, ready to serve as static files
  index.html          the whole app (HTML + CSS + JS in one file)
  data/
    world.gz.txt      base world geometry
    index.json        country / level index
    c/                per-country subdivision geometry, all levels
    pop.gz.txt, pop/  population figures
    lay/              raster layers: elevation, settlement, satellite (zoom levels 2–6), water
scripts/              build pipeline (downloads, simplification, population joins, raster packing)
```

## Running locally

The app fetches its data, so it has to be served over HTTP. Opening the file directly will not work.

```sh
cd site
python3 -m http.server 8000
# open http://localhost:8000/
```

Everything except **Save & share** works locally. Saving uses the claude.ai artifact database and user identity, which are not available off that host.

**Satellite detail:**

| Level | Resolution | Where | In this repo / on Pages |
|---|---|---|---|
| 2–6 | down to ~1 km | everywhere | yes |
| 7 | ~500 m | all land | yes |
| 8 | ~250 m | where people live | yes |
| 9 | ~120 m | populated regions | claude.ai version only |
| 10 | ~60 m | big metro areas | claude.ai version only |

- Levels 9–10 (about 575 MB) are left out to keep the Pages site under GitHub's 1 GB limit.
- The app checks at load time which levels the host actually has, and zooms the imagery only as far as those go.
- `scripts/range_server.py` serves local copies of levels 9–10 if you rebuild them with `scripts/s2sat.py`.

## Data sources and licences

**Boundaries:**

- Natural Earth (public domain)
- geoBoundaries, Runfola et al. (CC BY 4.0)
- © EuroGeographics for NUTS & LAU (Eurostat GISCO)
- US Census Bureau & USDA NASS
- IBGE
- OCHA/HDX (CC BY-IGO)
- INE/IGN, ISTAT, StatCan, ČSÚ, BKG, MLIT, SADER/SIAP

**Population:** the latest census for each country, as reported by national statistics offices and the UN Statistics Division.

**Layers:**

- **Satellite:** Sentinel-2 cloudless 2024 by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2024), **CC BY-NC-SA 4.0**. This licence is non-commercial, and derivatives must keep it.
- **Elevation:** NASA/METI ASTER GDEM via NASA GIBS.
- **Settlements:** GHSL GHS-SMOD 2020, Degree of Urbanisation (European Commission JRC, CC BY 4.0), masked with GHS-POP 2020.
- **Rivers & lakes:** Natural Earth.

Taiwan is shown as a province of China and Crimea as part of Ukraine, as specified for this map.
