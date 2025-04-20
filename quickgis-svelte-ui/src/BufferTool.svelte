<script>
  import { onMount } from 'svelte';
  import mapboxgl from 'mapbox-gl';
  import MapboxDraw from '@mapbox/mapbox-gl-draw';

  let map;
  let mapContainer;
  let uploadedFile = null;
  let uploadedGeoJSON = null;
  let distance = '';
  let bufferGeoJSON = null;
  let resultLink = '';
  let exportFormat = 'geojson';
  let isBuffering = false;
  let drawMode = 'upload';
  let draw;
  let drawnGeoJSON = null;

  mapboxgl.accessToken = 'pk.eyJ1IjoibXVrZXNocmF5IiwiYSI6ImNtOW03cnBvMDBkc2oycnE5ZDZ2OXM2bTYifQ.gozAGZElcAVol_6beAoVDw';

  onMount(() => {
    map = new mapboxgl.Map({
      container: mapContainer,
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [78, 20],
      zoom: 5
    });

    draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: {
        point: true,
        line_string: true,
        polygon: true,
        trash: true,
      }
    });

    map.addControl(draw);
    map.on('draw.create', updateDrawn);
    map.on('draw.update', updateDrawn);
    map.on('draw.delete', () => drawnGeoJSON = null);
  });

  function updateDrawn() {
    const data = draw.getAll();
    if (data.features.length > 0) {
      drawnGeoJSON = data;
    }
  }

  async function handleFileUpload(event) {
    uploadedFile = event.target.files[0];

    if (uploadedFile.name.endsWith('.geojson')) {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          uploadedGeoJSON = JSON.parse(reader.result);
          addGeoJSONToMap(uploadedGeoJSON, 'input-layer', '#3b82f6');
        } catch (err) {
          alert('Invalid GeoJSON file.');
        }
      };
      reader.readAsText(uploadedFile);
    } else if (uploadedFile.name.endsWith('.zip')) {
      const formData = new FormData();
      formData.append("file", uploadedFile);

      const response = await fetch('http://localhost:8000/preview/', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        alert("Preview failed: " + err.error);
        return;
      }

      const geojson = await response.json();
      uploadedGeoJSON = JSON.parse(geojson);
      addGeoJSONToMap(uploadedGeoJSON, 'input-layer', '#3b82f6');
    }
  }

  async function generateBuffer() {
    if (!distance) {
      alert('Enter buffer distance.');
      return;
    }

    let geoData = null;

    if (drawMode === 'upload') {
      if (!uploadedFile) {
        alert('Please upload a file.');
        return;
      }
      geoData = uploadedFile;
    } else {
      if (!drawnGeoJSON || drawnGeoJSON.features.length === 0) {
        alert('Please draw something on the map.');
        return;
      }
      geoData = new Blob([JSON.stringify(drawnGeoJSON)], { type: 'application/json' });
    }

    isBuffering = true;
    bufferGeoJSON = null;
    resultLink = '';

    const formData = new FormData();
    formData.append('file', geoData, drawMode === 'draw' ? 'drawn.geojson' : uploadedFile.name);
    formData.append('distance', distance);
    formData.append('output_format', exportFormat);

    const response = await fetch('http://localhost:8000/buffer/', {
      method: 'POST',
      body: formData
    });

    isBuffering = false;

    if (!response.ok) {
      const err = await response.json();
      alert("Error: " + err.error);
      return;
    }

    const blobResp = await response.blob();
    resultLink = URL.createObjectURL(blobResp);

    if (exportFormat === 'geojson') {
      const text = await blobResp.text();
      bufferGeoJSON = JSON.parse(text);
      addGeoJSONToMap(bufferGeoJSON, 'buffer-layer', '#ef4444');
    }
  }

  function addGeoJSONToMap(data, id, color) {
    if (map.getLayer(id)) map.removeLayer(id);
    if (map.getSource(id)) map.removeSource(id);

    map.addSource(id, {
      type: 'geojson',
      data
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
    data.features.forEach(f => {
      const coords = f.geometry.coordinates.flat(2);
      for (let i = 0; i < coords.length; i += 2) {
        bounds.extend([coords[i], coords[i + 1]]);
      }
    });
    map.fitBounds(bounds, { padding: 50 });
  }

  function getDownloadFilename() {
    return exportFormat === 'shapefile'
      ? 'buffered_shapefile.zip'
      : exportFormat === 'kml'
      ? 'buffered.kml'
      : exportFormat === 'csv'
      ? 'buffered.csv'
      : 'buffered.geojson';
  }
</script>


<div class="container">
  <div class="left-panel">
    <div class="form-section">
      <h2>🧭 QuickGIS Buffer Tool</h2>

      <div class="mode-toggle">
        <label><input type="radio" bind:group={drawMode} value="upload" /> Upload GeoJSON/Shapefile</label>
        <label><input type="radio" bind:group={drawMode} value="draw" /> Draw on Map</label>
      </div>

      {#if drawMode === 'upload'}
        <input type="file" accept=".geojson,.zip" on:change="{handleFileUpload}" />
      {/if}

      <input type="number" placeholder="Buffer distance in meters" bind:value="{distance}" />

      <label>Select export format:</label>
      <select bind:value="{exportFormat}">
        <option value="geojson">GeoJSON (.geojson)</option>
        <option value="shapefile">Shapefile (.zip)</option>
        <option value="kml">KML (.kml)</option>
        <option value="csv">CSV (.csv)</option>
      </select>

      <button on:click="{generateBuffer}">Generate Buffer</button>

      {#if isBuffering}
        <p class="info-text">⏳ Buffering in progress...</p>
      {:else if resultLink}
        <a class="download-button" href="{resultLink}" download="{getDownloadFilename()}">
          Download Buffered {exportFormat.toUpperCase()}
        </a>
      {/if}
    </div>

    <div class="instructions">
      <p><strong>What is a Buffer?</strong><br />A buffer creates zones around map features to analyze proximity or impact areas.</p>
      <p>✅ Upload GeoJSON or zipped Shapefile</p>
      <p>✅ Or draw points, lines, or polygons directly on the map</p>
      <p>📦 Export formats: GeoJSON, Shapefile, KML, CSV</p>
    </div>
  </div>

  <div class="map-panel">
    <div id="map" bind:this="{mapContainer}"></div>
  </div>
</div>


<style>
  body {
    margin: 0;
    padding: 0;
    font-family: 'Segoe UI', sans-serif;
    background: #f5f6fa;
  }

  .container {
    display: flex;
    flex-direction: row;
    gap: 2rem;
    max-width: 1400px;
    margin: 2rem auto;
    padding: 2rem;
    box-sizing: border-box;
    min-height: calc(100vh - 4rem); /* Leaves breathing space top/bottom */
  }

  .left-panel {
    flex: 1;
    max-width: 400px;
    background: #eaeaef;
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
  input[type="number"],
  select {
    margin-top: 0.5rem;
    width: 100%;
    padding: 0.6rem 0.75rem;
    font-size: 1rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background: #fff;
  }

  input:focus,
  select:focus {
    border-color: #3b82f6;
    outline: none;
  }

  .mode-toggle {
    margin-top: 1rem;
    display: flex;
    gap: 1rem;
    font-size: 0.9rem;
    color: #4b5563;
  }

  .mode-toggle input[type="radio"] {
    margin-right: 0.5rem;
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
      height: 400px;
      position: relative;
    }

    #map {
      position: relative;
      height: 100%;
    }
  }
</style>
