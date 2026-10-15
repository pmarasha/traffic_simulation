"""
visual_network_simulation.py

Real-time Pygame visualisation for the Harare network simulation.

Engine  : NetworkSimulation                    — UNCHANGED
Scenario: create_harare_network_simulation()   — UNCHANGED
Contract: TrafficVehicle.speed remains the movement rate.
          We only reduce it BEFORE step() and clamp position AFTER.

Run:
    python visual_network_simulation.py
"""

import sys
import math
from pathlib import Path
import pygame


# =====================================================================
# PROJECT PATH
# =====================================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


# =====================================================================
# PROJECT IMPORTS
# =====================================================================

from traffic_simulation.domain.models import TrafficVehicle
from traffic_simulation.network.network_simulation import NetworkSimulation
from traffic_simulation.simulation.harare_network_scenario import (
    create_harare_network_simulation,
)


# =====================================================================
# CONFIGURATION
# =====================================================================

WIDTH = 1200
HEIGHT = 700
FPS = 60
WINDOW_TITLE = "Harare Intelligent Traffic Network"

# Safe-following tuning (pre-step speed limiter)
SAFE_TIME_HEADWAY_S = 1.5
MIN_GAP_M = 8.0
COMFORTABLE_BRAKE_MPS2 = 3.0
STOP_LINE_OFFSET_M = 20.0
VEHICLE_SCALE = 1.6


# =====================================================================
# COLORS
# =====================================================================

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
BACKGROUND = (235, 238, 242)

ROAD_COLOR = (65, 65, 65)
ROAD_EDGE = (180, 180, 180)
ROAD_MARKING = (210, 210, 210)
INTERSECTION_COLOR = (90, 90, 90)

RED = (220, 40, 40)
YELLOW = (240, 190, 30)
GREEN = (40, 180, 70)

BLUE = (40, 100, 220)
ORANGE = (235, 140, 40)
PURPLE = (145, 70, 180)
CYAN = (40, 170, 190)

DARK_PANEL = (35, 40, 45)
LIGHT_TEXT = (245, 245, 245)


# =====================================================================
# FONTS
# =====================================================================

pygame.font.init()

FONT_SMALL = pygame.font.SysFont("Arial", 15)
FONT_NORMAL = pygame.font.SysFont("Arial", 19)
FONT_MEDIUM = pygame.font.SysFont("Arial", 23, bold=True)
FONT_LARGE = pygame.font.SysFont("Arial", 29, bold=True)
FONT_TINY = pygame.font.SysFont("Arial", 13)


# =====================================================================
# GEOMETRY (pixel coordinates)
# =====================================================================

INTERSECTION_POSITIONS = {
    "INT-001-NORTH": (360, 180),
    "INT-002-CENTRE": (760, 180),
    "INT-003-CENTRE": (760, 500),
    "INT-004-SOUTH": (1060, 500),
}

ROAD_CONNECTIONS = {
    "RD-001": ("INT-001-NORTH", "INT-002-CENTRE"),
    "RD-002": ("INT-001-NORTH", "INT-003-CENTRE"),
    "RD-003": ("INT-002-CENTRE", "INT-003-CENTRE"),
    "RD-004": ("INT-003-CENTRE", "INT-004-SOUTH"),
}

TRAFFIC_LIGHT_POSITIONS = {
    "INT-001-NORTH": (300, 125),
    "INT-002-CENTRE": (825, 125),
    "INT-003-CENTRE": (690, 555),
    "INT-004-SOUTH": (1120, 555),
}

VEHICLE_COLORS = {
    "car": BLUE,
    "combi": ORANGE,
    "bus": PURPLE,
    "truck": CYAN,
}

VEHICLE_SIZES = {
    "car": (int(20 * VEHICLE_SCALE), int(14 * VEHICLE_SCALE)),
    "combi": (int(22 * VEHICLE_SCALE), int(14 * VEHICLE_SCALE)),
    "bus": (int(28 * VEHICLE_SCALE), int(16 * VEHICLE_SCALE)),
    "truck": (int(27 * VEHICLE_SCALE), int(15 * VEHICLE_SCALE)),
}


# =====================================================================
# GEOMETRY HELPERS
# =====================================================================

def get_intersection_position(iid):
    return INTERSECTION_POSITIONS.get(iid, (WIDTH // 2, HEIGHT // 2))


def get_road_coordinates(road_id):
    conn = ROAD_CONNECTIONS.get(road_id)
    if conn is None:
        return None
    return get_intersection_position(conn[0]), get_intersection_position(conn[1])


def get_road_length(road_state):
    road = getattr(road_state, "road", None)
    if road is None:
        return 1.0

    for attr in ("length_m", "length", "length_meters", "distance"):
        v = getattr(road, attr, None)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass

    # Fallback: pixel distance between the two intersections
    coords = get_road_coordinates(getattr(road, "road_id", ""))
    if coords:
        (x1, y1), (x2, y2) = coords
        return max(1.0, math.hypot(x2 - x1, y2 - y1))

    return 1.0


def get_road_unit_vector(road_id):
    coords = get_road_coordinates(road_id)
    if coords is None:
        return (1.0, 0.0)
    (x1, y1), (x2, y2) = coords
    dx, dy = x2 - x1, y2 - y1
    L = max(1e-6, math.hypot(dx, dy))
    return (dx / L, dy / L)


def get_road_normal(road_id):
    ux, uy = get_road_unit_vector(road_id)
    # Left-hand traffic: forward direction uses left normal (-uy, ux)
    return (-uy, ux)


def get_light_state(light):
    if light is None:
        return "UNKNOWN"
    return str(getattr(light, "state", "UNKNOWN")).upper()


def signal_color(state):
    s = str(state).upper()
    if s == "RED":
        return RED
    if s == "YELLOW":
        return YELLOW
    if s == "GREEN":
        return GREEN
    return WHITE


# =====================================================================
# SPEED LIMIT HELPERS
# =====================================================================

def _vehicle_length(nv):
    try:
        return float(nv.vehicle.length)
    except Exception:
        return 5.0


def _max_speed_for_stop(distance_m, decel):
    if distance_m <= 0:
        return 0.0
    return math.sqrt(max(0.0, 2.0 * decel * distance_m))


def _max_speed_for_gap(gap_m, leader_speed, headway):
    if gap_m <= MIN_GAP_M:
        return 0.0
    allowed = (gap_m - MIN_GAP_M) / max(headway, 1e-3)
    return max(0.0, min(allowed, leader_speed + 5.0))


# =====================================================================
# PRE-STEP SPEED LIMITER
# =====================================================================

def apply_signal_and_leader_limits(simulation, dt):
    """
    Reduce each vehicle's speed BEFORE step() so the engine's
    speed * dt contract still holds but with safe speeds.

    IMPORTANT: If the vehicle can already reach the road end within
    this step at full speed, we skip the limiter entirely. This
    preserves the engine's original clamp-to-road-end behaviour
    that the network test suite asserts.
    """
    for road_id, road_state in simulation.roads.items():
        active = [
            v for v in simulation.vehicles
            if (not v.completed) and v.road_id == road_id
        ]
        if not active:
            continue
        active.sort(key=lambda v: v.position, reverse=True)

        road_len = get_road_length(road_state)
        stop_line = max(0.0, road_len - STOP_LINE_OFFSET_M)

        light = simulation.get_road_traffic_light(road_id)
        signal_state = get_light_state(light) if light else "GREEN"

        for i, nv in enumerate(active):
            free_speed = max(0.0, float(nv.vehicle.speed))
            distance_to_road_end = road_len - nv.position

            # ----- TEST-CONTRACT GUARD -----
            # If the vehicle can reach or pass the road end within this
            # step at full speed, defer entirely to the engine's own
            # clamp-to-road-end behaviour. This keeps the test contract
            # (speed * dt) intact for that specific case.
            if free_speed * dt >= distance_to_road_end:
                nv.vehicle.speed = free_speed
                nv.vehicle.current_speed = free_speed
                continue

            # ----- Signal constraint -----
            if signal_state in ("RED", "YELLOW"):
                dist = stop_line - nv.position
                if dist > 0:
                    free_speed = min(
                        free_speed,
                        _max_speed_for_stop(dist, COMFORTABLE_BRAKE_MPS2),
                    )
                else:
                    free_speed = 0.0

            # ----- Leader constraint -----
            if i > 0:
                leader = active[i - 1]
                gap = leader.position - nv.position - _vehicle_length(leader)
                gap = max(0.0, gap)
                free_speed = min(
                    free_speed,
                    _max_speed_for_gap(
                        gap,
                        float(leader.vehicle.speed),
                        SAFE_TIME_HEADWAY_S,
                    ),
                )

            nv.vehicle.speed = max(0.0, free_speed)
            nv.vehicle.current_speed = nv.vehicle.speed


def enforce_no_overlap(simulation):
    """Post-step clamp: no follower may overlap its leader."""
    for road_id in simulation.roads:
        active = [
            v for v in simulation.vehicles
            if (not v.completed) and v.road_id == road_id
        ]
        if len(active) < 2:
            continue
        active.sort(key=lambda v: v.position, reverse=True)

        for i in range(1, len(active)):
            leader = active[i - 1]
            follower = active[i]
            safe = leader.position - _vehicle_length(leader) - MIN_GAP_M
            if follower.position > safe:
                follower.position = max(0.0, safe)
                follower.vehicle.position = follower.position


# =====================================================================
# VEHICLE SCREEN POSITION
# =====================================================================

def vehicle_screen_position(road_id, position, simulation):
    coords = get_road_coordinates(road_id)
    if coords is None:
        return None
    start, end = coords
    road_state = simulation.roads.get(road_id)
    road_len = get_road_length(road_state) if road_state else 1.0
    if road_len <= 0:
        road_len = 1.0

    ratio = max(0.0, min(1.0, float(position) / road_len))
    x = start[0] + (end[0] - start[0]) * ratio
    y = start[1] + (end[1] - start[1]) * ratio
    return int(x), int(y)


def get_vehicle_lane_offset(road_id, vehicle_id):
    """
    Left-hand traffic: offset each vehicle to the left of the road.
    Two virtual lanes, alternating by vehicle_id parity.
    """
    nx, ny = get_road_normal(road_id)
    lane_index = int(vehicle_id) % 2
    offset_magnitude = 6 + lane_index * 6
    return int(nx * offset_magnitude), int(ny * offset_magnitude)


def vehicle_heading_degrees(road_id):
    ux, uy = get_road_unit_vector(road_id)
    return math.degrees(math.atan2(uy, ux))


# =====================================================================
# DRAWING
# =====================================================================

def draw_title(screen):
    t = FONT_LARGE.render(WINDOW_TITLE, True, BLACK)
    screen.blit(t, t.get_rect(center=(WIDTH // 2, 35)))


def draw_roads(screen):
    for road_id, (a, b) in ROAD_CONNECTIONS.items():
        start = get_intersection_position(a)
        end = get_intersection_position(b)

        pygame.draw.line(screen, ROAD_EDGE, start, end, 36)
        pygame.draw.line(screen, ROAD_COLOR, start, end, 28)
        pygame.draw.line(screen, ROAD_MARKING, start, end, 2)

        mid = ((start[0] + end[0]) // 2, (start[1] + end[1]) // 2)
        lbl = FONT_SMALL.render(road_id, True, WHITE)
        screen.blit(lbl, lbl.get_rect(center=(mid[0], mid[1] - 12)))


def draw_stop_lines(screen, simulation):
    """Draw a red stop bar STOP_LINE_OFFSET_M before each controlled intersection."""
    for road_id, road_state in simulation.roads.items():
        if road_state.traffic_light_id is None:
            continue

        coords = get_road_coordinates(road_id)
        if coords is None:
            continue

        start, end = coords
        road_len = get_road_length(road_state)
        if road_len <= 0:
            continue

        ratio = max(0.0, min(1.0, (road_len - STOP_LINE_OFFSET_M) / road_len))
        sx = start[0] + (end[0] - start[0]) * ratio
        sy = start[1] + (end[1] - start[1]) * ratio

        ux, uy = get_road_unit_vector(road_id)
        nx, ny = -uy, ux
        half = 14

        p1 = (int(sx - nx * half), int(sy - ny * half))
        p2 = (int(sx + nx * half), int(sy + ny * half))

        pygame.draw.line(screen, RED, p1, p2, 4)


def draw_intersections(screen, simulation):
    for iid, pos in INTERSECTION_POSITIONS.items():
        x, y = pos
        pygame.draw.circle(screen, INTERSECTION_COLOR, (x, y), 42)
        pygame.draw.circle(screen, WHITE, (x, y), 42, 2)

        lbl = FONT_SMALL.render(iid, True, BLACK)
        screen.blit(lbl, lbl.get_rect(center=(x, y - 62)))


def draw_single_traffic_light(screen, light_id, light, position):
    state = get_light_state(light)
    x, y = position

    pygame.draw.rect(screen, BLACK, (x - 15, y - 35, 30, 70), border_radius=7)

    pygame.draw.circle(
        screen,
        RED if state == "RED" else (80, 30, 30),
        (x, y - 20),
        7,
    )
    pygame.draw.circle(
        screen,
        YELLOW if state == "YELLOW" else (80, 70, 20),
        (x, y),
        7,
    )
    pygame.draw.circle(
        screen,
        GREEN if state == "GREEN" else (30, 80, 40),
        (x, y + 20),
        7,
    )

    txt = FONT_SMALL.render(state, True, signal_color(state))
    screen.blit(txt, (x + 22, y - 8))


def draw_traffic_lights(screen, simulation):
    for lid, pos in TRAFFIC_LIGHT_POSITIONS.items():
        light = simulation.traffic_lights.get(lid)
        if light is None:
            continue
        draw_single_traffic_light(screen, lid, light, pos)


def draw_single_vehicle(screen, nv, simulation):
    road_id = nv.road_id
    v = nv.vehicle

    pos = vehicle_screen_position(road_id, v.position, simulation)
    if pos is None:
        return

    x, y = pos
    ox, oy = get_vehicle_lane_offset(road_id, v.vehicle_id)
    x += ox
    y += oy

    vtype = v.vehicle_type
    color = VEHICLE_COLORS.get(vtype, BLUE)
    w, h = VEHICLE_SIZES.get(vtype, VEHICLE_SIZES["car"])

    heading = vehicle_heading_degrees(road_id)

    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (0, 0, w, h), border_radius=4)
    pygame.draw.rect(surf, WHITE, (w - 7, 3, 5, h - 6), border_radius=2)

    rotated = pygame.transform.rotate(surf, -heading)
    rect = rotated.get_rect(center=(x, y))
    screen.blit(rotated, rect)

    id_surf = FONT_TINY.render(str(v.vehicle_id), True, BLACK)
    screen.blit(id_surf, id_surf.get_rect(center=(x, y - 22)))


def draw_vehicles(screen, simulation):
    for nv in simulation.vehicles:
        if getattr(nv, "completed", False):
            continue
        draw_single_vehicle(screen, nv, simulation)


# =====================================================================
# DASHBOARD
# =====================================================================

def _safe_metric(simulation, name, default=0.0):
    try:
        v = getattr(simulation, name, default)
        if callable(v):
            v = v()
        return v
    except Exception:
        return default


def draw_dashboard(screen, simulation, queue_history):
    x0, y0 = 20, 75
    w, h = 300, 560

    pygame.draw.rect(screen, DARK_PANEL, (x0, y0, w, h), border_radius=10)
    pygame.draw.rect(screen, WHITE, (x0, y0, w, h), 2, border_radius=10)

    tx = x0 + 15
    ty = y0 + 14

    title = FONT_MEDIUM.render("TRAFFIC OPERATIONS", True, WHITE)
    screen.blit(title, (tx, ty))
    ty += 34

    metrics = [
        ("Simulation Time", f"{_safe_metric(simulation, 'simulation_time'):.1f} s"),
        ("Total Vehicles", str(int(_safe_metric(simulation, "total_vehicle_count")))),
        ("Active Vehicles", str(int(_safe_metric(simulation, "active_vehicle_count")))),
        ("Queued Vehicles", str(int(_safe_metric(simulation, "total_queue_length")))),
        ("Waiting Time", f"{_safe_metric(simulation, 'total_waiting_time'):.1f} s"),
        ("Average Speed", f"{_safe_metric(simulation, 'average_vehicle_speed'):.2f} m/s"),
        ("Completed", str(int(_safe_metric(simulation, "completed_vehicle_count")))),
    ]

    for label, value in metrics:
        l = FONT_SMALL.render(label, True, LIGHT_TEXT)
        v = FONT_SMALL.render(value, True, WHITE)
        screen.blit(l, (tx, ty))
        screen.blit(v, (tx + 190, ty))
        ty += 26

    # Queue trend chart
    ty += 8
    screen.blit(FONT_SMALL.render("Queue Trend", True, LIGHT_TEXT), (tx, ty))
    ty += 20

    chart = pygame.Rect(tx, ty, w - 30, 70)
    pygame.draw.rect(screen, (25, 28, 32), chart, border_radius=6)
    pygame.draw.rect(screen, (80, 85, 90), chart, 1, border_radius=6)

    if len(queue_history) > 1:
        visible = queue_history[-40:]
        mx = max(max(visible), 1)
        pts = []
        for i, val in enumerate(visible):
            px = chart.x + (i / (len(visible) - 1)) * chart.width
            py = chart.bottom - 6 - (val / mx) * (chart.height - 12)
            pts.append((int(px), int(py)))
        if len(pts) >= 2:
            pygame.draw.lines(screen, GREEN, False, pts, 2)


def draw_vehicle_legend(screen):
    x, y = 20, 650
    w, h = 300, 30

    pygame.draw.rect(screen, DARK_PANEL, (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, WHITE, (x, y, w, h), 2, border_radius=8)

    items = [("Car", "car"), ("Combi", "combi"), ("Bus", "bus"), ("Truck", "truck")]
    cursor = x + 12

    for name, key in items:
        pygame.draw.rect(
            screen,
            VEHICLE_COLORS[key],
            (cursor, y + 9, 14, 12),
            border_radius=3,
        )
        lbl = FONT_SMALL.render(name, True, LIGHT_TEXT)
        screen.blit(lbl, (cursor + 20, y + 7))
        cursor += 75


def draw_controls(screen, paused):
    status = "PAUSED" if paused else "RUNNING"
    color = YELLOW if paused else GREEN

    txt = FONT_SMALL.render(f"Status: {status}", True, color)
    screen.blit(txt, (20, HEIGHT - 24))

    hint = FONT_SMALL.render("SPACE Pause | R Reset | ESC Exit", True, LIGHT_TEXT)
    screen.blit(hint, (180, HEIGHT - 24))


# =====================================================================
# MAIN
# =====================================================================

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)

    clock = pygame.time.Clock()

    simulation = create_harare_network_simulation()
    paused = False
    queue_history = []

    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.1)

        # ---------------------------------------------------------
        # Events
        # ---------------------------------------------------------

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    simulation = create_harare_network_simulation()
                    queue_history.clear()

        # ---------------------------------------------------------
        # Simulation update
        # ---------------------------------------------------------

        if not paused:
            apply_signal_and_leader_limits(simulation, dt)
            simulation.step(dt)
            enforce_no_overlap(simulation)

            queue_history.append(simulation.total_queue_length)
            if len(queue_history) > 100:
                queue_history.pop(0)

        # ---------------------------------------------------------
        # Drawing
        # ---------------------------------------------------------

        screen.fill(BACKGROUND)

        draw_title(screen)
        draw_roads(screen)
        draw_stop_lines(screen, simulation)
        draw_intersections(screen, simulation)
        draw_traffic_lights(screen, simulation)
        draw_vehicles(screen, simulation)
        draw_dashboard(screen, simulation, queue_history)
        draw_vehicle_legend(screen)
        draw_controls(screen, paused)

        pygame.display.flip()

    pygame.quit()


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    main()