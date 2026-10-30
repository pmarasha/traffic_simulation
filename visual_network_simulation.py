"""
network_simulation.py

Core engine for the Harare Intelligent Traffic Network.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from traffic_simulation.domain.models import TrafficVehicle

@dataclass
class TrafficLight:
    light_id: str
    state: str = "GREEN"  # RED, YELLOW, GREEN
    duration: float = 30.0
    time_in_state: float = 0.0

@dataclass
class Road:
    road_id: str
    length_m: float = 1200.0
    speed_limit: float = 60.0

@dataclass
class RoadState:
    road_id: str
    road: Road
    traffic_light_id: Optional[str] = None

@dataclass
class NetworkVehicle:
    vehicle: TrafficVehicle
    road_id: str
    destination_intersection: Optional[str] = None
    next_road_id: Optional[str] = None
    completed: bool = False

    @property
    def position(self) -> float:
        return self.vehicle.position

    @position.setter
    def position(self, value: float):
        self.vehicle.position = value


class NetworkSimulation:
    def __init__(self):
        self.simulation_time: float = 0.0
        self.vehicles: List[NetworkVehicle] = []
        self.traffic_lights: Dict[str, TrafficLight] = {}
        self.roads: Dict[str, RoadState] = {}
        
        # Network topology for routing (matching Harare scenario)
        self.connected_roads = {
            "RD-001": ["RD-002", "RD-003"],
            "RD-002": ["RD-001", "RD-003"],
            "RD-003": ["RD-001", "RD-002", "RD-004"],
            "RD-004": ["RD-003"]
        }

    def add_road(self, road_id: str, length_m: float = 1200.0):
        if road_id not in self.roads:
            self.roads[road_id] = RoadState(
                road_id=road_id, 
                road=Road(road_id=road_id, length_m=length_m)
            )
        if road_id not in self.connected_roads:
            self.connected_roads[road_id] = []

    def get_road(self, road_id: str) -> Road:
        if road_id not in self.roads:
            raise KeyError(f"Road {road_id} not found")
        return self.roads[road_id].road

    def get_connected_roads(self, road_id: str) -> List[str]:
        return self.connected_roads.get(road_id, [])

    def add_traffic_light(self, light_id: str, state: str = "GREEN", duration: float = 30.0):
        self.traffic_lights[light_id] = TrafficLight(
            light_id=light_id, 
            state=state, 
            duration=duration
        )

    def assign_traffic_light_to_road(self, road_id: str, light_id: str):
        if road_id not in self.roads:
            self.add_road(road_id)
        self.roads[road_id].traffic_light_id = light_id

    def get_road_traffic_light(self, road_id: str) -> Optional[TrafficLight]:
        road_state = self.roads.get(road_id)
        if road_state and road_state.traffic_light_id:
            return self.traffic_lights.get(road_state.traffic_light_id)
        return None

    def add_vehicle(self, vehicle: TrafficVehicle, road_id: str, 
                    destination_intersection: Optional[str] = None, 
                    next_road_id: Optional[str] = None) -> NetworkVehicle:
        if road_id not in self.roads:
            self.add_road(road_id)
        nv = NetworkVehicle(
            vehicle=vehicle, 
            road_id=road_id,
            destination_intersection=destination_intersection,
            next_road_id=next_road_id
        )
        self.vehicles.append(nv)
        return nv

    def get_vehicle(self, vehicle_id: int) -> Optional[NetworkVehicle]:
        for nv in self.vehicles:
            if nv.vehicle.vehicle_id == vehicle_id:
                return nv
        return None

    def route_vehicle(self, network_vehicle: NetworkVehicle, new_road_id: str) -> bool:
        """Attempt to route a vehicle to a connected road."""
        current_road = network_vehicle.road_id
        if new_road_id in self.get_connected_roads(current_road):
            network_vehicle.road_id = new_road_id
            network_vehicle.position = 0.0
            return True
        return False

    def update_traffic_lights(self, time_seconds: float):
        for light in self.traffic_lights.values():
            light.time_in_state += time_seconds
            if light.time_in_state >= light.duration:
                light.time_in_state = 0.0
                if light.state == "GREEN":
                    light.state = "YELLOW"
                elif light.state == "YELLOW":
                    light.state = "RED"
                elif light.state == "RED":
                    light.state = "GREEN"

    def update_vehicles(self, time_seconds: float):
        for nv in self.vehicles:
            if nv.completed:
                continue

            v = nv.vehicle
            road_state = self.roads.get(nv.road_id)
            if not road_state:
                continue
                
            road_length = road_state.road.length_m
            light = self.get_road_traffic_light(nv.road_id)

            # Calculate intended movement
            distance_to_move = v.speed * time_seconds
            intended_position = v.position + distance_to_move

            # Check for Red Light / Stop Line
            if light and light.state in ("RED", "YELLOW"):
                if intended_position >= road_length or v.position >= road_length:
                    # Vehicle hits the end of the road and must wait
                    v.position = road_length
                    v.current_speed = 0.0
                    v.waiting_time += time_seconds  # Accumulate waiting time
                    continue
                else:
                    # Moving towards the red light
                    v.position = intended_position
                    v.current_speed = v.speed
                    v.waiting_time = 0.0
                    continue

            # Normal movement (Green or no light)
            v.position = intended_position
            v.current_speed = v.speed
            v.waiting_time = 0.0  # Reset waiting time if moving

            # Check if vehicle reached the end of the road
            if v.position >= road_length:
                v.position = road_length
                
                # Try routing to the next road
                if nv.next_road_id and self.route_vehicle(nv, nv.next_road_id):
                    continue  # Successfully routed
                    
                nv.completed = True  # No route, trip complete

    def step(self, time_seconds: float) -> None:
        """
        Advance the complete simulation.
        """
        if time_seconds <= 0:
            raise ValueError("time_seconds must be greater than zero.")

        self.simulation_time += time_seconds

        self.update_traffic_lights(time_seconds)
        self.update_vehicles(time_seconds)

    # =================================================================
    # METRICS PROPERTIES (Used by dashboard and visualiser)
    # =================================================================

    @property
    def total_queue_length(self) -> int:
        return sum(1 for nv in self.vehicles if not nv.completed and nv.vehicle.current_speed == 0)

    @property
    def total_vehicle_count(self) -> int:
        return len(self.vehicles)

    @property
    def active_vehicle_count(self) -> int:
        return sum(1 for nv in self.vehicles if not nv.completed)

    @property
    def total_waiting_time(self) -> float:
        return sum(nv.vehicle.waiting_time for nv in self.vehicles)

    @property
    def average_vehicle_speed(self) -> float:
        active = [nv for nv in self.vehicles if not nv.completed]
        if not active:
            return 0.0
        return sum(nv.vehicle.current_speed for nv in active) / len(active)

    @property
    def completed_vehicle_count(self) -> int:
        return sum(1 for nv in self.vehicles if nv.completed)