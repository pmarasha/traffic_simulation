"""
Harare Traffic Network Configuration.

Stage 2 of the traffic simulation.

Defines a connected network of intersections and roads
without changing the existing domain model.
"""

from dataclasses import dataclass
from typing import Dict, List


# =========================================================
# ROAD SEGMENT
# =========================================================

@dataclass(frozen=True)
class RoadSegment:
    """
    Represents a road connecting two intersections.
    """

    road_id: str
    name: str
    start_intersection: str
    end_intersection: str
    length_m: float
    speed_limit_kmh: float


# =========================================================
# NETWORK INTERSECTION
# =========================================================

@dataclass(frozen=True)
class NetworkIntersection:
    """
    Represents an intersection in the Harare network.
    """

    intersection_id: str
    name: str
    x: int
    y: int


# =========================================================
# HARARE TRAFFIC NETWORK
# =========================================================

class HarareTrafficNetwork:
    """
    Configuration of the initial Harare road network.

    This class describes the network topology only.

    Traffic behaviour remains handled by the network
    simulation and existing domain layers.
    """

    def __init__(self) -> None:
        self.intersections: Dict[
            str,
            NetworkIntersection,
        ] = {}

        self.roads: Dict[
            str,
            RoadSegment,
        ] = {}

        self._build_network()

    # -----------------------------------------------------
    # BUILD NETWORK
    # -----------------------------------------------------

    def _build_network(self) -> None:
        """
        Build the initial connected Harare road network.
        """

        # -------------------------------------------------
        # INTERSECTIONS
        # -------------------------------------------------

        self.intersections = {

            "INT-001": NetworkIntersection(
                intersection_id="INT-001",
                name="Simon Mazorodze / Remembrance",
                x=400,
                y=350,
            ),

            "INT-002": NetworkIntersection(
                intersection_id="INT-002",
                name="Simon Mazorodze / Paisley",
                x=700,
                y=350,
            ),

            "INT-003": NetworkIntersection(
                intersection_id="INT-003",
                name="Remembrance / Paisley",
                x=550,
                y=150,
            ),

            "INT-004": NetworkIntersection(
                intersection_id="INT-004",
                name="Southern Harare Approach",
                x=550,
                y=550,
            ),
        }

        # -------------------------------------------------
        # ROADS
        # -------------------------------------------------

        self.roads = {

            # -------------------------------------------------
            # RD-001
            # Simon Mazorodze Road
            #
            # INT-001 -> INT-002
            # -------------------------------------------------

            "RD-001": RoadSegment(
                road_id="RD-001",
                name="Simon Mazorodze Road",
                start_intersection="INT-001",
                end_intersection="INT-002",
                length_m=1200,
                speed_limit_kmh=60,
            ),

            # -------------------------------------------------
            # RD-002
            # Remembrance Drive
            #
            # INT-001 -> INT-003
            # -------------------------------------------------

            "RD-002": RoadSegment(
                road_id="RD-002",
                name="Remembrance Drive",
                start_intersection="INT-001",
                end_intersection="INT-003",
                length_m=900,
                speed_limit_kmh=50,
            ),

            # -------------------------------------------------
            # RD-003
            # Paisley Road
            #
            # INT-002 -> INT-003
            #
            # This connection allows:
            #
            # RD-001 -> RD-003
            #
            # which is required by the network routing tests.
            # -------------------------------------------------

            "RD-003": RoadSegment(
                road_id="RD-003",
                name="Paisley Road",
                start_intersection="INT-002",
                end_intersection="INT-003",
                length_m=1000,
                speed_limit_kmh=50,
            ),

            # -------------------------------------------------
            # RD-004
            # Southern Approach
            #
            # INT-003 -> INT-004
            # -------------------------------------------------

            "RD-004": RoadSegment(
                road_id="RD-004",
                name="Southern Approach",
                start_intersection="INT-003",
                end_intersection="INT-004",
                length_m=1100,
                speed_limit_kmh=50,
            ),
        }

    # -----------------------------------------------------
    # GET INTERSECTIONS
    # -----------------------------------------------------

    def get_intersections(
        self,
    ) -> List[NetworkIntersection]:
        """
        Return all intersections in the network.
        """

        return list(
            self.intersections.values()
        )

    # -----------------------------------------------------
    # GET ROADS
    # -----------------------------------------------------

    def get_roads(
        self,
    ) -> List[RoadSegment]:
        """
        Return all roads in the network.
        """

        return list(
            self.roads.values()
        )

    # -----------------------------------------------------
    # GET ROAD
    # -----------------------------------------------------

    def get_road(
        self,
        road_id: str,
    ) -> RoadSegment:
        """
        Return a road by ID.
        """

        if road_id not in self.roads:

            raise KeyError(
                f"Road '{road_id}' does not exist."
            )

        return self.roads[road_id]

    # -----------------------------------------------------
    # GET INTERSECTION
    # -----------------------------------------------------

    def get_intersection(
        self,
        intersection_id: str,
    ) -> NetworkIntersection:
        """
        Return an intersection by ID.
        """

        if (
            intersection_id
            not in self.intersections
        ):

            raise KeyError(
                f"Intersection "
                f"'{intersection_id}' "
                f"does not exist."
            )

        return self.intersections[
            intersection_id
        ]