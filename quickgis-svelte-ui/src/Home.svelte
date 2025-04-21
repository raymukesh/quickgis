<script>
  import { onMount } from "svelte";
  import { navigate } from "svelte-routing";
  import mapboxgl from "mapbox-gl";

  let map;
  let mapContainer;

  mapboxgl.accessToken = 'pk.eyJ1IjoibXVrZXNocmF5IiwiYSI6ImNtOW03cnBvMDBkc2oycnE5ZDZ2OXM2bTYifQ.gozAGZElcAVol_6beAoVDw';// Replace with your token

  onMount(() => {
    map = new mapboxgl.Map({
      container: mapContainer,
      style: "mapbox://styles/mapbox/streets-v11",
      center: [78, 20],
      zoom: 4
    });

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          map.flyTo({ center: [longitude, latitude], zoom: 12 });

          new mapboxgl.Marker({ color: "#22c55e" })
            .setLngLat([longitude, latitude])
            .setPopup(new mapboxgl.Popup().setText("📍 You are here!"))
            .addTo(map);
        },
        (err) => console.warn("Geolocation error:", err)
      );
    }
  });

  function goTo(path) {
    navigate(path);
  }
</script>

<style>
  .container {
    display: flex;
    gap: 2rem;
    padding: 2rem;
    max-width: 1400px;
    margin: auto;
    box-sizing: border-box;
  }

  .left-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .tile {
    background: #011530;
    border-radius: 10px;
    color: white;
    padding: 1.2rem;
    cursor: pointer;
    text-align: center;
    transition: 0.3s;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  }

  .tile:hover {
    background: #0284c7;
  }

  .tile-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }

  .map-panel {
    flex: 2;
    min-height: 600px;
    border: 2px solid #ccc;
    border-radius: 12px;
    overflow: hidden;
    position: relative;
  }

  #map {
    position: absolute;
    top: 0; bottom: 0; left: 0; right: 0;
  }

  @media (max-width: 900px) {
    .container {
      flex-direction: column;
      padding: 1rem;
    }

    .map-panel {
      height: 400px;
    }
  }
</style>

<div class="container">
  <div class="left-panel">
    <div class="tile" on:click={() => goTo("/visualise")}>
      <div class="tile-icon">🗺️</div>
      <h3>Visualise & Convert</h3>
      <p>View spatial data & convert formats</p>
    </div>

    <div class="tile" on:click={() => goTo("/buffer")}>
      <div class="tile-icon">📏</div>
      <h3>Buffer Tool</h3>
      <p>Create buffer zones around features</p>
    </div>

    <div class="tile" on:click={() => goTo("/clip")}>
      <div class="tile-icon">✂️</div>
      <h3>Clip Tool</h3>
      <p>Trim data using a mask layer</p>
    </div>

    <div class="tile" disabled>
      <div class="tile-icon">🔀</div>
      <h3>Intersect Tool</h3>
      <p>(Coming soon)</p>
    </div>
  </div>

  <div class="map-panel">
    <div id="map" bind:this={mapContainer}></div>
  </div>
</div>
