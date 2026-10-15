from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================
# TRAFFIC VEHICLE
# ============================================================

@dataclass
class TrafficVehicle:
    vehicle_id: int
    speed: float
    position: float = 0.0
    vehicle_type: str = "car"
    direction: str = "straight"
    stop_position: float = 100.0
    waiting_time: float = 0.0
    length: float = 5.0
    minimum_gap: float = 5.0
    current_speed: float = 0.0

    def __post_init__(self):
        self.current_speed = self.speed

    @property
    def speed_mps(self) -> float:
        return self.speed

    @property
    def current_speed_mps(self) -> float:
        return self.current_speed

    def move(
        self,
        duration: float,
        traffic_light: Optional["TrafficLight"] = None,
    ) -> None:
        if duration < 0:
            raise ValueError("Duration cannot be negative")

        # Once past the stop line, free-flow at full speed.
        if self.position > self.stop_position:
            self.resume()
            self.position += self.current_speed * duration
            return

        # Obey the light.
        if traffic_light is not None and traffic_light.state in ("RED", "YELLOW"):
            projected = self.position + self.speed * duration
            if projected >= self.stop_position:
                self.position = self.stop_position
                self.stop()
                self.update_waiting_time(duration)
                return

        # GREEN or no light.
        self.resume()
        self.position += self.current_speed * duration

    def stop(self) -> None:
        self.current_speed = 0.0

    def resume(self) -> None:
        self.current_speed = self.speed

    def update_waiting_time(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("Duration cannot be negative")
        self.waiting_time += duration


# ============================================================
# ROAD
# ============================================================

@dataclass
class Road:
    road_id: str
    name: str
    length: float
    speed_limit: float
    start_intersection: Optional[str] = None
    end_intersection: Optional[str] = None


# ============================================================
# TRAFFIC LIGHT
# ============================================================

@dataclass
class TrafficLight:
    light_id: int
    state: str = "RED"
    duration: float = 30.0
    timer: float = 0.0
    time_in_state: float = 0.0

    def __post_init__(self):
        self.time_in_state = self.timer

    def update(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("Duration cannot be negative")

        self.timer += duration
        self.time_in_state = self.timer

        if self.timer >= self.duration:
            self.change_state()

    def change_state(self, new_state: Optional[str] = None) -> None:
        if new_state is not None:
            self.state = new_state.upper()
        else:
            if self.state == "RED":
                self.state = "GREEN"
            elif self.state == "GREEN":
                self.state = "YELLOW"
            elif self.state == "YELLOW":
                self.state = "RED"
            else:
                raise ValueError(f"Invalid traffic light state: {self.state}")

        self.timer = 0.0
        self.time_in_state = 0.0

    def is_green(self) -> bool:
        return self.state == "GREEN"

    def is_red(self) -> bool:
        return self.state == "RED"

    def is_yellow(self) -> bool:
        return self.state == "YELLOW"


# ============================================================
# ROAD APPROACH
# ============================================================

@dataclass
class RoadApproach:
    approach_id: int
    road_name: str
    direction: str
    stop_position: float = 100.0
    traffic_light: Optional[TrafficLight] = None
    vehicles: List[TrafficVehicle] = field(default_factory=list)

    @property
    def traffic_volume(self) -> int:
        return len(self.vehicles)

    @property
    def queue_length(self) -> int:
        if self.traffic_light is None:
            return 0
        if self.traffic_light.state not in ("RED", "YELLOW"):
            return 0

        queue = 0
        for vehicle in self.vehicles:
            if (vehicle.position >= self.stop_position
                    or vehicle.waiting_time > 0):
                queue += 1
        return queue

    def add_traffic_light(self, traffic_light: TrafficLight) -> None:
        self.traffic_light = traffic_light

    def add_vehicle(self, vehicle: TrafficVehicle) -> None:
        vehicle.direction = self.direction
        vehicle.stop_position = self.stop_position
        self.vehicles.append(vehicle)

    def update(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("Duration cannot be negative")
        for vehicle in self.vehicles:
            vehicle.move(duration, self.traffic_light)


# ============================================================
# INTERSECTION
# ============================================================

@dataclass
class Intersection:
    intersection_id: int
    name: str
    approaches: List[RoadApproach] = field(default_factory=list)
    traffic_lights: List[TrafficLight] = field(default_factory=list)
    vehicles: List[TrafficVehicle] = field(default_factory=list)

    def add_traffic_light(self, traffic_light: TrafficLight) -> None:
        self.traffic_lights.append(traffic_light)

    def add_approach(self, approach: RoadApproach) -> None:
        self.approaches.append(approach)

    def add_road_approach(self, approach: RoadApproach) -> None:
        self.add_approach(approach)

    def add_vehicle(
        self,
        vehicle: TrafficVehicle,
        approach: Optional[RoadApproach] = None,
    ) -> None:
        self.vehicles.append(vehicle)
        if approach is not None:
            approach.add_vehicle(vehicle)

    def update(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("Duration cannot be negative")

        for traffic_light in self.traffic_lights:
            traffic_light.update(duration)

        approach_vehicle_ids = set()
        for approach in self.approaches:
            for vehicle in approach.vehicles:
                approach_vehicle_ids.add(id(vehicle))

        for vehicle in self.vehicles:
            if id(vehicle) not in approach_vehicle_ids:
                traffic_light = (
                    self.traffic_lights[0] if self.traffic_lights else None
                )
                vehicle.move(duration, traffic_light)

        for approach in self.approaches:
            approach.update(duration)


# ============================================================
# TRAFFIC SYSTEM
# ============================================================

@dataclass
class TrafficSystem:
    intersections: List[Intersection] = field(default_factory=list)
    simulation_time: float = 0.0

    # Traffic generator knobs
    spawn_rate: float = 0.3
    road_length: float = 300.0
    _next_vehicle_id: int = 1000

    def add_intersection(self, intersection: Intersection) -> None:
        self.intersections.append(intersection)

    def update(self, duration: float) -> None:
        if duration < 0:
            raise ValueError("Duration cannot be negative")

        for intersection in self.intersections:
            intersection.update(duration)

        self._spawn_vehicles()
        self._remove_exited_vehicles()

        self.simulation_time += duration

    def _spawn_vehicles(self) -> None:
        import random
        for intersection in self.intersections:
            if not intersection.approaches:
                continue
            for approach in intersection.approaches:
                if random.random() < self.spawn_rate:
                    self._next_vehicle_id += 1
                    vehicle = TrafficVehicle(
                        vehicle_id=self._next_vehicle_id,
                        speed=random.uniform(8.0, 16.0),
                        position=0.0,
                    )
                    approach.add_vehicle(vehicle)

    def _remove_exited_vehicles(self) -> None:
        for intersection in self.intersections:
            intersection.vehicles = [
                v for v in intersection.vehicles
                if v.position < self.road_length
            ]
            for approach in intersection.approaches:
                approach.vehicles = [
                    v for v in approach.vehicles
                    if v.position < self.road_length
                ]