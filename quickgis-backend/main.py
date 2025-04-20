from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import shutil
import os
from pathlib import Path
import uuid
from fastapi.middleware.cors import CORSMiddleware
import zipfile2 as zipfile
import tempfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow from any origin for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

## Shapefile Preview Support
@app.post("/preview/")
async def preview_shapefile(file: UploadFile = File(...)):
    try:
        input_ext = os.path.splitext(file.filename)[-1].lower()
        if input_ext != ".zip":
            return JSONResponse(status_code=400, content={"error": "Only .zip shapefile supported for preview."})

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, file.filename)
            with open(zip_path, "wb") as buffer:
                buffer.write(await file.read())

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            shp_files = [f for f in os.listdir(temp_dir) if f.endswith(".shp")]
            if not shp_files:
                return JSONResponse(status_code=400, content={"error": "No .shp file found in ZIP."})

            shp_path = os.path.join(temp_dir, shp_files[0])
            gdf = gpd.read_file(shp_path)

            if gdf.crs is None:
                gdf.set_crs(epsg=4326, inplace=True)
            else:
                gdf = gdf.to_crs(epsg=4326)

            return JSONResponse(content=gdf.to_json())

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

## Buffer Tool
@app.post("/buffer/")
async def create_buffer(
    file: UploadFile = File(...),
    distance: float = Form(...),
    output_format: str = Form("geojson")  # "geojson" or "shapefile"
):
    uid = uuid.uuid4().hex
    input_ext = Path(file.filename).suffix.lower()
    input_path = Path(UPLOAD_FOLDER) / f"{uid}_{file.filename}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # If zipped shapefile
        if input_ext == ".zip":
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(input_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                shp_files = [f for f in os.listdir(temp_dir) if f.endswith(".shp")]
                if not shp_files:
                    return JSONResponse(status_code=400, content={"error": "No .shp file found in ZIP."})
                
                shp_path = os.path.join(temp_dir, shp_files[0])
                gdf = gpd.read_file(shp_path)
        else:
            # Assume it's a single GeoJSON
            gdf = gpd.read_file(str(input_path))

        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)

        gdf_proj = gdf.to_crs(epsg=3857)
        gdf_proj["geometry"] = gdf_proj.buffer(distance)
        buffered_gdf = gdf_proj.to_crs(epsg=4326)

        if output_format == "shapefile":
            out_dir = Path(UPLOAD_FOLDER) / f"{uid}_shp"
            out_dir.mkdir(exist_ok=True)
            shp_output_path = out_dir / "buffered.shp"
            buffered_gdf.to_file(shp_output_path)
            zip_path = Path(UPLOAD_FOLDER) / f"{uid}_buffered_shapefile.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in out_dir.glob("buffered.*"):
                    zipf.write(file, arcname=file.name)
            return FileResponse(path=zip_path, filename="buffered_shapefile.zip", media_type="application/zip")
        
        if output_format == "kml":
            output_file = Path(UPLOAD_FOLDER) / f"{uid}_buffered.kml"
            buffered_gdf.to_file(output_file, driver="KML")
            return FileResponse(path=output_file, filename="buffered.kml", media_type="application/vnd.google-earth.kml+xml")

        elif output_format == "csv":
            output_file = Path(UPLOAD_FOLDER) / f"{uid}_buffered.csv"
            buffered_gdf.to_csv(output_file, index=False)
            return FileResponse(path=output_file, filename="buffered.csv", media_type="text/csv")


        else:
            output_geojson = Path(UPLOAD_FOLDER) / f"{uid}_buffered.geojson"
            buffered_gdf.to_file(output_geojson, driver="GeoJSON")
            return FileResponse(path=output_geojson, filename="buffered.geojson", media_type="application/json")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Buffer failed: {str(e)}"})


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

## Clip Tool
@app.post("/clip/")
async def clip_data(
    target_file: UploadFile = File(...),
    mask_file: UploadFile = File(...)
):
    uid = uuid.uuid4().hex
    target_path = Path(UPLOAD_FOLDER) / f"{uid}_target.{target_file.filename.split('.')[-1]}"
    mask_path = Path(UPLOAD_FOLDER) / f"{uid}_mask.geojson"
    
    with open(target_path, "wb") as f:
        shutil.copyfileobj(target_file.file, f)
    with open(mask_path, "wb") as f:
        shutil.copyfileobj(mask_file.file, f)

    try:
        # Determine whether target is raster or vector
        if target_path.suffix.lower() == ".tif":
            # Raster Clipping
            with rasterio.open(target_path) as src:
                mask_gdf = gpd.read_file(mask_path)
                if mask_gdf.crs is None:
                    mask_gdf.set_crs(epsg=4326, inplace=True)

                # Reproject mask to match raster
                mask_gdf = mask_gdf.to_crs(src.crs)

                # Clip raster using mask
                out_image, out_transform = mask(src, mask_gdf.geometry, crop=True)
                out_meta = src.meta.copy()
                out_meta.update({
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })

            output_raster = Path(UPLOAD_FOLDER) / f"{uid}_clipped.tif"
            with rasterio.open(output_raster, "w", **out_meta) as dest:
                dest.write(out_image)

            return FileResponse(path=output_raster, filename="clipped.tif", media_type='application/octet-stream')

        else:
            # Vector Clipping
            target_gdf = gpd.read_file(target_path)
            mask_gdf = gpd.read_file(mask_path)

            if target_gdf.crs is None:
                target_gdf.set_crs(epsg=4326, inplace=True)
            if mask_gdf.crs is None:
                mask_gdf.set_crs(epsg=4326, inplace=True)

            # Reproject to same CRS
            target_gdf = target_gdf.to_crs(epsg=3857)
            mask_gdf = mask_gdf.to_crs(epsg=3857)

            clipped = gpd.overlay(target_gdf, mask_gdf, how="intersection")
            clipped = clipped.to_crs(epsg=4326)

            output_vector = Path(UPLOAD_FOLDER) / f"{uid}_clipped.geojson"
            clipped.to_file(output_vector, driver="GeoJSON")

            return FileResponse(path=output_vector, filename="clipped.geojson", media_type='application/json')

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

