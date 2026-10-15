from traffic_simulation.domain.models import (
    TrafficLight,
    TrafficVehicle,
    Intersection,
    TrafficSystem,
    RoadApproach,
)

from traffic_simulation.simulation.engine import SimulationEngine


def test_traffic_light_changes_automatically():
    light = TrafficLight(
        light_id=1,
        state="RED",
        duration=30,
    )

    light.update(30)

    assert light.state == "GREEN"


def test_traffic_light_changes_from_green_to_yellow():
    light = TrafficLight(
        light_id=1,
        state="GREEN",
        duration=30,
    )

    light.update(30)

    assert light.state == "YELLOW"


def test_traffic_light_changes_from_yellow_to_red():
    light = TrafficLight(
        light_id=1,
        state="YELLOW",
        duration=30,
    )

    light.update(30)

    assert light.state == "RED"


def test_traffic_light_does_not_change_before_duration():
    light = TrafficLight(
        light_id=1,
        state="RED",
        duration=30,
    )

    light.update(10)

    assert light.state == "RED"


def test_vehicle_stops_at_red_light():
    light = TrafficLight(
        light_id=1,
        state="RED",
        duration=30,
    )

    vehicle = TrafficVehicle(
        vehicle_id=1,
        speed=10,
        position=0,
        stop_position=0,
    )

    vehicle.move(5, light)

    assert vehicle.position == 0


def test_vehicle_moves_when_light_is_green():
    light = TrafficLight(
        light_id=1,
        state="GREEN",
        duration=30,
    )

    vehicle = TrafficVehicle(
        vehicle_id=1,
        speed=10,
        position=0,
    )

    vehicle.move(5, light)

    assert vehicle.position == 50


def test_intersection_can_add_traffic_light():
    intersection = Intersection(
        intersection_id=1,
        name="Main Intersection",
    )

    light = TrafficLight(
        light_id=1,
        state="RED",
        duration=30,
    )

    intersection.add_traffic_light(light)

    assert len(intersection.traffic_lights) == 1


def test_intersection_can_add_vehicle():
    intersection = Intersection(
        intersection_id=1,
        name="Main Intersection",
    )

    vehicle = TrafficVehicle(
        vehicle_id=1,
        speed=10,
        position=0,
    )

    intersection.add_vehicle(vehicle)

    assert len(intersection.vehicles) == 1


def test_intersection_updates_traffic_lights():
    intersection = Intersection(
        intersection_id=1,
        name="Main Intersection",
    )

    light = TrafficLight(
        light_id=1,
        state="RED",
        duration=30,
    )

    intersection.add_traffic_light(light)

    intersection.update(30)

    assert light.state == "GREEN"


def test_intersection_vehicle_stops_at_red_light():
    intersection = Intersection(
        intersection_id=1,
        name="Main Intersection",
    )

    light = TrafficLight(
        light_id=1,
        state="RED",
        duration=30,
    )

    vehicle = TrafficVehicle(
        vehicle_id=1,
        speed=10,
        position=0,
        stop_position=0,
    )

    intersection.add_traffic_light(light)
    intersection.add_vehicle(vehicle)

    intersection.update(5)

    assert vehicle.position == 0


def test_intersection_vehicle_moves_at_green_light():
    intersection = Intersection(
        intersection_id=1,
        name="Main Intersection",
    )

    light = TrafficLight(
        light_id=1,
        state="GREEN",
        duration=30,
    )

    vehicle = TrafficVehicle(
        vehicle_id=1,
        speed=10,
        position=0,
    )

    intersection.add_traffic_light(light)
    intersection.add_vehicle(vehicle)

    intersection.update(5)

    assert vehicle.position == 50


def test_traffic_system_can_add_intersection():
    system = TrafficSystem()

    intersection = Intersection(
        intersection_id=1,
        name="Main Intersection",
    )

    system.add_intersection(intersection)

    assert len(system.intersections) == 1


def test_traffic_system_updates_multiple_intersections():
    system = TrafficSystem()

    intersection1 = Intersection(
        intersection_id=1,
        name="Intersection 1",
    )

    intersection2 = Intersection(
        intersection_id=2,
        name="Intersection 2",
    )

    light1 = TrafficLight(
        light_id=1,
        state="RED",
        duration=30,
    )

    light2 = TrafficLight(
        light_id=2,
        state="RED",
        duration=30,
    )

    intersection1.add_traffic_light(light1)
    intersection2.add_traffic_light(light2)

    system.add_intersection(intersection1)
    system.add_intersection(intersection2)

    system.update(30)

    assert light1.state == "GREEN"
    assert light2.state == "GREEN"


def test_traffic_system_has_simulation_time():
    system = TrafficSystem()

    assert system.simulation_time == 0


def test_traffic_system_advances_simulation_time():
    system = TrafficSystem()

    system.update(10)

    assert system.simulation_time == 10


def test_simulation_engine_advances_traffic_system():
    system = TrafficSystem()

    engine = SimulationEngine(
        traffic_system=system,
        time_step=5,
    )

    engine.step()

    assert system.simulation_time == 5


def test_intersection_can_add_road_approach():
    intersection = Intersection(
        intersection_id=1,
        name="Simon Mazorodze Road × Remembrance Drive",
    )

    approach = RoadApproach(
        approach_id=1,
        road_name="Simon Mazorodze Road",
        direction="north",
    )

    intersection.add_approach(approach)

    assert len(intersection.approaches) == 1
    assert intersection.approaches[0].road_name == "Simon Mazorodze Road"


def test_road_approach_can_add_vehicle():
    approach = RoadApproach(
        approach_id=1,
        road_name="Simon Mazorodze Road",
        direction="north",
    )

    vehicle = TrafficVehicle(
        vehicle_id=1,
        speed=10,
        position=0,
    )

    approach.add_vehicle(vehicle)

    assert len(approach.vehicles) == 1
    assert approach.vehicles[0].direction == "north"
    assert approach.vehicles[0].stop_position == 100.0


def test_road_approach_tracks_traffic_volume():
    approach = RoadApproach(
        approach_id=1,
        road_name="Remembrance Drive",
        direction="east",
    )

    approach.add_vehicle(
        TrafficVehicle(
            vehicle_id=1,
            speed=10,
            position=20,
        )
    )

    approach.add_vehicle(
        TrafficVehicle(
            vehicle_id=2,
            speed=8,
            position=40,
        )
    )

    assert approach.traffic_volume == 2