"""
ui/main_window.py
Main application window for the Building Electrical Estimator.
Handles all UI layout, user interactions, and coordinates with
calculation and drawing modules.
"""

import json
import os
from math import ceil
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from calculations.load_calc import calculate_room_loads, RoomInput, RoomResult
from calculations.wire_calc import estimate_wire_length
from calculations.material_calc import estimate_cost
from drawing.layout_drawer import LayoutDrawer


# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────
ROOM_TABLE_COLS = ["Room Name", "Length (m)", "Width (m)", "Height (m)", "Room Type", "AC"]
RESULT_TABLE_COLS = ["Room", "Area (m²)", "Lights", "Fans", "Sockets", "AC Point", "Load (W)"]

ROOM_TYPES = ["Bedroom", "Living Room", "Kitchen", "Bathroom", "Office", "Hall", "Store", "Other"]
BUILDING_TYPES = ["Residential", "Apartment", "Office", "Hospital", "School"]


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Building Electrical Estimator")
        self.setMinimumSize(1200, 750)
        # Stores the last successful calculation results so Generate Layout
        # can consume pre-computed values instead of re-calculating.
        self._last_results: list[RoomResult] = []
        self._build_ui()

    # ──────────────────────────────────────────
    #  UI Construction
    # ──────────────────────────────────────────

    def _build_ui(self) -> None:
        """Assemble the full window layout."""
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(10, 10, 10, 10)

        # Left panel: inputs + results (scrollable)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        left_scroll.setWidget(left_panel)

        left_layout.addWidget(self._build_project_info())
        left_layout.addWidget(self._build_room_table())
        left_layout.addWidget(self._build_standards())
        left_layout.addWidget(self._build_action_buttons())
        left_layout.addWidget(self._build_results_table())
        left_layout.addWidget(self._build_summary())
        left_layout.addStretch()

        # Right panel: layout drawing
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        draw_label = QLabel("Floor Plan Layout")
        draw_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(draw_label)

        self.drawer = LayoutDrawer()
        right_layout.addWidget(self.drawer, stretch=1)

        # Splitter so user can resize
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_scroll)
        splitter.addWidget(right_panel)
        splitter.setSizes([700, 500])
        root_layout.addWidget(splitter)

    # ── Project Info ──────────────────────────

    def _build_project_info(self) -> QGroupBox:
        group = QGroupBox("Project Information")
        layout = QHBoxLayout(group)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Project Name")

        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("Client Name")

        self.building_type_combo = QComboBox()
        self.building_type_combo.addItems(BUILDING_TYPES)

        for label_text, widget in [
            ("Project:", self.project_name_input),
            ("Client:", self.client_name_input),
            ("Building Type:", self.building_type_combo),
        ]:
            layout.addWidget(QLabel(label_text))
            layout.addWidget(widget)

        return group

    # ── Room Input Table ──────────────────────

    def _build_room_table(self) -> QGroupBox:
        group = QGroupBox("Room Input")
        layout = QVBoxLayout(group)

        self.room_table = QTableWidget(0, len(ROOM_TABLE_COLS))
        self.room_table.setHorizontalHeaderLabels(ROOM_TABLE_COLS)
        self.room_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.room_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.room_table.setMinimumHeight(180)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add Room")
        add_btn.clicked.connect(self._add_room_row)
        del_btn = QPushButton("− Delete Selected")
        del_btn.clicked.connect(self._delete_room_row)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()

        layout.addWidget(self.room_table)
        layout.addLayout(btn_row)
        return group

    # ── Standards ────────────────────────────

    def _build_standards(self) -> QGroupBox:
        group = QGroupBox("Estimation Standards")
        layout = QHBoxLayout(group)

        # (label, attribute_name, min, max, default, decimals, step)
        fields = [
            ("m²/Light",      "std_lighting_area",   1.0,  50.0,  9.0,  1, 0.5),
            ("m²/Fan",        "std_fan_area",         1.0,  50.0, 12.0,  1, 0.5),
            ("Sockets/Room",  "std_sockets",          1,    20,    3,    0, 1),
            ("Wire Wastage",  "std_wire_wastage",     1.0,   5.0,  1.3,  2, 0.05),
            ("Diversity",     "std_diversity",        0.1,   1.0,  0.8,  2, 0.05),
        ]

        for label_text, attr, mn, mx, default, decimals, step in fields:
            layout.addWidget(QLabel(label_text))
            if decimals == 0:
                spin = QSpinBox()
                spin.setRange(int(mn), int(mx))
                spin.setValue(int(default))
            else:
                spin = QDoubleSpinBox()
                spin.setRange(mn, mx)
                spin.setValue(default)
                spin.setDecimals(decimals)
                spin.setSingleStep(step)
            spin.setFixedWidth(80)
            setattr(self, attr, spin)
            layout.addWidget(spin)

        layout.addStretch()
        return group

    # ── Action Buttons ────────────────────────

    def _build_action_buttons(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        buttons = [
            ("⚡ Calculate",       self._calculate),
            ("🗺  Generate Layout", self._generate_layout),
            ("🗑  Clear",           self._clear_all),
            ("💾 Save Project",    self._save_project),
            ("📂 Load Project",    self._load_project),
        ]
        for label, slot in buttons:
            btn = QPushButton(label)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setMinimumHeight(32)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        return widget

    # ── Results Table ─────────────────────────

    def _build_results_table(self) -> QGroupBox:
        group = QGroupBox("Calculation Results")
        layout = QVBoxLayout(group)

        self.result_table = QTableWidget(0, len(RESULT_TABLE_COLS))
        self.result_table.setHorizontalHeaderLabels(RESULT_TABLE_COLS)
        self.result_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setMinimumHeight(160)

        layout.addWidget(self.result_table)
        return group

    # ── Summary Labels ────────────────────────

    def _build_summary(self) -> QGroupBox:
        group = QGroupBox("Summary")
        layout = QHBoxLayout(group)

        # Left column
        left = QVBoxLayout()
        right = QVBoxLayout()

        self.lbl_lights    = QLabel("Total Lights:       —")
        self.lbl_fans      = QLabel("Total Fans:         —")
        self.lbl_sockets   = QLabel("Total Sockets:      —")
        self.lbl_ac        = QLabel("Total AC Points:    —")
        self.lbl_load      = QLabel("Total Load:         —")
        self.lbl_wire      = QLabel("Est. Wire Length:   —")
        self.lbl_cost      = QLabel("Est. Cost:          —")

        for lbl in [self.lbl_lights, self.lbl_fans, self.lbl_sockets, self.lbl_ac]:
            lbl.setFont(QFont("Courier New", 9))
            left.addWidget(lbl)

        for lbl in [self.lbl_load, self.lbl_wire, self.lbl_cost]:
            lbl.setFont(QFont("Courier New", 9))
            right.addWidget(lbl)

        layout.addLayout(left)
        layout.addLayout(right)
        layout.addStretch()
        return group

    # ──────────────────────────────────────────
    #  Room Table Helpers
    # ──────────────────────────────────────────

    def _add_room_row(self) -> None:
        """Insert a new editable row in the room input table."""
        row = self.room_table.rowCount()
        self.room_table.insertRow(row)

        # Default text for Room Name
        self.room_table.setItem(row, 0, QTableWidgetItem(f"Room {row + 1}"))

        # Numeric defaults for Length / Width / Height
        for col, default in [(1, "4.0"), (2, "3.5"), (3, "2.8")]:
            self.room_table.setItem(row, col, QTableWidgetItem(default))

        # Room type combo
        room_type_combo = QComboBox()
        room_type_combo.addItems(ROOM_TYPES)
        self.room_table.setCellWidget(row, 4, room_type_combo)

        # AC checkbox (centred)
        ac_widget = QWidget()
        ac_layout = QHBoxLayout(ac_widget)
        ac_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ac_layout.setContentsMargins(0, 0, 0, 0)
        ac_cb = QCheckBox()
        ac_layout.addWidget(ac_cb)
        self.room_table.setCellWidget(row, 5, ac_widget)

    def _delete_room_row(self) -> None:
        """Remove the currently selected row."""
        selected = self.room_table.currentRow()
        if selected >= 0:
            self.room_table.removeRow(selected)
        else:
            QMessageBox.information(self, "No Selection", "Please select a row to delete.")

    def _read_room_inputs(self) -> list[RoomInput]:
        """
        Parse all rows from the room table.
        Skips rows with missing or invalid numeric data.
        """
        rooms: list[RoomInput] = []
        for row in range(self.room_table.rowCount()):
            try:
                name   = (self.room_table.item(row, 0) or QTableWidgetItem("")).text().strip() or f"Room {row+1}"
                length = float((self.room_table.item(row, 1) or QTableWidgetItem("0")).text())
                width  = float((self.room_table.item(row, 2) or QTableWidgetItem("0")).text())
                height = float((self.room_table.item(row, 3) or QTableWidgetItem("0")).text())

                # Room type from combo
                combo = self.room_table.cellWidget(row, 4)
                room_type = combo.currentText() if combo else "Other"

                # AC from checkbox
                ac_widget = self.room_table.cellWidget(row, 5)
                has_ac = False
                if ac_widget:
                    cb = ac_widget.findChild(QCheckBox)
                    has_ac = cb.isChecked() if cb else False

                if length <= 0 or width <= 0:
                    continue  # skip degenerate rooms

                rooms.append(RoomInput(
                    name=name,
                    length=length,
                    width=width,
                    height=height,
                    room_type=room_type,
                    has_ac=has_ac,
                ))
            except (ValueError, AttributeError):
                continue  # skip rows with non-numeric cells
        return rooms

    # ──────────────────────────────────────────
    #  Action Handlers
    # ──────────────────────────────────────────

    def _calculate(self) -> None:
        """Read room inputs, run calculations, populate results."""
        rooms = self._read_room_inputs()
        if not rooms:
            QMessageBox.warning(self, "No Rooms", "Add at least one valid room before calculating.")
            return

        lighting_area = self.std_lighting_area.value()
        fan_area      = self.std_fan_area.value()
        sockets       = self.std_sockets.value()
        wastage       = self.std_wire_wastage.value()
        diversity     = self.std_diversity.value()

        results: list[RoomResult] = calculate_room_loads(
            rooms,
            lighting_area_per_light=lighting_area,
            fan_area_per_fan=fan_area,
            sockets_per_room=sockets,
        )

        # Store for use by Generate Layout — drawer reads these, never recalculates
        self._last_results = results

        # Populate results table
        self.result_table.setRowCount(0)
        for res in results:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            for col, value in enumerate([
                res.name,
                f"{res.area:.2f}",
                str(res.lights),
                str(res.fans),
                str(res.sockets),
                str(res.ac_point),
                str(res.connected_load_w),
            ]):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.result_table.setItem(row, col, item)

        # Compute totals
        total_lights  = sum(r.lights         for r in results)
        total_fans    = sum(r.fans           for r in results)
        total_sockets = sum(r.sockets        for r in results)
        total_ac      = sum(r.ac_point       for r in results)
        total_load    = sum(r.connected_load_w for r in results)
        total_perimeter = sum(2 * (r.length + r.width) for r in rooms)

        wire_length = estimate_wire_length(total_perimeter, wastage)
        cost        = estimate_cost(
            total_lights, total_fans, total_sockets, total_ac, wire_length
        )

        # Update summary labels
        self.lbl_lights .setText(f"Total Lights:       {total_lights}")
        self.lbl_fans   .setText(f"Total Fans:         {total_fans}")
        self.lbl_sockets.setText(f"Total Sockets:      {total_sockets}")
        self.lbl_ac     .setText(f"Total AC Points:    {total_ac}")
        self.lbl_load   .setText(f"Total Load:         {total_load:,} W  ({total_load/1000:.2f} kW)")
        self.lbl_wire   .setText(f"Est. Wire Length:   {wire_length:.1f} m")
        self.lbl_cost   .setText(f"Est. Cost:          ₹ {cost:,.0f}")

    def _generate_layout(self) -> None:
        """Pass pre-calculated results to the drawing widget.
        Results must exist — run Calculate first."""
        if not self._last_results:
            QMessageBox.warning(
                self, "No Results",
                "Please run '⚡ Calculate' before generating the layout."
            )
            return
        self.drawer.draw_layout(self._last_results)

    def _clear_all(self) -> None:
        """Reset all inputs, tables, labels, and the drawing area."""
        self.project_name_input.clear()
        self.client_name_input.clear()
        self.building_type_combo.setCurrentIndex(0)

        self.room_table.setRowCount(0)
        self.result_table.setRowCount(0)
        self._last_results = []  # clear stored results

        for lbl in [
            self.lbl_lights, self.lbl_fans, self.lbl_sockets,
            self.lbl_ac, self.lbl_load, self.lbl_wire, self.lbl_cost,
        ]:
            # Reset label text to placeholder
            lbl.setText(lbl.text().split(":")[0] + ":       —")

        self.drawer.clear()

    # ── Save / Load ───────────────────────────

    def _save_project(self) -> None:
        """Serialize project to a JSON file chosen by the user."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "saved_projects/", "JSON Files (*.json)"
        )
        if not path:
            return

        data = {
            "project_name":  self.project_name_input.text(),
            "client_name":   self.client_name_input.text(),
            "building_type": self.building_type_combo.currentText(),
            "standards": {
                "lighting_area": self.std_lighting_area.value(),
                "fan_area":      self.std_fan_area.value(),
                "sockets":       self.std_sockets.value(),
                "wire_wastage":  self.std_wire_wastage.value(),
                "diversity":     self.std_diversity.value(),
            },
            "rooms": [],
        }

        for row in range(self.room_table.rowCount()):
            combo    = self.room_table.cellWidget(row, 4)
            ac_wgt   = self.room_table.cellWidget(row, 5)
            ac_cb    = ac_wgt.findChild(QCheckBox) if ac_wgt else None
            data["rooms"].append({
                "name":      (self.room_table.item(row, 0) or QTableWidgetItem("")).text(),
                "length":    (self.room_table.item(row, 1) or QTableWidgetItem("0")).text(),
                "width":     (self.room_table.item(row, 2) or QTableWidgetItem("0")).text(),
                "height":    (self.room_table.item(row, 3) or QTableWidgetItem("0")).text(),
                "room_type": combo.currentText() if combo else "Other",
                "has_ac":    ac_cb.isChecked() if ac_cb else False,
            })

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        QMessageBox.information(self, "Saved", f"Project saved to:\n{path}")

    def _load_project(self) -> None:
        """Load a previously saved JSON project file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "saved_projects/", "JSON Files (*.json)"
        )
        if not path or not os.path.exists(path):
            return

        with open(path) as f:
            data = json.load(f)

        self._clear_all()

        self.project_name_input .setText(data.get("project_name", ""))
        self.client_name_input  .setText(data.get("client_name", ""))
        btype = data.get("building_type", "Residential")
        idx = self.building_type_combo.findText(btype)
        if idx >= 0:
            self.building_type_combo.setCurrentIndex(idx)

        std = data.get("standards", {})
        self.std_lighting_area .setValue(std.get("lighting_area", 9.0))
        self.std_fan_area      .setValue(std.get("fan_area",      12.0))
        self.std_sockets       .setValue(std.get("sockets",       3))
        self.std_wire_wastage  .setValue(std.get("wire_wastage",  1.3))
        self.std_diversity     .setValue(std.get("diversity",     0.8))

        for room_data in data.get("rooms", []):
            self._add_room_row()
            row = self.room_table.rowCount() - 1
            self.room_table.item(row, 0).setText(room_data.get("name", ""))
            self.room_table.item(row, 1).setText(room_data.get("length", "0"))
            self.room_table.item(row, 2).setText(room_data.get("width", "0"))
            self.room_table.item(row, 3).setText(room_data.get("height", "0"))

            combo = self.room_table.cellWidget(row, 4)
            idx = combo.findText(room_data.get("room_type", "Other"))
            if idx >= 0:
                combo.setCurrentIndex(idx)

            ac_wgt = self.room_table.cellWidget(row, 5)
            ac_cb  = ac_wgt.findChild(QCheckBox) if ac_wgt else None
            if ac_cb:
                ac_cb.setChecked(room_data.get("has_ac", False))

        QMessageBox.information(self, "Loaded", "Project loaded successfully.")
