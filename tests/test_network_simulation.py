"""
Tests for the Harare network traffic simulation.

These tests verify:
    - network creation
    - vehicle movement
    - traffic-light behavior
    - waiting time
    - queue length
    - vehicle routing
    - completed vehicles
    - network-level KPIs
"""

import pytest

from traffic_simulation.domain.models import TrafficVehicle
from traffic_simulation.network.network_simulation import (
    NetworkSimulation,
)
from traffic_simulation.simulation.harare_network_scenario import (
    create_harare_network_simulation,
)


# ---------------------------------------------------------
# Network creation
# ---------------------------------------------------------


def test_network_simulation_creates_four_intersections():
    simulation = create_harare_network_simulation()

    assert len(
        simulation.network.get_intersections()
    ) == 4


def test_network_simulation_creates_four_roads():
    simulation = create_harare_network_simulation()

    assert len(simulation.roads) == 4


def test_harare_network_contains_six_vehicles():
    simulation = create_harare_network_simulation()

    assert simulation.total_vehicle_count == 6


# ---------------------------------------------------------
# Vehicle movement
# ---------------------------------------------------------


def test_vehicle_moves_forward():
    simulation = NetworkSimulation()

    vehicle = TrafficVehicle(
        vehicle_id=1,
        speed=10,
        position=0,
    )

    simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
    )

    simulation.step(1)

    network_vehicle = simulation.get_vehicle(1)

    assert network_vehicle is not None
    assert network_vehicle.position == 10


def test_vehicle_moves_multiple_seconds():
    simulation = NetworkSimulation()

    vehicle = TrafficVehicle(
        vehicle_id=2,
        speed=20,
        position=0,
    )

    simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
    )

    simulation.step(5)

    network_vehicle = simulation.get_vehicle(2)

    assert network_vehicle is not None
    assert network_vehicle.position == 100


# ---------------------------------------------------------
# Traffic lights
# ---------------------------------------------------------


def test_red_light_is_respected():
    simulation = NetworkSimulation()

    simulation.add_traffic_light(
        "RD-001-LIGHT",
        state="RED",
        duration=30,
    )

    simulation.assign_traffic_light_to_road(
        "RD-001",
        "RD-001-LIGHT",
    )

    vehicle = TrafficVehicle(
        vehicle_id=10,
        speed=100,
        position=1100,
    )

    simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
    )

    simulation.step(2)

    network_vehicle = simulation.get_vehicle(10)

    assert network_vehicle is not None
    assert network_vehicle.position == 1200
    assert network_vehicle.vehicle.waiting_time == 2


def test_green_light_allows_vehicle_to_continue():
    simulation = NetworkSimulation()

    simulation.add_traffic_light(
        "RD-001-LIGHT",
        state="GREEN",
        duration=30,
    )

    simulation.assign_traffic_light_to_road(
        "RD-001",
        "RD-001-LIGHT",
    )

    vehicle = TrafficVehicle(
        vehicle_id=11,
        speed=100,
        position=100,
    )

    simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
    )

    simulation.step(2)

    network_vehicle = simulation.get_vehicle(11)

    assert network_vehicle is not None
    assert network_vehicle.position == 300
    assert network_vehicle.vehicle.waiting_time == 0


def test_traffic_light_changes_state():
    simulation = NetworkSimulation()

    simulation.add_traffic_light(
        "TEST-LIGHT",
        state="GREEN",
        duration=30,
    )

    simulation.update_traffic_lights(30)

    assert (
        simulation.traffic_lights[
            "TEST-LIGHT"
        ].state
        == "YELLOW"
    )


# ---------------------------------------------------------
# Queue and waiting time
# ---------------------------------------------------------


def test_waiting_time_accumulates_at_red_light():
    simulation = NetworkSimulation()

    simulation.add_traffic_light(
        "RD-001-LIGHT",
        state="RED",
        duration=30,
    )

    simulation.assign_traffic_light_to_road(
        "RD-001",
        "RD-001-LIGHT",
    )

    vehicle = TrafficVehicle(
        vehicle_id=20,
        speed=100,
        position=1200,
    )

    simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
    )

    simulation.step(5)

    network_vehicle = simulation.get_vehicle(20)

    assert network_vehicle is not None
    assert network_vehicle.vehicle.waiting_time == 5


def test_queue_length_increases_when_vehicle_waits():
    simulation = NetworkSimulation()

    simulation.add_traffic_light(
        "RD-001-LIGHT",
        state="RED",
        duration=30,
    )

    simulation.assign_traffic_light_to_road(
        "RD-001",
        "RD-001-LIGHT",
    )

    vehicle = TrafficVehicle(
        vehicle_id=21,
        speed=100,
        position=1200,
    )

    simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
    )

    simulation.step(1)

    assert simulation.total_queue_length == 1


# ---------------------------------------------------------
# Road connectivity
# ---------------------------------------------------------


def test_connected_roads_are_returned():
    simulation = NetworkSimulation()

    connected_roads = simulation.get_connected_roads(
        "RD-001"
    )

    connected_ids = {
        road.road_id
        for road in connected_roads
    }

    assert "RD-002" in connected_ids
    assert "RD-003" in connected_ids


def test_invalid_road_raises_error():
    simulation = NetworkSimulation()

    with pytest.raises(KeyError):
        simulation.get_road("INVALID-ROAD")


# ---------------------------------------------------------
# Vehicle routing
# ---------------------------------------------------------


def test_vehicle_can_route_to_connected_road():
    simulation = NetworkSimulation()

    vehicle = TrafficVehicle(
        vehicle_id=30,
        speed=100,
        position=1200,
    )

    network_vehicle = simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
        next_road_id="RD-003",
    )

    routed = simulation.route_vehicle(
        network_vehicle
    )

    assert routed is True
    assert network_vehicle.road_id == "RD-003"
    assert network_vehicle.position == 0


def test_vehicle_cannot_route_to_unconnected_road():
    simulation = NetworkSimulation()

    vehicle = TrafficVehicle(
        vehicle_id=31,
        speed=100,
        position=1200,
    )

    network_vehicle = simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
    )

    routed = simulation.route_vehicle(
        network_vehicle,
        "RD-004",
    )

    assert routed is False
    assert network_vehicle.road_id == "RD-001"


# ---------------------------------------------------------
# Vehicle completion
# ---------------------------------------------------------


def test_vehicle_completes_when_no_next_road_exists():
    simulation = NetworkSimulation()

    vehicle = TrafficVehicle(
        vehicle_id=40,
        speed=100,
        position=1100,
    )

    simulation.add_vehicle(
        vehicle,
        road_id="RD-001",
    )

    simulation.step(2)

    network_vehicle = simulation.get_vehicle(40)

    assert network_vehicle is not None
    assert network_vehicle.completed is True
    assert simulation.completed_vehicle_count == 1


# ---------------------------------------------------------
# Network metrics
# ---------------------------------------------------------


def test_network_metrics_return_expected_values():
    simulation = create_harare_network_simulation()

    metrics = simulation.get_network_metrics()

    assert metrics["total_vehicles"] == 6
    assert metrics["active_vehicles"] == 6
    assert metrics["completed_vehicles"] == 0
    assert metrics["road_count"] == 4
    assert metrics["intersection_count"] == 4


def test_average_waiting_time_is_zero_initially():
    simulation = create_harare_network_simulation()

    assert simulation.average_waiting_time == 0


def test_average_vehicle_speed_is_calculated():
    simulation = NetworkSimulation()

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=50,
            speed=40,
            position=0,
        ),
        road_id="RD-001",
    )

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=51,
            speed=60,
            position=0,
        ),
        road_id="RD-001",
    )

    assert simulation.average_vehicle_speed == 50


# ---------------------------------------------------------
# Simulation time
# ---------------------------------------------------------


def test_simulation_time_advances():
    simulation = NetworkSimulation()

    simulation.step(5)

    assert simulation.simulation_time == 5


def test_invalid_time_step_is_rejected():
    simulation = NetworkSimulation()

    with pytest.raises(ValueError):
        simulation.step(0)

    with pytest.raises(ValueError):
        simulation.step(-1)


# ---------------------------------------------------------
# Reset
# ---------------------------------------------------------


def test_network_simulation_can_reset():
    simulation = NetworkSimulation()

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=60,
            speed=20,
            position=0,
        ),
        road_id="RD-001",
    )

    simulation.step(5)

    assert simulation.simulation_time == 5

    simulation.reset()

    assert simulation.simulation_time == 0
    assert simulation.total_vehicle_count == 0
    assert simulation.completed_vehicle_count == 0