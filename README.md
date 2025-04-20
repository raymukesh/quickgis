# 🌍 QuickGIS – Lightweight Geoprocessing Tools

![Status](https://img.shields.io/badge/status-in%20development-yellow.svg)
![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red.svg)
![Frontend](https://img.shields.io/badge/frontend-svelte-orange.svg)
![Backend](https://img.shields.io/badge/backend-fastapi-blue.svg)
![Maintainer](https://img.shields.io/badge/maintainer-Mukesh%20Ray-blueviolet)

QuickGIS is a modern, browser-based geospatial toolkit designed to perform common GIS tasks like buffering, clipping, and more — without needing desktop GIS software.

Built using **Svelte** for the frontend and **FastAPI** for the backend, it simplifies geoprocessing for planners, researchers, and students alike.

---

## 🚀 Features

- 📏 **Buffer Tool**  
  Upload or draw GeoJSON/Shapefile and create buffers with specified distance. Supports export in GeoJSON, Shapefile, KML, and CSV.

- ✂️ **Clip Tool**  
  Clip a raster (GeoTIFF) or vector (GeoJSON/Shapefile) layer using a mask. Automatically handles reprojection. Export in your preferred format.

- ✍️ **Draw Interactively**  
  Draw points, lines, or polygons directly on the map and apply buffer operations without needing external files.

- 📁 **Multi-format Support**  
  Upload and export in `.geojson`, `.zip` (shapefile), `.tif`, `.kml`, and `.csv`.

- 🌐 **Browser-based**  
  Lightweight and accessible — just open in your browser and go.

---

## 🛠 Tech Stack

| Layer     | Stack                       |
|-----------|-----------------------------|
| Frontend  | Svelte, Mapbox GL JS, Draw  |
| Backend   | Python, FastAPI, GeoPandas, Rasterio |
| Formats   | GeoJSON, Shapefile (ZIP), GeoTIFF, CSV, KML |

---

## 📁 Project Structure

```
quickgis/
├── frontend/         # Svelte-based UI
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/          # FastAPI backend
│   ├── main.py
│   ├── requirements.txt
│   └── environment.yml
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 🖼️ Frontend (Svelte)

```bash
cd frontend
npm install
npm run dev
```

> Runs at: http://localhost:8080

---

### 🚀 Backend (FastAPI)

#### Using Conda + `environment.yml`:

```bash
cd backend
conda env create -f environment.yml
conda activate webApp
uvicorn main:app --reload
```

> Runs at: http://localhost:8000

---

## 📦 Core Dependencies

### From `environment.yml`:

```yaml
python=3.10
fastapi=0.109.0
uvicorn=0.27.1
geopandas=1.0.1
fiona=1.9.6
shapely=2.0.3
rasterio=1.4.2
zipfile2=0.0.12
python-multipart=0.0.9
```

---

## 🧪 Usage Highlights

- Upload **GeoJSON or zipped Shapefiles** directly
- Draw geometry on the map instead of uploading
- Choose **export format** (GeoJSON, Shapefile, KML, CSV)
- All processing is done via **FastAPI endpoints**
- Frontend communicates with backend via REST calls

---

## 🛡️ License

**All Rights Reserved**  
This project is proprietary and intended for academic and research purposes.  
No part of this repository may be copied or redistributed without written permission.

---

## 👤 Author

**Mukesh Ray**  
🟠 [GitHub](https://github.com/raymukesh)  