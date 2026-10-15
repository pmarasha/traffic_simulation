"""
Harare Network Traffic Scenario.

Creates a multi-intersection Harare traffic scenario using
the connected road network and NetworkSimulation.

The existing harare_scenario.py remains unchanged.
"""

from traffic_simulation.domain.models import TrafficVehicle

from traffic_simulation.network.network_simulation import (
    NetworkSimulation,
)


def create_harare_network_simulation() -> NetworkSimulation:
    """
    Create the initial multi-intersection Harare network simulation.

    Network:

        INT-001
           |
        RD-001
           |
        INT-002
           |
        RD-003
           |
        INT-003
           |
        RD-004
           |
        INT-004

    Additional connection:

        INT-001
           |
        RD-002
           |
        INT-003
    """

    simulation = NetworkSimulation()

    # ---------------------------------------------------------
    # Traffic lights
    # ---------------------------------------------------------

    simulation.add_traffic_light(
        "INT-001-NORTH",
        state="GREEN",
        duration=30,
    )

    simulation.add_traffic_light(
        "INT-002-CENTRE",
        state="RED",
        duration=30,
    )

    simulation.add_traffic_light(
        "INT-003-CENTRE",
        state="RED",
        duration=30,
    )

    simulation.add_traffic_light(
        "INT-004-SOUTH",
        state="GREEN",
        duration=30,
    )

    # ---------------------------------------------------------
    # Vehicle 1
    #
    # Simon Mazorodze Road
    # RD-001 → Paisley Road
    # RD-003 → Southern Approach
    # RD-004
    # ---------------------------------------------------------

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=101,
            speed=60,
            position=0,
            vehicle_type="car",
            direction="east",
        ),
        road_id="RD-001",
        destination_intersection="INT-004",
        next_road_id="RD-003",
    )

    # ---------------------------------------------------------
    # Vehicle 2
    #
    # Remembrance Drive
    # RD-002 → Paisley Road
    # RD-003
    # ---------------------------------------------------------

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=102,
            speed=45,
            position=0,
            vehicle_type="combi",
            direction="north",
        ),
        road_id="RD-002",
        destination_intersection="INT-002",
        next_road_id="RD-003",
    )

    # ---------------------------------------------------------
    # Vehicle 3
    #
    # Simon Mazorodze Road
    # RD-001 → Remembrance Drive
    # RD-002
    # ---------------------------------------------------------

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=103,
            speed=50,
            position=150,
            vehicle_type="truck",
            direction="east",
        ),
        road_id="RD-001",
        destination_intersection="INT-003",
        next_road_id="RD-002",
    )

    # ---------------------------------------------------------
    # Vehicle 4
    #
    # Paisley Road
    # RD-003 → Southern Approach
    # RD-004
    # ---------------------------------------------------------

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=104,
            speed=55,
            position=100,
            vehicle_type="bus",
            direction="south",
        ),
        road_id="RD-003",
        destination_intersection="INT-004",
        next_road_id="RD-004",
    )

    # ---------------------------------------------------------
    # Vehicle 5
    #
    # Southern Approach
    # RD-004
    # Final destination INT-004
    # ---------------------------------------------------------

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=105,
            speed=40,
            position=250,
            vehicle_type="car",
            direction="south",
        ),
        road_id="RD-004",
        destination_intersection="INT-004",
    )

    # ---------------------------------------------------------
    # Vehicle 6
    #
    # Paisley Road
    # RD-003 → Southern Approach
    # RD-004
    # ---------------------------------------------------------

    simulation.add_vehicle(
        TrafficVehicle(
            vehicle_id=106,
            speed=35,
            position=50,
            vehicle_type="combi",
            direction="south",
        ),
        road_id="RD-003",
        destination_intersection="INT-004",
        next_road_id="RD-004",
    )

    return simulation