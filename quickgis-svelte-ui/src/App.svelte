<script>
  import { Router, Route, Link } from 'svelte-routing';
  import Home from './Home.svelte';
  import BufferTool from './BufferTool.svelte';
  import ClipTool from './ClipTool.svelte';
  import VisualiseConvertTool from './VisualiseConvertTool.svelte';
  import { component_subscribe } from 'svelte/internal';
</script>

<Router>
  <header class="header">
    <div class="logo">🌍 QuickGIS</div>
    <nav class="nav-links">
      <Link to="/">Home</Link>
      <Link to="/buffer">Buffer Tool</Link>
      <Link to="/clip">Clip Tool</Link>
    </nav>
  </header>

  <main>
    <Route path="/" component={Home} />
    <Route path="/buffer" component={BufferTool} />
    <Route path="/clip" component={ClipTool} />
    <Route path="/visualise" component={VisualiseConvertTool} ?></Route>
  </main>

  <footer class="footer">
    <p>&copy; 2025 QuickGIS. All rights reserved.</p>
    <p>Built for geospatial analysis, visualization, and processing — no install required.</p>
  </footer>
</Router>
