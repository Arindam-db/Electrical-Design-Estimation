"""
calculations/load_calc.py
Core electrical load calculations for each room.

Formulas used:
  area           = length × width
  lights         = max(1, ceil(area / lighting_area_per_light))
  fans           = max(1, ceil(area / fan_area_per_fan))
  sockets        = intelligent rule based on light count
  ac_point       = 1 if room has AC else 0
  connected_load = (lights × LIGHT_W) + (fans × FAN_W)
                   + (sockets × SOCKET_W) + (ac_point × AC_W)
"""

from dataclasses import dataclass
from math import ceil


# ─────────────────────────────────────────────
#  Wattage constants — edit here to update everywhere
# ─────────────────────────────────────────────
LIGHT_W  = 12    # Watts per light point (LED)
FAN_W    = 75    # Watts per ceiling fan
SOCKET_W = 100   # Watts per socket (assumed load)
AC_W     = 1500  # Watts per AC unit (1.5-ton typical)


# ─────────────────────────────────────────────
#  Room-type default overrides
#  Extend each entry with room-specific rules in the future.
#  Example future use:
#    "Bathroom": {"min_fans": 0, "exhaust_fan": True}
#    "Kitchen":  {"min_sockets": 4}
# ─────────────────────────────────────────────
ROOM_TYPE_DEFAULTS: dict[str, dict] = {
    "Bedroom":    {},
    "Hall":       {},
    "Kitchen":    {},
    "Bathroom":   {},
    "Store Room": {},
    "Office":     {},
}


@dataclass
class RoomInput:
    """All user-supplied data for a single room."""
    name:      str
    length:    float   # metres
    width:     float   # metres
    height:    float   # metres  — kept for future vertical wire calculations
    room_type: str
    has_ac:    bool


@dataclass
class RoomResult:
    """Calculated electrical quantities for a single room."""
    name:             str
    length:           float
    width:            float
    area:             float
    lights:           int
    fans:             int
    sockets:          int
    ac_point:         int
    connected_load_w: int   # Watts


def _calc_sockets(lights: int) -> int:
    """
    Determine socket count from light count.
    Isolated here so room-specific rules can be inserted later.

    Rule:
        lights <= 2  →  2 sockets  (small room)
        lights <= 4  →  3 sockets  (medium room)
        lights  > 4  →  4 sockets  (large room)
    """
    if lights <= 2:
        return 2
    elif lights <= 4:
        return 3
    else:
        return 4


def calculate_room(
    room: RoomInput,
    lighting_area_per_light: float,
    fan_area_per_fan: float,
    sockets_per_room: int,          # kept in signature for API compatibility
) -> RoomResult:
    """
    Compute electrical quantities for one room.

    Parameters
    ----------
    room                    : RoomInput dataclass
    lighting_area_per_light : m² served by one light fitting
    fan_area_per_fan        : m² served by one ceiling fan
    sockets_per_room        : legacy parameter (retained for compatibility,
                              not used — socket count is now derived from lights)

    Note: room.height is preserved for future wire-length calculations
    (e.g. vertical drops from ceiling to switch boards).
    """
    area   = room.length * room.width

    # Guarantee at least one fixture per room regardless of area
    lights = max(1, ceil(area / lighting_area_per_light))
    fans   = max(1, ceil(area / fan_area_per_fan))

    # Intelligent socket count — isolated in _calc_sockets()
    sockets = _calc_sockets(lights)

    ac_pt  = 1 if room.has_ac else 0

    # Future use: room.height can be used for vertical wire estimation
    # e.g. vertical_drop_m = room.height * (lights + fans + sockets)

    load = (
        lights  * LIGHT_W
        + fans  * FAN_W
        + sockets * SOCKET_W
        + ac_pt  * AC_W
    )

    return RoomResult(
        name             = room.name,
        length           = room.length,
        width            = room.width,
        area             = area,
        lights           = lights,
        fans             = fans,
        sockets          = sockets,
        ac_point         = ac_pt,
        connected_load_w = load,
    )


def calculate_room_loads(
    rooms: list[RoomInput],
    lighting_area_per_light: float,
    fan_area_per_fan: float,
    sockets_per_room: int,
) -> list[RoomResult]:
    """Run calculate_room() for every room in the list."""
    return [
        calculate_room(r, lighting_area_per_light, fan_area_per_fan, sockets_per_room)
        for r in rooms
    ]
