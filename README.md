#Building Electrical Estimator (BEE)

A desktop application for room-by-room electrical load planning and cost estimation, built with **Python 3.12+ and PyQt6**.

Designed for electrical engineering students, junior engineers, and site estimators who need a fast, offline tool to generate connected-load summaries, fixture counts, wire estimates, and schematic floor plans — without CAD software.

---

## 📸 Screenshots

> Add screenshots here after your first run.  
> `docs/screenshots/main_window.png`, `docs/screenshots/layout.png`

---

## ✨ Features

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

## 🗂️ Project Structure

```
BuildingElectricalEstimator/
├── main.py                      # Entry point
├── ui/
│   ├── main_window.py           # All GUI layout and event handling
│   └── dialogs.py               # Placeholder for future dialogs
├── calculations/
│   ├── load_calc.py             # Core formulas (lights, fans, sockets, load)
│   ├── wire_calc.py             # Wire length estimation
│   └── material_calc.py        # Cost estimation (loads from JSON)
├── drawing/
│   └── layout_drawer.py        # Matplotlib floor-plan widget
├── reports/
│   ├── excel_export.py          # Placeholder
│   └── pdf_export.py           # Placeholder
├── data/
│   ├── standards.json           # Default estimation standards
│   └── material_costs.json     # Unit costs in ₹ (editable)
└── saved_projects/             # User project files (auto-created)
```

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

## 🚀 How to Use

1. **Fill in Project Information** — project name, client name, building type.
2. **Add rooms** using the *+ Add Room* button. Edit name, dimensions, room type, and check AC if applicable.
3. **Adjust standards** if needed (defaults follow general IS/NBC guidelines).
4. Click **⚡ Calculate** — results table and summary labels populate instantly.
5. Click **🗺 Generate Layout** — a schematic floor plan renders on the right panel.
6. Use **Export PNG / SVG** buttons below the canvas to save the drawing.
7. Click **💾 Save Project** to save your work as a `.json` file.

---

## 🔢 Calculation Logic

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

## 💰 Editing Unit Costs

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

## 🛠️ Tech Stack

| Library | Purpose |
|---|---|
| PyQt6 | GUI framework |
| matplotlib | Embedded floor-plan canvas |
| numpy | Symbol position distribution (linspace) |
| json (stdlib) | Project save/load, cost config |

---

## 🗺️ Roadmap

- [ ] Excel report export (`openpyxl`)
- [ ] PDF estimation report (`reportlab`)
- [ ] Room-type-specific rules (bathroom, store room, kitchen)
- [ ] Conduit and DB sizing suggestions
- [ ] Multi-floor support
- [ ] Windows `.exe` packaging via PyInstaller

---

## 👨‍💻 Author

**Arindam**  
Electrical Engineering, 6th Semester  
Tripura Institute of Technology (TIT), Narsingarh  

Mini project developed as part of academic learning in building electrical systems and desktop application development.

---

## 📄 License

This project is released under the [MIT License](LICENSE).

You are free to use, modify, and distribute this software for personal, academic, or commercial purposes with attribution.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add: your feature description"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## ⭐ Acknowledgements

- PyQt6 documentation — https://doc.qt.io/qtforpython/
- matplotlib embedding guide — https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html
- IS 732 / NBC 2016 — reference standards for electrical estimation rules
