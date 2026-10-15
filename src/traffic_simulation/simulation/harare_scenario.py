from traffic_simulation.domain.models import (
    Intersection,
    RoadApproach,
    TrafficLight,
    TrafficSystem,
    TrafficVehicle,
)


def create_simon_mazorodze_remembrance_intersection() -> Intersection:
    """
    Create the Simon Mazorodze Road × Remembrance Drive
    intersection scenario in Harare.
    """

    intersection = Intersection(
        intersection_id=1,
        name="Simon Mazorodze Road × Remembrance Drive",
    )

    # ---------------------------------------------------------
    # Traffic lights
    # ---------------------------------------------------------

    simon_mazorodze_light = TrafficLight(
        light_id=1,
        state="GREEN",
        duration=30,
    )

    remembrance_drive_light = TrafficLight(
        light_id=2,
        state="RED",
        duration=30,
    )

    paisley_road_light = TrafficLight(
        light_id=3,
        state="RED",
        duration=30,
    )

    # ---------------------------------------------------------
    # Road approaches
    # ---------------------------------------------------------

    simon_mazorodze = RoadApproach(
        approach_id=1,
        road_name="Simon Mazorodze Road",
        direction="north",
        stop_position=100.0,
    )

    remembrance_drive = RoadApproach(
        approach_id=2,
        road_name="Remembrance Drive",
        direction="east",
        stop_position=100.0,
    )

    paisley_road = RoadApproach(
        approach_id=3,
        road_name="Paisley Road",
        direction="south",
        stop_position=100.0,
    )

    # ---------------------------------------------------------
    # Attach traffic lights to their approaches
    # ---------------------------------------------------------

    simon_mazorodze.add_traffic_light(
        simon_mazorodze_light
    )

    remembrance_drive.add_traffic_light(
        remembrance_drive_light
    )

    paisley_road.add_traffic_light(
        paisley_road_light
    )

    # ---------------------------------------------------------
    # Add traffic lights to the intersection
    # ---------------------------------------------------------

    intersection.add_traffic_light(
        simon_mazorodze_light
    )

    intersection.add_traffic_light(
        remembrance_drive_light
    )

    intersection.add_traffic_light(
        paisley_road_light
    )

    # ---------------------------------------------------------
    # Simon Mazorodze Road vehicles
    # ---------------------------------------------------------

    simon_mazorodze.add_vehicle(
        TrafficVehicle(
            vehicle_id=1,
            speed=12,
            position=0,
            vehicle_type="car",
        )
    )

    simon_mazorodze.add_vehicle(
        TrafficVehicle(
            vehicle_id=2,
            speed=10,
            position=20,
            vehicle_type="combi",
        )
    )

    simon_mazorodze.add_vehicle(
        TrafficVehicle(
            vehicle_id=3,
            speed=8,
            position=40,
            vehicle_type="truck",
        )
    )

    # ---------------------------------------------------------
    # Remembrance Drive vehicles
    # ---------------------------------------------------------

    remembrance_drive.add_vehicle(
        TrafficVehicle(
            vehicle_id=4,
            speed=11,
            position=0,
            vehicle_type="car",
        )
    )

    remembrance_drive.add_vehicle(
        TrafficVehicle(
            vehicle_id=5,
            speed=9,
            position=25,
            vehicle_type="combi",
        )
    )

    remembrance_drive.add_vehicle(
        TrafficVehicle(
            vehicle_id=6,
            speed=7,
            position=50,
            vehicle_type="bus",
        )
    )

    # ---------------------------------------------------------
    # Paisley Road vehicles
    # ---------------------------------------------------------

    paisley_road.add_vehicle(
        TrafficVehicle(
            vehicle_id=7,
            speed=10,
            position=0,
            vehicle_type="car",
        )
    )

    paisley_road.add_vehicle(
        TrafficVehicle(
            vehicle_id=8,
            speed=8,
            position=30,
            vehicle_type="combi",
        )
    )

    # ---------------------------------------------------------
    # Add approaches to intersection
    # ---------------------------------------------------------

    intersection.add_approach(
        simon_mazorodze
    )

    intersection.add_approach(
        remembrance_drive
    )

    intersection.add_approach(
        paisley_road
    )

    return intersection


def create_harare_traffic_system() -> TrafficSystem:
    """
    Create a Harare traffic system containing the
    Simon Mazorodze Road × Remembrance Drive intersection.
    """

    traffic_system = TrafficSystem()

    intersection = (
        create_simon_mazorodze_remembrance_intersection()
    )

    traffic_system.add_intersection(
        intersection
    )

    return traffic_system