"""
run_simulation.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from traffic_simulation.simulation.harare_scenario import (
    create_harare_traffic_system,
)
from traffic_simulation.simulation.engine import SimulationEngine
from traffic_simulation.simulation.metrics_service import MetricsService


def display_simulation(metrics) -> None:
    print("\n" + "=" * 60)
    print(f"SIMULATION TIME: {metrics.simulation_time:.0f} seconds")
    print("=" * 60)
    print(f"Total vehicles:      {metrics.total_vehicles}")
    print(f"Total queue length:  {metrics.total_queue_length}")
    print(f"Avg waiting time:    {metrics.average_waiting_time:.1f}s")
    print(f"Congestion level:    {metrics.congestion_level}")


def run_simulation(duration: int = 500, time_step: float = 1.0,
                   max_queue: int = 25, demand_multiplier: float = 1.0, **_ignored) -> dict:
    """
    Runs the microscopic traffic simulation.
    demand_multiplier: 1.0 = baseline, 0.7 = 70% morning peak demand.
    """
    
    # Safely attempt to pass demand multiplier to the scenario generator
    try:
        # If your underlying scenario supports this kwarg, it will use it.
        system = create_harare_traffic_system(demand_multiplier=demand_multiplier)
    except TypeError:
        # Fallback for existing functionality: load standard system
        system = create_harare_traffic_system()
        # Attempt to scale arrival rates directly if the attribute exists
        if hasattr(system, "arrival_rate"):
            system.arrival_rate *= demand_multiplier
        for intersection in system.intersections:
            for approach in intersection.approaches:
                if hasattr(approach, "arrival_rate"):
                    approach.arrival_rate *= demand_multiplier
                if hasattr(approach, "spawn_probability"):
                    approach.spawn_probability *= demand_multiplier

    engine = SimulationEngine(traffic_system=system, time_step=time_step)
    metrics_service = MetricsService()

    history = []
    steps = max(1, int(duration / time_step))

    prev_vehicles = 0
    cumulative_throughput = 0

    for tick in range(steps):
        engine.step()
        m = metrics_service.collect(system)

        vehicles = m.total_vehicles
        congestion = min(1.0, m.total_queue_length / max(1, max_queue))

        speeds = []
        for intersection in system.intersections:
            for approach in intersection.approaches:
                for v in approach.vehicles:
                    speeds.append(v.current_speed)
            for v in intersection.vehicles:
                speeds.append(v.current_speed)
        avg_speed = round(sum(speeds) / len(speeds), 2) if speeds else 0.0

        if vehicles < prev_vehicles:
            cumulative_throughput += (prev_vehicles - vehicles)
        prev_vehicles = vehicles

        lights = []
        for intersection in system.intersections:
            for light in intersection.traffic_lights:
                lights.append({
                    "intersection": intersection.name,
                    "light_id": light.light_id,
                    "state": light.state,
                    "time_in_state": round(light.time_in_state, 1),
                })

        approaches = []
        for intersection in system.intersections:
            for approach in intersection.approaches:
                approaches.append({
                    "road": approach.road_name,
                    "direction": approach.direction,
                    "vehicles": approach.traffic_volume,
                    "queue": approach.queue_length,
                    "signal": (
                        approach.traffic_light.state
                        if approach.traffic_light else "NONE"
                    ),
                })

        snapshot = {
            "tick": tick + 1,
            "time": round(system.simulation_time, 1),
            "vehicles": vehicles,
            "congestion": round(congestion, 3),
            "congestion_level": m.congestion_level,
            "avg_speed": avg_speed,
            "throughput": cumulative_throughput,
            "queue_length": m.total_queue_length,
            "avg_waiting_time": round(m.average_waiting_time, 2),
            "lights": lights,
            "approaches": approaches,
            "demand_multiplier": demand_multiplier,  # Track scenario in output
        }
        history.append(snapshot)

    return {
        "latest": history[-1] if history else {},
        "history": history,
        "meta": {
            "duration": duration,
            "time_step": time_step,
            "demand_multiplier": demand_multiplier,
            "intersections": [i.name for i in system.intersections],
        },
    }


def main() -> None:
    system = create_harare_traffic_system()
    engine = SimulationEngine(traffic_system=system, time_step=1.0)
    metrics_service = MetricsService()

    print("\nHARARE TRAFFIC SIMULATION")
    print("-------------------------")
    print("Starting simulation...")

    for _ in range(30):
        engine.step()
        m = metrics_service.collect(system)
        display_simulation(m)

    print("\nSimulation complete.")


if __name__ == "__main__":
    main()