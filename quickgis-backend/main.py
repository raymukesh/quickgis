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

## Visualise and Convert GIS Data
@app.post("/convert/")
async def convert_file(
    file: UploadFile = File(...),
    output_format: str = Form("geojson")
):
    uid = uuid.uuid4().hex
    temp_dir = Path(UPLOAD_FOLDER) / f"{uid}_convert"
    temp_dir.mkdir(exist_ok=True)

    try:
        input_ext = Path(file.filename).suffix.lower()
        input_path = temp_dir / f"uploaded{input_ext}"

        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Handle zipped shapefile
        if input_ext == ".zip":
            unzip_path = temp_dir / "unzipped"
            unzip_path.mkdir(exist_ok=True)
            with zipfile.ZipFile(input_path, "r") as zip_ref:
                zip_ref.extractall(unzip_path)
            shp_files = list(unzip_path.glob("*.shp"))
            if not shp_files:
                return JSONResponse(status_code=400, content={"error": "No .shp file found in ZIP."})
            gdf = gpd.read_file(shp_files[0])
        else:
            gdf = gpd.read_file(input_path)

        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        else:
            gdf = gdf.to_crs(epsg=4326)

        if output_format == "shapefile":
            out_dir = temp_dir / "out_shp"
            out_dir.mkdir(exist_ok=True)
            shp_output = out_dir / "converted.shp"
            gdf.to_file(shp_output)
            zip_path = temp_dir / "converted_shapefile.zip"
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for f in out_dir.glob("converted.*"):
                    zipf.write(f, arcname=f.name)
            return FileResponse(path=zip_path, filename="converted_shapefile.zip", media_type="application/zip")

        elif output_format == "kml":
            kml_output = temp_dir / "converted.kml"
            gdf.to_file(kml_output, driver="KML")
            return FileResponse(path=kml_output, filename="converted.kml", media_type="application/vnd.google-earth.kml+xml")

        elif output_format == "csv":
            csv_output = temp_dir / "converted.csv"
            gdf.to_csv(csv_output, index=False)
            return FileResponse(path=csv_output, filename="converted.csv", media_type="text/csv")

        else:
            geojson_output = temp_dir / "converted.geojson"
            gdf.to_file(geojson_output, driver="GeoJSON")
            return FileResponse(path=geojson_output, filename="converted.geojson", media_type="application/json")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Conversion failed: {str(e)}"})

## Shapefile Preview Support
@app.post("/preview/")
async def preview_any(file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[-1].lower()
        uid = uuid.uuid4().hex

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, "wb") as buffer:
                buffer.write(await file.read())

            if ext == ".zip":
                with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                shp_files = [f for f in os.listdir(temp_dir) if f.endswith(".shp")]
                if not shp_files:
                    return JSONResponse(status_code=400, content={"error": "No .shp found in ZIP"})
                gdf = gpd.read_file(os.path.join(temp_dir, shp_files[0]))

            elif ext == ".kml":
                gdf = gpd.read_file(temp_path, driver="KML")

            elif ext == ".csv":
                gdf = gpd.read_file(temp_path)

            elif ext == ".geojson" or ext == ".json":
                gdf = gpd.read_file(temp_path)

            else:
                return JSONResponse(status_code=400, content={"error": f"Unsupported preview format: {ext}"})

            if gdf.crs is None:
                gdf.set_crs(epsg=4326, inplace=True)
            else:
                gdf = gdf.to_crs(epsg=4326)

            return JSONResponse(content=gdf.to_json())

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Preview failed: {str(e)}"})


## Buffer Tool
@app.post("/buffer/")
async def create_buffer(
    file: UploadFile = File(...),
    distance: float = Form(...),
    output_format: str = Form("geojson")  # "geojson", "shapefile", "kml", "csv"
):
    uid = uuid.uuid4().hex
    input_ext = Path(file.filename).suffix.lower()
    input_path = Path(UPLOAD_FOLDER) / f"{uid}_{file.filename}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if input_ext == ".zip":
            # Handle zipped shapefile
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(input_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                shp_files = [f for f in os.listdir(temp_dir) if f.endswith(".shp")]
                if not shp_files:
                    return JSONResponse(status_code=400, content={"error": "No .shp file found in ZIP."})

                shp_path = os.path.join(temp_dir, shp_files[0])
                gdf = gpd.read_file(shp_path)

        elif input_ext == ".kml":
            # Handle KML file
            gdf = gpd.read_file(input_path)

        else:
            # Assume it's GeoJSON or similar
            gdf = gpd.read_file(str(input_path))

        # Set default CRS if missing
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)

        # Reproject to metric for buffer calculation
        gdf_proj = gdf.to_crs(epsg=3857)
        gdf_proj["geometry"] = gdf_proj.buffer(distance)
        buffered_gdf = gdf_proj.to_crs(epsg=4326)

        # Output in selected format
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

        elif output_format == "kml":
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
    mask_file: UploadFile = File(...),
    output_format: str = Form("geojson")
):
    uid = uuid.uuid4().hex
    temp_dir = Path(UPLOAD_FOLDER) / f"{uid}_clip"
    temp_dir.mkdir(exist_ok=True)

    def extract_shapefile(upload: UploadFile, prefix: str):
        ext = Path(upload.filename).suffix.lower()
        out_path = temp_dir / f"{prefix}_{upload.filename}"
        with open(out_path, "wb") as f:
            shutil.copyfileobj(upload.file, f)

        if ext == ".zip":
            unzip_path = temp_dir / f"{prefix}_unzipped"
            unzip_path.mkdir(exist_ok=True)
            with zipfile.ZipFile(out_path, "r") as zip_ref:
                zip_ref.extractall(unzip_path)
            shp_files = list(unzip_path.glob("*.shp"))
            if not shp_files:
                raise ValueError(f"No .shp file found in {prefix} ZIP.")
            return gpd.read_file(shp_files[0])
        else:
            return gpd.read_file(out_path)

    try:
        if target_file.filename.endswith(".tif"):
            # Raster Clip
            with rasterio.open(target_file.file) as src:
                mask_gdf = extract_shapefile(mask_file, "mask")
                if mask_gdf.crs is None:
                    mask_gdf.set_crs(epsg=4326, inplace=True)
                mask_gdf = mask_gdf.to_crs(src.crs)

                out_image, out_transform = mask(src, mask_gdf.geometry, crop=True)
                out_meta = src.meta.copy()
                out_meta.update({
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })

                output_raster = temp_dir / "clipped.tif"
                with rasterio.open(output_raster, "w", **out_meta) as dest:
                    dest.write(out_image)

            return FileResponse(path=output_raster, filename="clipped.tif", media_type='application/octet-stream')

        else:
            # Vector Clip
            target_gdf = extract_shapefile(target_file, "target")
            mask_gdf = extract_shapefile(mask_file, "mask")

            if target_gdf.crs is None:
                target_gdf.set_crs(epsg=4326, inplace=True)
            if mask_gdf.crs is None:
                mask_gdf.set_crs(epsg=4326, inplace=True)

            target_gdf = target_gdf.to_crs(epsg=3857)
            mask_gdf = mask_gdf.to_crs(epsg=3857)

            clipped = gpd.overlay(target_gdf, mask_gdf, how="intersection").to_crs(epsg=4326)

            if clipped.empty:
                return JSONResponse(status_code=400, content={"error": "Resulting clipped file is empty."})

            # Output based on format
            if output_format == "shapefile":
                shp_dir = temp_dir / "shp_output"
                shp_dir.mkdir(exist_ok=True)
                shp_output = shp_dir / "clipped.shp"
                clipped.to_file(shp_output)
                zip_path = temp_dir / "clipped_shapefile.zip"
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for f in shp_dir.glob("clipped.*"):
                        zipf.write(f, arcname=f.name)
                return FileResponse(path=zip_path, filename="clipped_shapefile.zip", media_type="application/zip")

            elif output_format == "kml":
                kml_output = temp_dir / "clipped.kml"
                clipped.to_file(kml_output, driver="KML")
                return FileResponse(path=kml_output, filename="clipped.kml", media_type="application/vnd.google-earth.kml+xml")

            elif output_format == "csv":
                csv_output = temp_dir / "clipped.csv"
                clipped.to_csv(csv_output, index=False)
                return FileResponse(path=csv_output, filename="clipped.csv", media_type="text/csv")

            else:  # Default to GeoJSON
                geojson_output = temp_dir / "clipped.geojson"
                clipped.to_file(geojson_output, driver="GeoJSON")
                return FileResponse(path=geojson_output, filename="clipped.geojson", media_type="application/json")

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Clip failed: {str(e)}"})

