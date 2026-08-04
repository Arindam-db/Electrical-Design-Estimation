##  Electrical Estimator

A desktop application for room-by-room electrical load planning and cost estimation, built with **Python 3.12+ and PyQt6**.

Designed for electrical engineering students, junior engineers, and site estimators who need a fast, offline tool to generate connected-load summaries, fixture counts, wire estimates, and schematic floor plans — without CAD software.

---

##  Screenshots


![Main Window](docs/screenshots/main_window.png)

![Floor Plan Layout](docs/screenshots/layout.png)

---

##  Features

- **Room-by-room input table** — name, dimensions, room type, AC flag
- **Intelligent fixture calculation**
  - Lights and fans computed from room area with a guaranteed minimum of 1 per room
  - Sockets derived automatically from light count
- **Standards panel** — adjust m²/light, m²/fan, wire wastage factor, diversity factor
- **Results table** — area, lights, fans, sockets, AC points, connected load (W) per room
- **Summary totals** — total load (W/kW), estimated wire length, estimated cost (₹)
- **Schematic floor plan** — top-view matplotlib canvas with:
  - Multi-row automatic wrapping
  - Grid-distributed symbols (●light ⊕fan □socket ★AC)
  - Export as PNG or SVG
- **Save / Load projects** — JSON format, no database required
- **Editable cost data** — prices stored in `data/material_costs.json`, no code changes needed

---

---

## ⚙️ Installation

### Prerequisites

- Python 3.12 or 3.13
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/BuildingElectricalEstimator.git
cd BuildingElectricalEstimator

# 2. (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 3. Install dependencies
pip install PyQt6 matplotlib numpy

# 4. Run the application
python main.py
```

> **Note:** `openpyxl` and `reportlab` are listed as future dependencies for Excel/PDF export. They are not required to run the current version.

---

##  How to Use

1. **Fill in Project Information** — project name, client name, building type.
2. **Add rooms** using the *+ Add Room* button. Edit name, dimensions, room type, and check AC if applicable.
3. **Adjust standards** if needed (defaults follow general IS/NBC guidelines).
4. Click ** Calculate** — results table and summary labels populate instantly.
5. Click **🗺 Generate Layout** — a schematic floor plan renders on the right panel.
6. Use **Export PNG / SVG** buttons below the canvas to save the drawing.
7. Click ** Save Project** to save your work as a `.json` file.

---

##  Calculation Logic

| Parameter | Formula |
|---|---|
| Area | `length × width` |
| Lights | `max(1, ceil(area / m²_per_light))` |
| Fans | `max(1, ceil(area / m²_per_fan))` |
| Sockets | `2` if lights ≤ 2 · `3` if lights ≤ 4 · `4` otherwise |
| AC Point | `1` if AC selected, else `0` |
| Connected Load | `(lights×12W) + (fans×75W) + (sockets×100W) + (ac×1500W)` |
| Wire Length | `total_perimeter × wastage_factor` |
| Cost | `(material subtotal) × (1 + conduit_factor + labour_factor)` |

---

##  Editing Unit Costs

Open `data/material_costs.json` and update values — no code changes needed:

```json
{
    "light_fitting":  350.0,
    "fan":           1500.0,
    "socket_outlet":  200.0,
    "ac_point":       800.0,
    "wire_per_metre":  25.0,
    "conduit_factor":   0.15,
    "labour_factor":    0.20
}
```

---

At last thanks for using this repo 

---


Pull requests are welcome.

---

