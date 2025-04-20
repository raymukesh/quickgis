# 🌍 QuickGIS – Lightweight Geoprocessing Tools

![Status](https://img.shields.io/badge/status-in%20development-yellow.svg)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red.svg)
![Frontend](https://img.shields.io/badge/frontend-svelte-orange.svg)
![Backend](https://img.shields.io/badge/backend-fastapi-blue.svg)
![Maintainer](https://img.shields.io/badge/maintainer-Mukesh%20Ray-blueviolet)


QuickGIS is a modern, browser-based geospatial toolkit designed to perform common GIS tasks like buffering, clipping, and more — without needing to install desktop GIS software.

Built with **Svelte**, **Mapbox GL JS**, and **Python (FastAPI)**, QuickGIS is simple, fast, and easy to use for planners, researchers, and students.

---

## 🚀 Features

- 📏 **Buffer Tool**  
  Upload or draw GeoJSON/Shapefile and create buffers with specified distance. Supports export in GeoJSON, Shapefile, KML, and CSV.

- ✂️ **Clip Tool**  
  Clip a raster (GeoTIFF) or vector (GeoJSON/Shapefile) layer using a mask. Export clipped results with proper projection handling.

- 🖱️ **Draw Geometry Interactively**  
  No file? No problem. Draw points, lines, or polygons directly on the map and process them.

- 🌐 **Web-Based, No Install Required**  
  No QGIS, no ArcGIS — just a browser.

---

## 🛠 Tech Stack

- **Frontend**: Svelte, Mapbox GL JS, Mapbox Draw
- **Backend**: Python, FastAPI, GeoPandas, Rasterio and other supporting packages
- **Formats Supported**: `.geojson`, `.zip` (shapefile), `.tif`, `.kml`, `.csv`

---

## 🛡️ License
- All Rights Reserved.
- This project is proprietary. No part of this repository may be copied, distributed, or reused without explicit permission from the author.

## 🧰 Project Structure

```bash
quickgis-svelte-ui/
├── public/
├── src/
│   ├── BufferTool.svelte
│   ├── ClipTool.svelte
│   ├── Home.svelte
│   └── App.svelte
├── global.css
├── package.json
└── README.md
