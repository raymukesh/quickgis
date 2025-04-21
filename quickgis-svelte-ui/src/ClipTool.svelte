<script>
  import { onMount } from 'svelte';
  import mapboxgl from 'mapbox-gl';

  let map;
  let mapContainer;
  let maskFile;
  let targetFile;
  let resultLink = '';
  let exportFormat = 'geojson';
  let isClipping = false;
  let rasterOverlayUrl = null;

  mapboxgl.accessToken = 'pk.eyJ1IjoibXVrZXNocmF5IiwiYSI6ImNtOW03cnBvMDBkc2oycnE5ZDZ2OXM2bTYifQ.gozAGZElcAVol_6beAoVDw';

  onMount(() => {
    map = new mapboxgl.Map({
      container: mapContainer,
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [78, 20],
      zoom: 5
    });
  });

  async function previewLayer(file, id, color) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://localhost:8000/preview/", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const err = await response.json();
      alert("Preview failed: " + err.error);
      return;
    }

    const geojson = await response.json();

    if (map.getLayer(id)) map.removeLayer(id);
    if (map.getSource(id)) map.removeSource(id);

    map.addSource(id, {
      type: 'geojson',
      data: JSON.parse(geojson)
    });

    map.addLayer({
      id,
      type: 'fill',
      source: id,
      paint: {
        'fill-color': color,
        'fill-opacity': 0.5
      }
    });

    const bounds = new mapboxgl.LngLatBounds();
    JSON.parse(geojson).features.forEach(f => {
      const coords = f.geometry.coordinates.flat(2);
      for (let i = 0; i < coords.length; i += 2) {
        bounds.extend([coords[i], coords[i + 1]]);
      }
    });
    map.fitBounds(bounds, { padding: 50 });
  }

  async function handleClip() {
    if (!maskFile || !targetFile) {
      alert('Please upload both files.');
      return;
    }

    isClipping = true;
    resultLink = null;
    rasterOverlayUrl = null;

    const formData = new FormData();
    formData.append('mask_file', maskFile);
    formData.append('target_file', targetFile);
    formData.append('output_format', exportFormat);

    const response = await fetch('http://localhost:8000/clip/', {
      method: 'POST',
      body: formData
    });

    isClipping = false;

    if (!response.ok) {
      const err = await response.json();
      alert("Clip failed: " + err.error);
      return;
    }

    const blob = await response.blob();
    resultLink = URL.createObjectURL(blob);

    if (targetFile.name.endsWith('.tif')) {
      if (map.getLayer('raster-layer')) map.removeLayer('raster-layer');
      if (map.getSource('raster-source')) map.removeSource('raster-source');

      rasterOverlayUrl = resultLink;

      map.addSource('raster-source', {
        type: 'image',
        url: rasterOverlayUrl,
        coordinates: [
          [74.5, 26.8],
          [75.5, 26.8],
          [75.5, 25.8],
          [74.5, 25.8]
        ]
      });

      map.addLayer({
        id: 'raster-layer',
        type: 'raster',
        source: 'raster-source',
        paint: { 'raster-opacity': 0.75 }
      });
    } else if (exportFormat === 'geojson') {
      const text = await blob.text();
      const resultGeoJSON = JSON.parse(text);

      if (map.getLayer('result-layer')) map.removeLayer('result-layer');
      if (map.getSource('result-layer')) map.removeSource('result-layer');

      map.addSource('result-layer', {
        type: 'geojson',
        data: resultGeoJSON
      });

      map.addLayer({
        id: 'result-layer',
        type: 'fill',
        source: 'result-layer',
        paint: {
          'fill-color': '#22c55e',
          'fill-opacity': 0.6
        }
      });
    }
  }

  function getDownloadFilename() {
    return exportFormat === 'shapefile'
      ? 'clipped_shapefile.zip'
      : exportFormat === 'kml'
      ? 'clipped.kml'
      : exportFormat === 'csv'
      ? 'clipped.csv'
      : exportFormat === 'tif'
      ? 'clipped.tif'
      : 'clipped.geojson';
  }
</script>

<div class="container">
  <div class="left-panel">
    <div class="form-section">
      <h2>✂️ QuickGIS Clip Tool</h2>

      <label>Upload Clipping Mask (.geojson or .zip)</label>
      <input type="file" accept=".geojson,.zip" on:change={(e) => { maskFile = e.target.files[0]; previewLayer(maskFile, 'mask-layer', '#ef4444'); }} />

      <label>Upload Target Layer (.geojson, .zip, or .tif)</label>
      <input type="file" accept=".geojson,.zip,.tif" on:change={(e) => { targetFile = e.target.files[0]; if (!targetFile.name.endsWith('.tif')) previewLayer(targetFile, 'target-layer', '#3b82f6'); }} />

      <label>Select export format:</label>
      <select bind:value="{exportFormat}">
        <option value="geojson">GeoJSON (.geojson)</option>
        <option value="shapefile">Shapefile (.zip)</option>
        <option value="kml">KML (.kml)</option>
        <option value="csv">CSV (.csv)</option>
        <option value="tif">GeoTIFF (.tif)</option>
      </select>

      <button on:click="{handleClip}">Clip Layers</button>

      {#if isClipping}
        <p class="info-text">⏳ Clipping in progress...</p>
      {:else if resultLink}
        <a class="download-button" href="{resultLink}" download="{getDownloadFilename()}">
          ✅ Download Clipped {exportFormat.toUpperCase()}
        </a>
      {/if}
    </div>

    <div class="instructions">
      <p><strong>What is Clipping?</strong><br />Clipping trims a vector or raster to the extent of another polygon layer.</p>
      <p>✅ Supports GeoJSON, Shapefile (.zip), and raster (TIFF)</p>
      <p>🎯 Export: GeoJSON, Shapefile, KML, CSV, TIFF</p>
    </div>
  </div>

  <div class="map-panel">
    <div id="map" bind:this="{mapContainer}"></div>
  </div>
</div>

<style>
  .container {
    display: flex;
    flex-direction: row;
    gap: 2rem;
    max-width: 1400px;
    margin: 2rem auto;
    padding: 2rem;
    box-sizing: border-box;
    min-height: calc(100vh - 4rem);
  }

  .left-panel {
    flex: 1;
    max-width: 400px;
    background: #f0f4f8;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .form-section {
    flex-grow: 1;
  }

  .map-panel {
    flex: 2;
    min-height: 600px;
    position: relative;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  }

  #map {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    left: 0;
    border: 2px solid #d1d5db;
    border-radius: 10px;
  }

  h2 {
    font-size: 1.5rem;
    color: #1f2937;
    margin-bottom: 1rem;
  }

  label {
    font-weight: 600;
    font-size: 0.95rem;
    margin-top: 1rem;
    color: #374151;
  }

  input[type="file"],
  select {
    margin-top: 0.5rem;
    width: 100%;
    padding: 0.6rem 0.75rem;
    font-size: 1rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: #fff;
  }

  button {
    margin-top: 2rem;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: bold;
    background-color: #0ea5e9;
    color: #fff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.3s ease;
    width: 100%;
  }

  button:hover {
    background-color: #0284c7;
  }

  .info-text,
  .instructions {
    font-size: 0.9rem;
    color: #4b5563;
    margin-top: 1rem;
    line-height: 1.4;
  }

  .download-button {
    margin-top: 1.5rem;
    display: block;
    padding: 0.75rem 1rem;
    background: #2563eb;
    color: #fff;
    font-weight: bold;
    text-align: center;
    border-radius: 6px;
    text-decoration: none;
    transition: background 0.3s ease;
  }

  .download-button:hover {
    background: #1d4ed8;
  }

  @media (max-width: 900px) {
  .container {
    flex-direction: column;
    padding: 1rem;
  }

  .map-panel {
    position: relative;
    min-height: 400px; /* 🔄 Ensure map is tall enough */
    height: 400px;      /* 💡 Fix height explicitly */
  }

  #map {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    left: 0;
    height: 100%;
  }
}

</style>