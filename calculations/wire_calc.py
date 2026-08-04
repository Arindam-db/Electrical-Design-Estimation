"""
calculations/wire_calc.py
Wire length estimation.

Current approach (placeholder — easy to refine):
  estimated_wire_length = total_room_perimeter × wire_wastage_factor

The wastage factor accounts for:
  - Vertical drops from ceiling/floor to fixtures
  - Routing around doors and windows
  - Loop connections and junction boxes
  - General slack / contractor margins

Replace or extend the formula here without touching the UI.
"""


def estimate_wire_length(
    total_perimeter_m: float,
    wastage_factor: float = 1.3,
) -> float:
    """
    Estimate total wire run length in metres.

    Parameters
    ----------
    total_perimeter_m : sum of (2*(length+width)) for all rooms
    wastage_factor    : multiplier > 1.0 for routing and slack

    Returns
    -------
    Estimated wire length in metres.
    """
    if total_perimeter_m <= 0 or wastage_factor <= 0:
        return 0.0

    return total_perimeter_m * wastage_factor
