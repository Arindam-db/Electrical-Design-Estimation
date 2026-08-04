"""
calculations/material_calc.py
Basic material cost estimation.

All unit prices are in Indian Rupees (₹).
Edit  data/material_costs.json  to update prices — no code changes needed.

This is intentionally simple — a full BOM (Bill of Materials)
system with database-backed pricing can be added later.
"""

import json
import os

# Path to the external costs file (relative to this module)
_COSTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "material_costs.json"
)

# ─────────────────────────────────────────────
#  Fallback defaults used if the JSON file is missing or malformed
# ─────────────────────────────────────────────
_FALLBACK_COSTS: dict[str, float] = {
    "light_fitting":  350.0,
    "fan":            1500.0,
    "socket_outlet":  200.0,
    "ac_point":       800.0,
    "wire_per_metre":  25.0,
    "conduit_factor":   0.15,
    "labour_factor":    0.20,
}


def _load_unit_costs() -> dict[str, float]:
    """
    Load unit costs from data/material_costs.json.
    Falls back to hardcoded defaults if the file is unavailable.
    """
    try:
        with open(_COSTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # Strip the comment key if present
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_FALLBACK_COSTS)


def estimate_cost(
    total_lights:  int,
    total_fans:    int,
    total_sockets: int,
    total_ac:      int,
    wire_length_m: float,
) -> float:
    """
    Compute a rough total material + labour estimate in ₹.

    Parameters
    ----------
    total_lights  : number of light points
    total_fans    : number of ceiling fans
    total_sockets : number of socket outlets
    total_ac      : number of AC points
    wire_length_m : estimated wire run in metres

    Returns
    -------
    Estimated cost in ₹.
    """
    uc = _load_unit_costs()

    material = (
        total_lights  * uc["light_fitting"]
        + total_fans  * uc["fan"]
        + total_sockets * uc["socket_outlet"]
        + total_ac    * uc["ac_point"]
        + wire_length_m * uc["wire_per_metre"]
    )

    # Add conduit/accessories and labour as percentage of material
    total = material * (1 + uc["conduit_factor"] + uc["labour_factor"])
    return round(total, 2)
