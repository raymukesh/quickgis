<script>
  import { onMount } from 'svelte';
  import mapboxgl from 'mapbox-gl';

  let map;
  let mapContainer;
  let uploadedFile = null;
  let uploadedGeoJSON = null;
  let downloadLink = '';
  let selectedFormat = 'geojson';
  let uploadedMarkers = [];

  mapboxgl.accessToken = 'pk.eyJ1IjoibXVrZXNocmF5IiwiYSI6ImNtOW03cnBvMDBkc2oycnE5ZDZ2OXM2bTYifQ.gozAGZElcAVol_6beAoVDw';

  onMount(() => {
    map = new mapboxgl.Map({
      container: mapContainer,
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [78, 20],
      zoom: 4
    });
  });

  async function handleUpload(event) {
    uploadedFile = event.target.files[0];
    if (!uploadedFile) return;

    const ext = uploadedFile.name.split('.').pop().toLowerCase();

    if (ext === 'geojson' || ext === 'json') {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          uploadedGeoJSON = JSON.parse(reader.result);
          previewGeoJSON(uploadedGeoJSON, 'visualise-layer');
        } catch (err) {
          alert("Failed to read GeoJSON.");
        }
      };
      reader.readAsText(uploadedFile);
    } else if (ext === 'zip' || ext === 'kml') {
      const formData = new FormData();
      formData.append("file", uploadedFile);

      const response = await fetch("http://localhost:8000/preview/", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        alert("Preview failed: " + error.error);
        return;
      }

      const geojson = await response.json();
      uploadedGeoJSON = geojson;
      previewGeoJSON(uploadedGeoJSON, 'visualise-layer');
    } else {
      alert("Unsupported format.");
    }
  }

  function previewGeoJSON(data, id) {
    if (map.getLayer(id)) map.removeLayer(id);
    if (map.getSource(id)) map.removeSource(id);
    uploadedMarkers.forEach(marker => marker.remove());
    uploadedMarkers = [];

    const bounds = new mapboxgl.LngLatBounds();

    for (const feature of data.features) {
      const geom = feature.geometry;
      if (!geom) continue;

      if (geom.type === 'Point') {
        const [lng, lat] = geom.coordinates;
        const marker = new mapboxgl.Marker({ color: '#6366f1' })
          .setLngLat([lng, lat])
          .setPopup(new mapboxgl.Popup().setText("📍 Point"))
          .addTo(map);
        uploadedMarkers.push(marker);
        bounds.extend([lng, lat]);

      } else if (geom.type === 'MultiPoint') {
        geom.coordinates.forEach(coord => {
          const marker = new mapboxgl.Marker({ color: '#6366f1' })
            .setLngLat(coord)
            .setPopup(new mapboxgl.Popup().setText("📍 MultiPoint"))
            .addTo(map);
          uploadedMarkers.push(marker);
          bounds.extend(coord);
        });

      } else {
        map.addSource(id, { type: 'geojson', data });

        const layerType = ['LineString', 'MultiLineString'].includes(geom.type) ? 'line' : 'fill';
        map.addLayer({
          id,
          type: layerType,
          source: id,
          paint: layerType === 'line' ? {
            'line-color': '#6366f1',
            'line-width': 2
          } : {
            'fill-color': '#6366f1',
            'fill-opacity': 0.5
          }
        });

        const coords = geom.coordinates.flat(Infinity);
        for (let i = 0; i < coords.length; i += 2) {
          bounds.extend([coords[i], coords[i + 1]]);
        }
      }
    }

    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 50 });
    }
  }

  async function convertAndDownload() {
    if (!uploadedFile) {
      alert("Please upload a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", uploadedFile);
    formData.append("output_format", selectedFormat);

    const response = await fetch("http://localhost:8000/convert/", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      alert("Conversion failed: " + error.error);
      return;
    }

    const blob = await response.blob();
    downloadLink = URL.createObjectURL(blob);
  }

  function goToMyLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const lngLat = [longitude, latitude];

          map.flyTo({ center: lngLat, zoom: 12 });

          new mapboxgl.Marker({ color: '#22c55e' })
            .setLngLat(lngLat)
            .setPopup(new mapboxgl.Popup().setText("📍 You are here!"))
            .addTo(map);
        },
        (error) => {
          alert("📌 Location access denied or unavailable.");
          console.warn("Geolocation error:", error.message);
        }
      );
    } else {
      alert("Geolocation is not supported by your browser.");
    }
  }

  function getDownloadName() {
    return selectedFormat === 'shapefile'
      ? 'converted_shapefile.zip'
      : selectedFormat === 'kml'
      ? 'converted.kml'
      : selectedFormat === 'csv'
      ? 'converted.csv'
      : 'converted.geojson';
  }
</script>

<!-- Layout and CSS remain the same -->


<!-- Layout HTML -->
<div class="container">
  <div class="left-panel">
    <div class="form-section">
      <h2>📂 QuickGIS Visualise Tool</h2>

      <label>Upload Spatial File (.geojson, .zip, .kml)</label>
      <input type="file" on:change={handleUpload} accept=".geojson,.zip,.kml" />

      <label>Convert to:</label>
      <select bind:value={selectedFormat}>
        <option value="geojson">GeoJSON (.geojson)</option>
        <option value="shapefile">Shapefile (.zip)</option>
        <option value="kml">KML (.kml)</option>
        <option value="csv">CSV (.csv)</option>
      </select>

      <button on:click={convertAndDownload}>Convert & Download</button>

      {#if downloadLink}
        <a class="download-button" href={downloadLink} download={getDownloadName()}>
          📥 Download {selectedFormat.toUpperCase()}
        </a>
      {/if}
    </div>

    <button class="location-button" on:click={goToMyLocation}>
      📍 Go to My Location
    </button>

    <div class="instructions">
      <p><strong>What is Visualise & Convert?</strong><br />
        Upload any spatial file (GeoJSON, Shapefile ZIP, or KML), preview it on the map, and convert it to other formats.
      </p>
      <p>✅ Upload supported formats: .geojson, .zip, .kml</p>
      <p>📦 Convert to: GeoJSON, Shapefile, KML, CSV</p>
    </div>
  </div>

  <div class="map-panel">
    <div id="map" bind:this={mapContainer}></div>
  </div>
</div>

<!-- Add your existing CSS here (unchanged) -->


<style>
  .container {
    display: flex;
    gap: 2rem;
    max-width: 1400px;
    margin: 2rem auto;
    padding: 2rem;
    min-height: calc(100vh - 4rem);
    box-sizing: border-box;
  }
  
  .left-panel {
    flex: 1;
    max-width: 400px;
    background: #eaeaef;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  
  .map-panel {
    flex: 2;
    position: relative;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
    min-height: 600px;
  }
  
  #map {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
    border: 2px solid #d1d5db;
    border-radius: 10px;
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
    background: #0284c7;
  }
  
  .download-button {
    margin-top: 1rem;
    display: block;
    text-align: center;
    background: #2563eb;
    color: white;
    padding: 0.75rem;
    border-radius: 6px;
    font-weight: bold;
    text-decoration: none;
  }
  
  .download-button:hover {
    background: #1d4ed8;
  }
  
  .location-button {
  margin-top: 1rem;
  margin-bottom: 0.5rem; /* 🔽 Add this line or reduce if already present */
  background: #10b981;
  color: white;
  font-weight: bold;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s ease;
  width: 100%;
}
  
  .location-button:hover {
        background: #059669;
      }
     
  .instructions {
    font-size: 0.9rem;
    color: #4b5563;
    margin-top: 0.5rem;
    line-height: 1.4;
  }
    
  label {
    font-weight: 600;
    font-size: 0.95rem;
    margin-top: 1rem;
    color: #374151;
    display: block;
  }
  
  input,
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
  
  /* 🔽 Mobile layout responsiveness */
  @media (max-width: 900px) {
    .container {
      flex-direction: column;
      padding: 1rem;
    }
  
    .map-panel {
      position: relative;
      min-height: 400px;
      height: 400px;
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