import pygame

from traffic_simulation.simulation.engine import SimulationEngine
from traffic_simulation.simulation.harare_scenario import (
    create_harare_traffic_system,
)
from traffic_simulation.simulation.metrics_service import MetricsService


# ============================================================
# CONFIGURATION
# ============================================================

WIDTH = 1152
HEIGHT = 720
FPS = 60

ROAD_WIDTH = 140

VEHICLE_WIDTH = 38
VEHICLE_HEIGHT = 20

# Base interval (in real seconds) between engine steps.
# The engine runs at FPS * speed_multiplier steps per second.
SIMULATION_SPEED = 0.05

# 1.0 = "designed" speed; 0.5 = half; 0.25 = quarter; 2.0 = double.
# Start slow so the traffic evolution is easy to watch.
speed_multiplier = 0.5

# Speed adjustment step (multiply/divide by this on each keypress).
SPEED_STEP = 1.5

# Dashboard
DASHBOARD_X = WIDTH - 322
DASHBOARD_Y = 58
DASHBOARD_WIDTH = 300
DASHBOARD_HEIGHT = 645

# Intersection
INTERSECTION_X = 430
INTERSECTION_Y = HEIGHT // 2


# ============================================================
# COLORS
# ============================================================

BACKGROUND = (34, 120, 69)
ROAD_COLOR = (62, 62, 62)
ROAD_LINE = (235, 235, 235)

WHITE = (245, 245, 245)
LIGHT_TEXT = (180, 180, 180)
DARK_PANEL = (25, 25, 25)
PANEL_BORDER = (75, 75, 75)

GREEN = (30, 210, 75)
YELLOW = (220, 180, 30)
RED = (225, 50, 50)

BLUE = (60, 130, 230)
ORANGE = (245, 145, 35)
PURPLE = (175, 70, 200)


# ============================================================
# INITIALIZATION
# ============================================================

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Harare Smart Traffic Simulation")

clock = pygame.time.Clock()


# Fonts
title_font = pygame.font.SysFont("Arial", 24, bold=True)
heading_font = pygame.font.SysFont("Arial", 18, bold=True)
normal_font = pygame.font.SysFont("Arial", 14)
small_font = pygame.font.SysFont("Arial", 12)
tiny_font = pygame.font.SysFont("Arial", 11)


# ============================================================
# SIMULATION
# ============================================================

system = create_harare_traffic_system()
engine = SimulationEngine(system)

metrics_service = MetricsService()
metrics = metrics_service.collect(system)

paused = False

queue_history = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def vehicle_color(vehicle_type):
    """Return a visual color based on vehicle type."""

    if vehicle_type == "car":
        return BLUE

    if vehicle_type == "combi":
        return ORANGE

    if vehicle_type == "truck":
        return PURPLE

    if vehicle_type == "bus":
        return (50, 170, 170)

    return WHITE


def draw_text(text, font, x, y, color=WHITE):
    """Draw text on the screen."""

    surface = font.render(str(text), True, color)
    screen.blit(surface, (x, y))


def draw_centered_text(text, font, center_x, y, color=WHITE):
    """Draw centered text."""

    surface = font.render(str(text), True, color)

    screen.blit(
        surface,
        (
            center_x - surface.get_width() // 2,
            y,
        ),
    )


def draw_traffic_light(x, y, state, label):
    """Draw a traffic light."""

    # Housing
    housing = pygame.Rect(
        x,
        y,
        42,
        90,
    )

    pygame.draw.rect(
        screen,
        (20, 20, 20),
        housing,
        border_radius=7,
    )

    # Light positions
    positions = [
        (x + 21, y + 17),
        (x + 21, y + 45),
        (x + 21, y + 73),
    ]

    states = [
        ("RED", RED),
        ("YELLOW", YELLOW),
        ("GREEN", GREEN),
    ]

    for index, (light_state, color) in enumerate(states):

        if state == light_state:
            pygame.draw.circle(
                screen,
                color,
                positions[index],
                9,
            )
        else:
            dark_color = tuple(
                max(20, int(value * 0.28))
                for value in color
            )

            pygame.draw.circle(
                screen,
                dark_color,
                positions[index],
                9,
            )

    draw_centered_text(
        label,
        tiny_font,
        x + 21,
        y + 96,
        LIGHT_TEXT,
    )


def draw_roads():
    """Draw the road network."""

    # Horizontal road
    horizontal_rect = pygame.Rect(
        0,
        INTERSECTION_Y - ROAD_WIDTH // 2,
        WIDTH,
        ROAD_WIDTH,
    )

    pygame.draw.rect(
        screen,
        ROAD_COLOR,
        horizontal_rect,
    )

    # Vertical road
    vertical_rect = pygame.Rect(
        INTERSECTION_X - ROAD_WIDTH // 2,
        0,
        ROAD_WIDTH,
        HEIGHT,
    )

    pygame.draw.rect(
        screen,
        ROAD_COLOR,
        vertical_rect,
    )

    # Horizontal lane markings
    lane_y = INTERSECTION_Y

    for x in range(0, WIDTH, 60):

        if (
            x < INTERSECTION_X - ROAD_WIDTH // 2
            or x > INTERSECTION_X + ROAD_WIDTH // 2
        ):

            pygame.draw.rect(
                screen,
                ROAD_LINE,
                (
                    x,
                    lane_y - 2,
                    32,
                    4,
                ),
            )

    # Vertical lane markings
    lane_x = INTERSECTION_X

    for y in range(0, HEIGHT, 60):

        if (
            y < INTERSECTION_Y - ROAD_WIDTH // 2
            or y > INTERSECTION_Y + ROAD_WIDTH // 2
        ):

            pygame.draw.rect(
                screen,
                ROAD_LINE,
                (
                    lane_x - 2,
                    y,
                    4,
                    30,
                ),
            )

    # Stop lines
    stop_offset = ROAD_WIDTH // 2 + 10

    pygame.draw.rect(
        screen,
        WHITE,
        (
            INTERSECTION_X - stop_offset,
            INTERSECTION_Y - ROAD_WIDTH // 2,
            6,
            ROAD_WIDTH,
        ),
    )

    pygame.draw.rect(
        screen,
        WHITE,
        (
            INTERSECTION_X + stop_offset - 6,
            INTERSECTION_Y - ROAD_WIDTH // 2,
            6,
            ROAD_WIDTH,
        ),
    )

    pygame.draw.rect(
        screen,
        WHITE,
        (
            INTERSECTION_X - ROAD_WIDTH // 2,
            INTERSECTION_Y - stop_offset,
            ROAD_WIDTH,
            6,
        ),
    )

    pygame.draw.rect(
        screen,
        WHITE,
        (
            INTERSECTION_X - ROAD_WIDTH // 2,
            INTERSECTION_Y + stop_offset - 6,
            ROAD_WIDTH,
            6,
        ),
    )


def draw_road_labels():
    """Draw names of the roads."""

    draw_text(
        "SIMON MAZORODZE ROAD",
        small_font,
        12,
        INTERSECTION_Y - ROAD_WIDTH // 2 - 22,
        LIGHT_TEXT,
    )

    draw_text(
        "PAISLEY ROAD",
        small_font,
        INTERSECTION_X + ROAD_WIDTH // 2 + 4,
        145,
        LIGHT_TEXT,
    )

    draw_text(
        "REMEMBRANCE DRIVE",
        small_font,
        INTERSECTION_X + ROAD_WIDTH // 2 + 45,
        INTERSECTION_Y + ROAD_WIDTH // 2 + 25,
        LIGHT_TEXT,
    )


def draw_vehicles(intersection):
    """Draw all vehicles."""

    for approach in intersection.approaches:

        for vehicle in approach.vehicles:

            color = vehicle_color(
                vehicle.vehicle_type
            )

            # Convert simulation position into screen position.
            position = vehicle.position

            if approach.direction == "north":

                x = INTERSECTION_X - 55
                y = (
                    INTERSECTION_Y
                    - ROAD_WIDTH // 2
                    - position * 1.0
                )

                rect = pygame.Rect(
                    x,
                    y,
                    VEHICLE_WIDTH,
                    VEHICLE_HEIGHT,
                )

            elif approach.direction == "south":

                x = INTERSECTION_X + 18
                y = (
                    INTERSECTION_Y
                    + ROAD_WIDTH // 2
                    + position * 1.0
                )

                rect = pygame.Rect(
                    x,
                    y,
                    VEHICLE_WIDTH,
                    VEHICLE_HEIGHT,
                )

            elif approach.direction == "east":

                x = (
                    INTERSECTION_X
                    + ROAD_WIDTH // 2
                    + position * 1.0
                )

                y = INTERSECTION_Y + 20

                rect = pygame.Rect(
                    x,
                    y,
                    VEHICLE_WIDTH,
                    VEHICLE_HEIGHT,
                )

            else:

                x = (
                    INTERSECTION_X
                    - ROAD_WIDTH // 2
                    - position * 1.0
                )

                y = INTERSECTION_Y - 40

                rect = pygame.Rect(
                    x,
                    y,
                    VEHICLE_WIDTH,
                    VEHICLE_HEIGHT,
                )

            # Keep vehicles inside the visible screen.
            rect.x = max(
                0,
                min(
                    rect.x,
                    WIDTH - VEHICLE_WIDTH,
                ),
            )

            rect.y = max(
                0,
                min(
                    rect.y,
                    HEIGHT - VEHICLE_HEIGHT,
                ),
            )

            pygame.draw.rect(
                screen,
                color,
                rect,
                border_radius=5,
            )

            # Vehicle number
            number_surface = tiny_font.render(
                str(vehicle.vehicle_id),
                True,
                (20, 20, 20),
            )

            screen.blit(
                number_surface,
                (
                    rect.centerx
                    - number_surface.get_width() // 2,
                    rect.centery
                    - number_surface.get_height() // 2,
                ),
            )


def draw_dashboard(metrics, paused, speed_multiplier):
    """Draw the traffic operations dashboard."""

    panel = pygame.Rect(
        DASHBOARD_X,
        DASHBOARD_Y,
        DASHBOARD_WIDTH,
        DASHBOARD_HEIGHT,
    )

    pygame.draw.rect(
        screen,
        DARK_PANEL,
        panel,
        border_radius=10,
    )

    pygame.draw.rect(
        screen,
        PANEL_BORDER,
        panel,
        width=1,
        border_radius=10,
    )

    x = DASHBOARD_X + 14

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    draw_text(
        "TRAFFIC OPERATIONS",
        heading_font,
        x,
        DASHBOARD_Y + 16,
    )

    draw_text(
        "Harare Smart Traffic Simulation",
        tiny_font,
        x,
        DASHBOARD_Y + 42,
        LIGHT_TEXT,
    )

    draw_text(
        "Simon Mazorodze × Remembrance",
        tiny_font,
        x,
        DASHBOARD_Y + 59,
        LIGHT_TEXT,
    )

    # System status
    status_y = DASHBOARD_Y + 82

    status_color = YELLOW if paused else GREEN

    pygame.draw.circle(
        screen,
        status_color,
        (x + 7, status_y + 5),
        5,
    )

    draw_text(
        "SYSTEM PAUSED" if paused else "SYSTEM RUNNING",
        small_font,
        x + 17,
        status_y - 3,
    )

    # Show current speed next to the status.
    draw_text(
        f"SPEED {speed_multiplier:.2f}x",
        tiny_font,
        x + 150,
        status_y - 2,
        LIGHT_TEXT,
    )

    # --------------------------------------------------------
    # Key Metrics
    # --------------------------------------------------------

    metrics_y = DASHBOARD_Y + 112

    draw_text(
        "SIMULATION TIME",
        tiny_font,
        x,
        metrics_y,
        LIGHT_TEXT,
    )

    draw_text(
        f"{metrics.simulation_time:.1f}s",
        normal_font,
        x,
        metrics_y + 17,
    )

    draw_text(
        "TOTAL VEHICLES",
        tiny_font,
        x,
        metrics_y + 48,
        LIGHT_TEXT,
    )

    draw_text(
        metrics.total_vehicles,
        normal_font,
        x,
        metrics_y + 65,
    )

    draw_text(
        "QUEUED VEHICLES",
        tiny_font,
        x,
        metrics_y + 96,
        LIGHT_TEXT,
    )

    draw_text(
        metrics.total_queue_length,
        normal_font,
        x,
        metrics_y + 113,
    )

    # Average waiting time
    draw_text(
        "AVERAGE WAITING TIME",
        tiny_font,
        x,
        metrics_y + 144,
        LIGHT_TEXT,
    )

    draw_text(
        f"{metrics.average_waiting_time:.1f}s",
        normal_font,
        x,
        metrics_y + 161,
    )

    # Total waiting time
    draw_text(
        "TOTAL WAITING TIME",
        tiny_font,
        x,
        metrics_y + 192,
        LIGHT_TEXT,
    )

    draw_text(
        f"{metrics.total_waiting_time:.1f}s",
        normal_font,
        x,
        metrics_y + 209,
    )

    # --------------------------------------------------------
    # Congestion
    # --------------------------------------------------------

    congestion_y = DASHBOARD_Y + 338

    draw_text(
        "OVERALL CONGESTION",
        tiny_font,
        x,
        congestion_y,
        LIGHT_TEXT,
    )

    congestion_box = pygame.Rect(
        x,
        congestion_y + 17,
        DASHBOARD_WIDTH - 28,
        34,
    )

    pygame.draw.rect(
        screen,
        (35, 35, 35),
        congestion_box,
        border_radius=6,
    )

    congestion_colors = {
        "LOW": GREEN,
        "MODERATE": YELLOW,
        "HIGH": ORANGE,
        "SEVERE": RED,
    }

    congestion_color = congestion_colors.get(
        metrics.congestion_level,
        WHITE,
    )

    pygame.draw.circle(
        screen,
        congestion_color,
        (
            congestion_box.x + 18,
            congestion_box.centery,
        ),
        8,
    )

    draw_text(
        metrics.congestion_level,
        normal_font,
        congestion_box.x + 34,
        congestion_box.y + 8,
    )

    # --------------------------------------------------------
    # Vehicle Composition
    # --------------------------------------------------------

    composition_y = DASHBOARD_Y + 390

    draw_text(
        "VEHICLE COMPOSITION",
        tiny_font,
        x,
        composition_y,
        LIGHT_TEXT,
    )

    counts = {
        "Cars": 0,
        "Kombis": 0,
        "Trucks": 0,
        "Buses": 0,
    }

    intersection = system.intersections[0]

    for approach in intersection.approaches:

        for vehicle in approach.vehicles:

            if vehicle.vehicle_type == "car":
                counts["Cars"] += 1

            elif vehicle.vehicle_type == "combi":
                counts["Kombis"] += 1

            elif vehicle.vehicle_type == "truck":
                counts["Trucks"] += 1

            elif vehicle.vehicle_type == "bus":
                counts["Buses"] += 1

    draw_text(
        f"Cars: {counts['Cars']}",
        tiny_font,
        x,
        composition_y + 20,
    )

    draw_text(
        f"Kombis: {counts['Kombis']}",
        tiny_font,
        x + 130,
        composition_y + 20,
    )

    draw_text(
        f"Trucks: {counts['Trucks']}",
        tiny_font,
        x,
        composition_y + 38,
    )

    draw_text(
        f"Buses: {counts['Buses']}",
        tiny_font,
        x + 130,
        composition_y + 38,
    )

    # --------------------------------------------------------
    # Approach Status
    # --------------------------------------------------------

    approach_y = DASHBOARD_Y + 446

    draw_text(
        "APPROACH STATUS",
        tiny_font,
        x,
        approach_y,
        LIGHT_TEXT,
    )

    current_y = approach_y + 18

    for road_name, approach_metrics in metrics.approach_metrics.items():

        # Shorten long names where necessary.
        display_name = road_name

        if len(display_name) > 24:
            display_name = display_name[:22] + "..."

        draw_text(
            display_name,
            tiny_font,
            x,
            current_y,
        )

        current_y += 15

        draw_text(
            (
                f"Signal: {approach_metrics.signal_state}   "
                f"Queue: {approach_metrics.queue_length}"
            ),
            tiny_font,
            x + 4,
            current_y,
            LIGHT_TEXT,
        )

        current_y += 14

        draw_text(
            f"Wait: {approach_metrics.total_waiting_time:.1f}s",
            tiny_font,
            x + 4,
            current_y,
            LIGHT_TEXT,
        )

        current_y += 20

    # --------------------------------------------------------
    # Queue Trend
    # --------------------------------------------------------

    chart_title_y = DASHBOARD_Y + 568

    draw_text(
        "QUEUE TREND",
        tiny_font,
        x,
        chart_title_y,
        LIGHT_TEXT,
    )

    chart = pygame.Rect(
        x,
        chart_title_y + 17,
        DASHBOARD_WIDTH - 28,
        55,
    )

    pygame.draw.rect(
        screen,
        (31, 31, 31),
        chart,
        border_radius=4,
    )

    pygame.draw.rect(
        screen,
        PANEL_BORDER,
        chart,
        width=1,
        border_radius=4,
    )

    if len(queue_history) > 1:

        visible_history = queue_history[-40:]

        max_queue = max(
            max(visible_history),
            1,
        )

        points = []

        for index, value in enumerate(visible_history):

            if len(visible_history) == 1:
                px = chart.x
            else:
                px = chart.x + (
                    index
                    / (len(visible_history) - 1)
                ) * chart.width

            py = chart.bottom - 7 - (
                value / max_queue
            ) * (chart.height - 14)

            points.append(
                (
                    int(px),
                    int(py),
                )
            )

        if len(points) >= 2:
            pygame.draw.lines(
                screen,
                GREEN,
                False,
                points,
                2,
            )

    # Current queue number
    draw_text(
        f"{metrics.total_queue_length}",
        tiny_font,
        chart.x + 8,
        chart.y + 7,
        WHITE,
    )


def reset_simulation():
    """Reset the simulation."""

    global system
    global engine
    global metrics
    global queue_history
    global paused

    system = create_harare_traffic_system()
    engine = SimulationEngine(system)

    metrics = metrics_service.collect(system)

    queue_history = []

    paused = False


# ============================================================
# MAIN LOOP
# ============================================================

running = True

# Time accumulator: how many seconds of real time have elapsed
# since the last engine step.
sim_accumulator = 0.0

while running:

    # dt = seconds elapsed since the previous frame
    dt = clock.tick(FPS) / 1000.0

    # --------------------------------------------------------
    # Events
    # --------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                paused = not paused

            elif event.key == pygame.K_r:
                reset_simulation()

            # Speed up: UP arrow or '=' / '+'
            elif event.key in (
                pygame.K_UP,
                pygame.K_EQUALS,
                pygame.K_PLUS,
                pygame.K_KP_PLUS,
            ):
                speed_multiplier = min(
                    speed_multiplier * SPEED_STEP,
                    8.0,
                )

            # Slow down: DOWN arrow or '-' / '_'
            elif event.key in (
                pygame.K_DOWN,
                pygame.K_MINUS,
                pygame.K_UNDERSCORE,
                pygame.K_KP_MINUS,
            ):
                speed_multiplier = max(
                    speed_multiplier / SPEED_STEP,
                    0.05,
                )

    # --------------------------------------------------------
    # Simulation update
    # --------------------------------------------------------

    if not paused:

        # Target interval (real seconds) between engine steps.
        # Smaller interval = faster simulation.
        step_interval = SIMULATION_SPEED / speed_multiplier

        sim_accumulator += dt

        # Run as many engine steps as the accumulator allows.
        # Cap the loop so a laggy frame can't cause a spiral.
        max_steps_per_frame = 60
        steps_done = 0

        while (
            sim_accumulator >= step_interval
            and steps_done < max_steps_per_frame
        ):
            engine.step()
            sim_accumulator -= step_interval
            steps_done += 1

            metrics = metrics_service.collect(system)

            queue_history.append(
                metrics.total_queue_length
            )

            if len(queue_history) > 100:
                queue_history.pop(0)

    # --------------------------------------------------------
    # Drawing
    # --------------------------------------------------------

    screen.fill(BACKGROUND)

    # Title
    draw_centered_text(
        "HARARE SMART TRAFFIC SIMULATION",
        title_font,
        INTERSECTION_X,
        70,
    )

    draw_roads()
    draw_road_labels()

    # Traffic lights
    intersection = system.intersections[0]

    for approach in intersection.approaches:

        if approach.traffic_light is None:
            continue

        state = approach.traffic_light.state

        if approach.direction == "north":

            draw_traffic_light(
                INTERSECTION_X - 134,
                INTERSECTION_Y - 35,
                state,
                "SIMON",
            )

        elif approach.direction == "east":

            draw_traffic_light(
                INTERSECTION_X + 65,
                INTERSECTION_Y + 15,
                state,
                "REMEMBRANCE",
            )

        elif approach.direction == "south":

            draw_traffic_light(
                INTERSECTION_X - 134,
                INTERSECTION_Y + 45,
                state,
                "PAISLEY",
            )

    draw_vehicles(intersection)

    draw_dashboard(
        metrics,
        paused,
        speed_multiplier,
    )

    # --------------------------------------------------------
    # Controls
    # --------------------------------------------------------

    draw_text(
        "SPACE: Pause/Resume   R: Reset   "
        "UP/DOWN: Speed   ESC: Exit",
        small_font,
        8,
        HEIGHT - 20,
        LIGHT_TEXT,
    )

    draw_text(
        f"Speed: {speed_multiplier:.2f}x",
        small_font,
        WIDTH - 130,
        HEIGHT - 20,
        WHITE,
    )

    pygame.display.flip()


pygame.quit()