<script>
  import { onMount } from 'svelte';
  import mapboxgl from 'mapbox-gl';

  let map;
  let mapContainer;
  let maskFile;
  let targetFile;
  let resultLink = '';
  let maskGeoJSON = null;
  let targetGeoJSON = null;
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

  function previewGeoJSON(file, id, color, zIndex = 0) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const geojson = JSON.parse(reader.result);
        if (id === 'mask-layer') maskGeoJSON = geojson;
        if (id === 'target-layer') targetGeoJSON = geojson;

        if (map.getLayer(id)) map.removeLayer(id);
        if (map.getSource(id)) map.removeSource(id);

        map.addSource(id, { type: 'geojson', data: geojson });
        map.addLayer({
          id,
          type: 'fill',
          source: id,
          paint: {
            'fill-color': color,
            'fill-opacity': 0.5
          }
        });

        if (zIndex) map.moveLayer(id);

        const bounds = new mapboxgl.LngLatBounds();
        geojson.features.forEach(f => {
          const coords = f.geometry.coordinates.flat(2);
          for (let i = 0; i < coords.length; i += 2) {
            bounds.extend([coords[i], coords[i + 1]]);
          }
        });
        map.fitBounds(bounds, { padding: 50 });

      } catch (err) {
        alert('Invalid GeoJSON file');
      }
    };
    reader.readAsText(file);
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

  // 🎯 If it's a raster, display on map using raster overlay
  if (targetFile.name.endsWith('.tif')) {
    if (map.getSource('raster-source')) map.removeLayer('raster-layer');
    if (map.getLayer('raster-layer')) map.removeSource('raster-source');

    rasterOverlayUrl = resultLink;

    map.addSource('raster-source', {
      type: 'image',
      url: rasterOverlayUrl,
      coordinates: [  // Temporary bounds (we can improve this)
        [74.5, 26.8],  // top left
        [75.5, 26.8],  // top right
        [75.5, 25.8],  // bottom right
        [74.5, 25.8]   // bottom left
      ]
    });

    map.addLayer({
      id: 'raster-layer',
      type: 'raster',
      source: 'raster-source',
      paint: { 'raster-opacity': 0.75 }
    });
  } else {
    const text = await blob.text();
    const resultGeoJSON = JSON.parse(text);

    if (map.getLayer('result-layer')) map.removeLayer('result-layer');
    if (map.getSource('result-layer')) map.removeSource('result-layer');

    map.addSource('result-layer', { type: 'geojson', data: resultGeoJSON });
    map.addLayer({
      id: 'result-layer',
      type: 'fill',
      source: 'result-layer',
      paint: {
        'fill-color': '#22c55e',
        'fill-opacity': 0.6
      }
    });

    map.moveLayer('mask-layer');
  }
}


</script>

<style>
  .container {
    max-width: 800px;
    margin: auto;
    padding: 1rem;
  }

  input, button {
    margin-top: 1rem;
    width: 100%;
    padding: 0.5rem;
  }

  button {
    background-color: #0ea5e9;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
  }

  button:hover {
    background-color: #0284c7;
  }

  .download {
    margin-top: 1rem;
  }

  #map {
    height: 500px;
    width: 100%;
    margin-top: 2rem;
    border: 2px solid #ccc;
    border-radius: 6px;
  }
</style>

<div class="container">
  <h2>🧩 QuickGIS Clip Tool</h2>

  <label>Upload Clipping Mask (GeoJSON Polygon)</label>
  <input type="file" accept=".geojson" on:change={(e) => { maskFile = e.target.files[0]; previewGeoJSON(maskFile, 'mask-layer', '#ef4444', 1); }} />

  <label>Upload Target Layer (GeoJSON or GeoTIFF)</label>
  <input type="file" accept=".geojson,.tif" on:change={(e) => {
    targetFile = e.target.files[0];
    if (targetFile.name.endsWith('.geojson')) {
      previewGeoJSON(targetFile, 'target-layer', '#3b82f6');
    }
  }} />

  <button on:click={handleClip}>🔪 Clip Layer</button>

  {#if isClipping}
    <p>⏳ Clipping in progress...</p>
  {:else if resultLink}

<div class="download">
    ✅ Clip complete! <a href="{resultLink}" download={targetFile.name.endsWith('.tif') ? "clipped.tif" : "clipped.geojson"}>
      Download {targetFile.name.endsWith('.tif') ? "GeoTIFF" : "GeoJSON"} Result
    </a>
  </div>
  {/if}

</div>

<div id="map" bind:this={mapContainer}></div>
