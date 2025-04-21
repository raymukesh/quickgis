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