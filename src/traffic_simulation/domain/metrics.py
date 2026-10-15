from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ApproachMetrics:
    road_name: str
    traffic_volume: int = 0
    queue_length: int = 0
    total_waiting_time: float = 0.0
    average_waiting_time: float = 0.0
    signal_state: str = "UNKNOWN"

    def calculate_average_waiting_time(self) -> None:
        if self.traffic_volume > 0:
            self.average_waiting_time = (
                self.total_waiting_time / self.traffic_volume
            )
        else:
            self.average_waiting_time = 0.0


@dataclass
class TrafficMetrics:
    simulation_time: float = 0.0
    total_vehicles: int = 0
    total_queue_length: int = 0
    total_waiting_time: float = 0.0
    average_waiting_time: float = 0.0
    throughput: int = 0
    congestion_level: str = "LOW"
    approach_metrics: Dict[str, ApproachMetrics] = field(
        default_factory=dict
    )

    def calculate_average_waiting_time(self) -> None:
        if self.total_vehicles > 0:
            self.average_waiting_time = (
                self.total_waiting_time / self.total_vehicles
            )
        else:
            self.average_waiting_time = 0.0