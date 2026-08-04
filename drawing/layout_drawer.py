"""
drawing/layout_drawer.py
Generates a top-view floor-plan sketch using matplotlib embedded in PyQt6.

Rooms wrap into multiple rows when their combined width exceeds MAX_ROW_WIDTH.
Each room shows symbols placed on a proportional grid using numpy.linspace so
positions scale correctly when rooms are resized.

Symbol counts come ONLY from RoomResult — no recalculation is done here.
The results table is the single source of truth.
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING

import numpy as np

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox

# matplotlib Qt backend
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches

if TYPE_CHECKING:
    from calculations.load_calc import RoomResult


# ─────────────────────────────────────────────
#  Visual config
# ─────────────────────────────────────────────
ROOM_FILL    = "#f0f4ff"
ROOM_EDGE    = "#2c3e50"
LIGHT_COLOR  = "#f1c40f"   # yellow
FAN_COLOR    = "#3498db"   # blue
SOCKET_COLOR = "#27ae60"   # green
AC_COLOR     = "#e74c3c"   # red

GAP_H        = 0.5   # horizontal gap between rooms (metres)
GAP_V        = 1.2   # vertical gap between rows (metres, room label space)
MAX_ROW_WIDTH = 20.0  # metres — wrap to new row beyond this


class LayoutDrawer(QWidget):
    """
    PyQt6 widget that embeds a matplotlib figure for drawing floor plans.
    Consumes RoomResult objects — never recalculates.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.figure = Figure(tight_layout=True)
        self.canvas = FigureCanvas(self.figure)

        # Export buttons (Change 7)
        self._btn_png = QPushButton("Export PNG")
        self._btn_svg = QPushButton("Export SVG")
        self._btn_png.clicked.connect(lambda: self._export("png"))
        self._btn_svg.clicked.connect(lambda: self._export("svg"))
        self._btn_png.setEnabled(False)
        self._btn_svg.setEnabled(False)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._btn_png)
        btn_row.addWidget(self._btn_svg)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas, stretch=1)
        layout.addLayout(btn_row)

        self._draw_placeholder()

    # ──────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────

    def draw_layout(self, results: list[RoomResult]) -> None:
        """
        Render top-view room layout from pre-calculated RoomResult objects.
        No calculations are performed here — all values come from results.
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_aspect("equal")
        ax.set_facecolor("#ecf0f1")
        ax.set_title("Top-View Floor Layout (Schematic)", fontsize=10)

        # ── Multi-row layout (Change 6) ──────────
        x_cursor  = 0.0
        y_cursor  = 0.0   # bottom of current row
        row_max_h = 0.0   # tallest room in current row

        for room in results:
            # Wrap to new row if this room would exceed max width
            if x_cursor > 0 and x_cursor + room.width > MAX_ROW_WIDTH:
                y_cursor  += row_max_h + GAP_V
                x_cursor   = 0.0
                row_max_h  = 0.0

            self._draw_room(ax, room, x_cursor, y_cursor)
            row_max_h  = max(row_max_h, room.length)
            x_cursor  += room.width + GAP_H

        # Axis limits
        total_w   = MAX_ROW_WIDTH + GAP_H
        total_h   = y_cursor + row_max_h + GAP_V
        ax.set_xlim(-0.5, total_w)
        ax.set_ylim(-0.5, total_h)

        # ── Improved legend (Change 11) ──────────
        legend_elements = [
            mpatches.Patch(facecolor=LIGHT_COLOR,  label="● Light"),
            mpatches.Patch(facecolor=FAN_COLOR,    label="⊕ Fan"),
            mpatches.Patch(facecolor=SOCKET_COLOR, label="□ Socket"),
            mpatches.Patch(facecolor=AC_COLOR,     label="★ AC Point"),
        ]
        ax.legend(
            handles=legend_elements,
            loc="upper right",
            fontsize=8,
            framealpha=0.9,
            title="Symbols",
            title_fontsize=8,
        )

        ax.set_xlabel("Width (m)")
        ax.set_ylabel("Length (m)")
        ax.grid(True, linestyle="--", alpha=0.3)

        self.canvas.draw()
        self._btn_png.setEnabled(True)
        self._btn_svg.setEnabled(True)

    def clear(self) -> None:
        """Reset to the placeholder state."""
        self._btn_png.setEnabled(False)
        self._btn_svg.setEnabled(False)
        self._draw_placeholder()

    # ──────────────────────────────────────────
    #  Export (Change 7)
    # ──────────────────────────────────────────

    def _export(self, fmt: str) -> None:
        """Save the current figure as PNG or SVG chosen by the user."""
        filter_str = "PNG Image (*.png)" if fmt == "png" else "SVG Vector (*.svg)"
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {fmt.upper()}", f"floor_plan.{fmt}", filter_str
        )
        if not path:
            return
        try:
            self.figure.savefig(path, dpi=150, bbox_inches="tight")
            QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    # ──────────────────────────────────────────
    #  Internal helpers
    # ──────────────────────────────────────────

    def _draw_placeholder(self) -> None:
        """Show an empty canvas with instructions."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#ecf0f1")
        ax.text(
            0.5, 0.5,
            "Add rooms, click '⚡ Calculate',\nthen '🗺  Generate Layout'",
            ha="center", va="center",
            fontsize=12, color="#7f8c8d",
            transform=ax.transAxes,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()

    def _draw_room(
        self,
        ax,
        room: RoomResult,
        x_start: float,
        y_start: float,
    ) -> None:
        """
        Draw one room rectangle and place symbols inside it.
        All counts come directly from room (RoomResult) — no recalculation.
        """
        w = room.width    # x-axis
        h = room.length   # y-axis

        # Room rectangle
        rect = mpatches.FancyBboxPatch(
            (x_start, y_start), w, h,
            boxstyle="square,pad=0.0",
            linewidth=1.5,
            edgecolor=ROOM_EDGE,
            facecolor=ROOM_FILL,
        )
        ax.add_patch(rect)

        # Room label above the room
        ax.text(
            x_start + w / 2, y_start + h + 0.15,
            f"{room.name}\n{room.length:.1f}×{room.width:.1f} m",
            ha="center", va="bottom", fontsize=7, color=ROOM_EDGE,
        )

        # ── Symbols from pre-calculated counts (Change 3) ──
        # Place lights (upper two-thirds of room)
        self._place_symbols(
            ax, x_start, y_start + h * 0.35, w, h * 0.55,
            room.lights, "●", LIGHT_COLOR,
        )

        # Place fans (lower two-thirds of room, offset from lights)
        self._place_symbols(
            ax, x_start, y_start + h * 0.05, w, h * 0.55,
            room.fans, "⊕", FAN_COLOR,
        )

        # Place sockets along bottom edge (Change 4 & 5)
        self._place_sockets(ax, x_start, y_start, w, room.sockets)

        # AC symbol top-right corner
        if room.ac_point:
            ax.text(
                x_start + w - 0.25, y_start + h - 0.25,
                "★", ha="center", va="center",
                fontsize=12, color=AC_COLOR,
            )

    @staticmethod
    def _place_symbols(
        ax,
        x_start: float,
        y_start: float,
        w: float,
        h: float,
        count: int,
        symbol: str,
        color: str,
    ) -> None:
        """
        Distribute `count` symbols evenly inside a sub-area of the room.
        Uses numpy.linspace for proportional, resize-safe positioning (Change 5).
        Grid shape computed with sqrt to avoid clustering (Change 4).
        """
        if count <= 0:
            return

        rows = max(1, math.ceil(math.sqrt(count)))
        cols = math.ceil(count / rows)

        # Positions span 20%–80% of the allotted sub-area (Change 5)
        xs = np.linspace(x_start + 0.2 * w, x_start + 0.8 * w, cols)
        ys = np.linspace(y_start + 0.15 * h, y_start + 0.85 * h, rows)

        placed = 0
        for y in ys:
            for x in xs:
                if placed >= count:
                    break
                ax.text(x, y, symbol, ha="center", va="center",
                        fontsize=9, color=color)
                placed += 1

    @staticmethod
    def _place_sockets(
        ax,
        x_start: float,
        y_start: float,
        w: float,
        count: int,
    ) -> None:
        """
        Place socket squares along the bottom wall using linspace (Change 5).
        Count comes from RoomResult.sockets — no recalculation.
        """
        if count <= 0:
            return
        xs = np.linspace(x_start + 0.15 * w, x_start + 0.85 * w, count)
        for x in xs:
            ax.text(x, y_start + 0.12, "□", ha="center", va="center",
                    fontsize=9, color=SOCKET_COLOR)
