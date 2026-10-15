"""
macro_model.py

Simplified 4-step national transport model for Zimbabwe.
Supports scenario overrides via optional parameters.

Steps:
    1. Trip generation       (production per zone)
    2. Trip distribution     (gravity model)
    3. (Mode choice)         omitted — road-only demo
    4. Trip assignment       (direct-link, single path)
    5. Link performance      (BPR volume-delay function)

Run standalone:
    python macro_model.py
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


# =====================================================================
# CALIBRATION CONSTANTS  (defaults — can be overridden at call time)
# =====================================================================

TRIP_RATE_PER_CAPITA = 5.0     # long-distance trips per person per year
GRAVITY_BETA = 1.5             # distance-decay parameter
GRAVITY_SCALE_KM = 500.0       # impedance scale
PEAK_HOUR_FACTOR = 0.10        # share of daily flow in the peak hour
BPR_ALPHA = 0.15               # BPR coefficient
BPR_BETA = 4.0                 # BPR exponent
BPR_VC_CEILING = 1.3           # BPR validity ceiling


# =====================================================================
# 1. ZONES — ten provinces
# =====================================================================

@dataclass
class Zone:
    zone_id: str
    name: str
    population: int
    employment: int
    lat: float
    lon: float


ZONES: Dict[str, Zone] = {
    "ZW-HA": Zone("ZW-HA", "Harare Metropolitan",     2_427_000, 950_000, -17.83, 31.05),
    "ZW-BY": Zone("ZW-BY", "Bulawayo Metropolitan",     665_000, 210_000, -20.15, 28.58),
    "ZW-MA": Zone("ZW-MA", "Manicaland",              1_880_000, 240_000, -18.97, 32.67),
    "ZW-MC": Zone("ZW-MC", "Mashonaland Central",     1_220_000, 130_000, -16.75, 31.07),
    "ZW-ME": Zone("ZW-ME", "Mashonaland East",        1_410_000, 160_000, -18.17, 31.55),
    "ZW-MW": Zone("ZW-MW", "Mashonaland West",        1_730_000, 210_000, -17.72, 29.91),
    "ZW-MV": Zone("ZW-MV", "Masvingo",                1_640_000, 150_000, -20.07, 30.83),
    "ZW-MN": Zone("ZW-MN", "Matabeleland North",        800_000,  90_000, -18.90, 27.20),
    "ZW-MS": Zone("ZW-MS", "Matabeleland South",        750_000,  80_000, -21.00, 29.00),
    "ZW-MI": Zone("ZW-MI", "Midlands",                1_820_000, 180_000, -19.45, 29.82),
}


# =====================================================================
# 2. NETWORK — key national corridors
# =====================================================================

@dataclass
class Link:
    link_id: str
    from_zone: str
    to_zone: str
    length_km: float
    free_flow_speed_kmh: float
    capacity_veh_per_hr: float
    road_class: str


LINKS: List[Link] = [
    Link("A1-HA-BY",  "ZW-HA", "ZW-BY", 439, 100, 1800, "A1"),
    Link("A2-HA-MA",  "ZW-HA", "ZW-MA", 263,  90, 1500, "A2"),
    Link("A3-HA-MC",  "ZW-HA", "ZW-MC",  85,  80, 1200, "A3"),
    Link("A4-HA-ME",  "ZW-HA", "ZW-ME",  75,  80, 1200, "A4"),
    Link("A5-HA-MW",  "ZW-HA", "ZW-MW", 160,  90, 1400, "A5"),
    Link("A1H-HA-MV", "ZW-HA", "ZW-MV", 290,  90, 1400, "A1"),
    Link("A6-BY-MN",  "ZW-BY", "ZW-MN", 180,  80, 1000, "A6"),
    Link("A7-BY-MS",  "ZW-BY", "ZW-MS", 300,  85, 1100, "A7"),
    Link("A5H-BY-MI", "ZW-BY", "ZW-MI", 200,  90, 1300, "A5"),
    Link("A2H-MA-MI", "ZW-MA", "ZW-MI", 300,  80, 1100, "A2"),
    Link("A3H-MC-MW", "ZW-MC", "ZW-MW", 200,  75, 1000, "A3"),
    Link("A4H-ME-MV", "ZW-ME", "ZW-MV", 250,  80, 1100, "A4"),
]


# =====================================================================
# 3. HELPERS
# =====================================================================

def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


# =====================================================================
# 4. STEP 1 — TRIP GENERATION
# =====================================================================

def trip_generation(zones, trip_rate):
    return {zid: z.population * trip_rate / 365.0 for zid, z in zones.items()}


# =====================================================================
# 5. STEP 2 — TRIP DISTRIBUTION
# =====================================================================

def trip_distribution(zones, productions, gravity_beta):
    attractions = {zid: z.employment for zid, z in zones.items()}
    matrix = {}
    for i, zi in zones.items():
        impedance = {}
        denom = 0.0
        for j, zj in zones.items():
            if i == j:
                continue
            d = _haversine_km(zi.lat, zi.lon, zj.lat, zj.lon)
            f = math.exp(-gravity_beta * d / GRAVITY_SCALE_KM)
            imp = attractions[j] * f
            impedance[j] = imp
            denom += imp
        if denom <= 0:
            continue
        for j, val in impedance.items():
            matrix[(i, j)] = productions[i] * val / denom
    return matrix


# =====================================================================
# 6. STEP 4 — TRIP ASSIGNMENT
# =====================================================================

def trip_assignment(matrix, links):
    flow = {l.link_id: 0.0 for l in links}
    for (i, j), trips in matrix.items():
        for l in links:
            if (l.from_zone == i and l.to_zone == j) or \
               (l.from_zone == j and l.to_zone == i):
                flow[l.link_id] += trips
                break
    return flow


# =====================================================================
# 7. STEP 5 — LINK PERFORMANCE
# =====================================================================

def link_performance(link, flow_veh_per_day, peak_hour_factor):
    peak_hour_flow = flow_veh_per_day * peak_hour_factor
    vc_raw = peak_hour_flow / link.capacity_veh_per_hr
    vc_for_delay = min(vc_raw, BPR_VC_CEILING)
    travel_time_free = (link.length_km / link.free_flow_speed_kmh) * 60.0
    travel_time = travel_time_free * (1 + BPR_ALPHA * (vc_for_delay ** BPR_BETA))
    return {
        "link_id": link.link_id,
        "from_zone": link.from_zone,
        "to_zone": link.to_zone,
        "road_class": link.road_class,
        "length_km": link.length_km,
        "flow_veh_per_day": round(flow_veh_per_day, 0),
        "peak_hour_flow": round(peak_hour_flow, 0),
        "capacity_veh_per_hr": link.capacity_veh_per_hr,
        "vc_ratio": round(vc_raw, 3),
        "free_flow_min": round(travel_time_free, 1),
        "travel_time_min": round(travel_time, 1),
        "delay_min": round(travel_time - travel_time_free, 1),
        "status": (
            "OK"            if vc_raw < 0.70 else
            "NEAR-CAPACITY" if vc_raw < 0.90 else
            "OVERLOADED"
        ),
    }


# =====================================================================
# 8. TOP-LEVEL RUN  (accepts scenario overrides)
# =====================================================================

def run_macro_model(trip_multiplier: float = 1.0,
                    peak_hour_factor: Optional[float] = None,
                    gravity_beta: Optional[float] = None) -> dict:
    """
    Execute the full 4-step model.

    trip_multiplier   : 1.0 = baseline. 1.5 = 150% of baseline demand.
                        Applies to the per-capita trip rate.
    peak_hour_factor  : fraction of daily flow in the peak hour.
                        None = use default (0.10).
    gravity_beta      : distance-decay parameter. None = use default.
    """
    trip_rate = TRIP_RATE_PER_CAPITA * trip_multiplier
    phf = peak_hour_factor if peak_hour_factor is not None else PEAK_HOUR_FACTOR
    gb  = gravity_beta      if gravity_beta      is not None else GRAVITY_BETA

    productions = trip_generation(ZONES, trip_rate)
    matrix = trip_distribution(ZONES, productions, gb)
    flows = trip_assignment(matrix, LINKS)
    performance = [link_performance(l, flows[l.link_id], phf) for l in LINKS]

    total_daily = sum(productions.values())
    overloaded = [p for p in performance if p["vc_ratio"] >= 0.90]
    near_cap = [p for p in performance if 0.70 <= p["vc_ratio"] < 0.90]
    max_vc = max((p["vc_ratio"] for p in performance), default=0.0)
    total_delay = sum(p["delay_min"] for p in performance)

    return {
        "zones": {
            zid: {"name": z.name, "population": z.population,
                  "employment": z.employment}
            for zid, z in ZONES.items()
        },
        "links": performance,
        "summary": {
            "num_zones": len(ZONES),
            "num_links": len(LINKS),
            "total_daily_trips": round(total_daily, 0),
            "overloaded_count": len(overloaded),
            "near_capacity_count": len(near_cap),
            "max_vc_ratio": round(max_vc, 3),
            "total_delay_min": round(total_delay, 1),
        },
        "parameters": {
            "trip_rate_per_capita": round(trip_rate, 2),
            "trip_multiplier": trip_multiplier,
            "gravity_beta": gb,
            "peak_hour_factor": phf,
            "bpr_alpha": BPR_ALPHA,
            "bpr_beta": BPR_BETA,
            "bpr_vc_ceiling": BPR_VC_CEILING,
        },
    }


# =====================================================================
# CLI
# =====================================================================

def _print_report(result):
    s = result["summary"]
    print("=" * 72)
    print("  NATIONAL TRANSPORT MACRO MODEL — Zimbabwe")
    print("=" * 72)
    print(f"  Zones modelled          : {s['num_zones']}")
    print(f"  Corridors modelled      : {s['num_links']}")
    print(f"  Total daily trips       : {int(s['total_daily_trips']):,}")
    print(f"  Overloaded links (>=0.9): {s['overloaded_count']}")
    print(f"  Near-capacity (0.7-0.9) : {s['near_capacity_count']}")
    print(f"  Maximum V/C ratio       : {s['max_vc_ratio']}")
    print(f"  Total corridor delay    : {s['total_delay_min']} min")
    print("-" * 72)
    print(f"  {'Link':12s}  {'Flow/day':>9s}  {'Peak/hr':>8s}  "
          f"{'V/C':>5s}  {'Delay':>6s}  Status")
    print("-" * 72)
    for link in result["links"]:
        flag = " ***" if link["vc_ratio"] >= 0.90 else ""
        print(f"  {link['link_id']:12s}  "
              f"{int(link['flow_veh_per_day']):>9,}  "
              f"{int(link['peak_hour_flow']):>8,}  "
              f"{link['vc_ratio']:>5.2f}  "
              f"{link['delay_min']:>5.1f}m  "
              f"{link['status']}{flag}")
    print("=" * 72)


if __name__ == "__main__":
    _print_report(run_macro_model())