from traffic_simulation.simulation.harare_scenario import (
    create_harare_traffic_system,
    create_simon_mazorodze_remembrance_intersection,
)


def test_harare_intersection_has_correct_name():
    intersection = create_simon_mazorodze_remembrance_intersection()

    assert (
        intersection.name
        == "Simon Mazorodze Road × Remembrance Drive"
    )


def test_harare_intersection_has_three_approaches():
    intersection = create_simon_mazorodze_remembrance_intersection()

    assert len(intersection.approaches) == 3


def test_harare_intersection_has_correct_road_approaches():
    intersection = create_simon_mazorodze_remembrance_intersection()

    road_names = [
        approach.road_name
        for approach in intersection.approaches
    ]

    assert "Simon Mazorodze Road" in road_names
    assert "Remembrance Drive" in road_names
    assert "Paisley Road" in road_names


def test_harare_intersection_has_three_traffic_lights():
    intersection = create_simon_mazorodze_remembrance_intersection()

    assert len(intersection.traffic_lights) == 3


def test_harare_intersection_has_vehicles():
    intersection = create_simon_mazorodze_remembrance_intersection()

    total_vehicles = sum(
        approach.traffic_volume
        for approach in intersection.approaches
    )

    assert total_vehicles == 8


def test_harare_intersection_contains_different_vehicle_types():
    intersection = create_simon_mazorodze_remembrance_intersection()

    vehicle_types = []

    for approach in intersection.approaches:
        for vehicle in approach.vehicles:
            vehicle_types.append(vehicle.vehicle_type)

    assert "car" in vehicle_types
    assert "combi" in vehicle_types
    assert "bus" in vehicle_types
    assert "truck" in vehicle_types


def test_harare_traffic_system_contains_intersection():
    traffic_system = create_harare_traffic_system()

    assert len(traffic_system.intersections) == 1

    assert (
        traffic_system.intersections[0].name
        == "Simon Mazorodze Road × Remembrance Drive"
    )


def test_harare_traffic_system_starts_at_zero():
    traffic_system = create_harare_traffic_system()

    assert traffic_system.simulation_time == 0


def test_each_approach_has_its_own_traffic_light():
    intersection = create_simon_mazorodze_remembrance_intersection()

    for approach in intersection.approaches:
        assert approach.traffic_light is not None


def test_simon_mazorodze_starts_green():
    intersection = create_simon_mazorodze_remembrance_intersection()

    simon_mazorodze = intersection.approaches[0]

    assert simon_mazorodze.traffic_light.state == "GREEN"


def test_remembrance_drive_starts_red():
    intersection = create_simon_mazorodze_remembrance_intersection()

    remembrance_drive = intersection.approaches[1]

    assert remembrance_drive.traffic_light.state == "RED"


def test_paisley_road_starts_red():
    intersection = create_simon_mazorodze_remembrance_intersection()

    paisley_road = intersection.approaches[2]

    assert paisley_road.traffic_light.state == "RED"


def test_red_approach_vehicle_stops_at_stop_line():
    intersection = create_simon_mazorodze_remembrance_intersection()

    remembrance_drive = intersection.approaches[1]

    vehicle = remembrance_drive.vehicles[0]

    intersection.update(20)

    assert vehicle.position == 100.0


def test_green_approach_vehicle_moves():
    intersection = create_simon_mazorodze_remembrance_intersection()

    simon_mazorodze = intersection.approaches[0]

    vehicle = simon_mazorodze.vehicles[0]

    initial_position = vehicle.position

    intersection.update(5)

    assert vehicle.position > initial_position


def test_red_approach_has_queue():
    intersection = create_simon_mazorodze_remembrance_intersection()

    remembrance_drive = intersection.approaches[1]

    intersection.update(20)

    assert remembrance_drive.queue_length > 0