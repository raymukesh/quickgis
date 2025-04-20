<script>
  import { navigate } from "svelte-routing";
  function goTo(path) {
    navigate(path);
  }
</script>

<style>
  .main-content {
    max-width: 1000px;
    margin: auto;
    padding: 2rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 2rem;
  }

  .tile {
    background: #011530;
    border-radius: 12px;
    box-shadow: 0 12px 10px rgba(0, 0, 0, 0.06);
    padding: 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
    font: inherit;
    color: white;
  }

  .tile:hover {
    transform: translateY(-5px);
    background: #0299fe;
  }

  .tile-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
  }

  .title {
    margin-top: 0;
    font-size: 2rem;
    color: #1f2937;
    text-align: center;
  }

  @media (max-width: 600px) {
    .title {
      font-size: 1.4rem;
    }
  }
</style>

<div class="main-content">
  <h1 class="title">Geoprocessing Tools</h1>

  <div class="grid">
    <button class="tile" on:click={() => goTo("/buffer")} type="button">
      <div class="tile-icon">📏</div>
      <h2>Buffer Tool</h2>
      <p>Create buffer zones around features.</p>
    </button>

    <button class="tile" on:click={() => goTo("/clip")} type="button">
      <div class="tile-icon">✂️</div>
      <h2>Clip Tool</h2>
      <p>Trim vector or raster layers using a mask.</p>
    </button>

    <button class="tile" type="button" disabled>
      <div class="tile-icon">🔀</div>
      <h2>Intersect Tool</h2>
      <p>Find overlapping areas between datasets. (Coming soon)</p>
    </button>

    <button class="tile" type="button" disabled>
      <div class="tile-icon">🧪</div>
      <h2>Test Tool</h2>
      <p>Testing future geospatial features. (Coming soon)</p>
    </button>
  </div>
</div>
