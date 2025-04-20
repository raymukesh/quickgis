# QuickGIS Buffer Backend (Python)

This is a FastAPI backend for performing buffer operations on uploaded GeoJSON files.

## 🚀 How to Use

### 1. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the server
```bash
uvicorn main:app --reload
```

Server will be available at: http://localhost:8000

Your Svelte app should POST to: `http://localhost:8000/buffer/` with:
- A `file` (GeoJSON)
- A `distance` (in meters)
