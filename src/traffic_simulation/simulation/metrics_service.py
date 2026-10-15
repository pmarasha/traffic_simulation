from traffic_simulation.domain.metrics import (
    ApproachMetrics,
    TrafficMetrics,
)
from traffic_simulation.domain.models import TrafficSystem


class MetricsService:
    """Collects traffic metrics from the simulation."""

    def collect(self, traffic_system: TrafficSystem) -> TrafficMetrics:
        metrics = TrafficMetrics()

        metrics.simulation_time = (
            traffic_system.simulation_time
        )

        for intersection in traffic_system.intersections:

            # -------------------------------------------------
            # Road approaches
            # -------------------------------------------------

            for approach in intersection.approaches:

                approach_metrics = ApproachMetrics(
                    road_name=approach.road_name,
                    traffic_volume=approach.traffic_volume,
                    queue_length=approach.queue_length,
                )

                # Traffic light state
                if approach.traffic_light is not None:
                    approach_metrics.signal_state = (
                        approach.traffic_light.state
                    )

                # Waiting time
                approach_metrics.total_waiting_time = sum(
                    vehicle.waiting_time
                    for vehicle in approach.vehicles
                )

                approach_metrics.calculate_average_waiting_time()

                metrics.approach_metrics[
                    approach.road_name
                ] = approach_metrics

                metrics.total_vehicles += (
                    approach_metrics.traffic_volume
                )

                metrics.total_queue_length += (
                    approach_metrics.queue_length
                )

                metrics.total_waiting_time += (
                    approach_metrics.total_waiting_time
                )

            # -------------------------------------------------
            # Backward compatibility:
            # vehicles directly attached to intersections
            # -------------------------------------------------

            if not intersection.approaches:

                metrics.total_vehicles += len(
                    intersection.vehicles
                )

                metrics.total_waiting_time += sum(
                    vehicle.waiting_time
                    for vehicle in intersection.vehicles
                )

        metrics.calculate_average_waiting_time()

        metrics.congestion_level = (
            self.calculate_congestion_level(metrics)
        )

        return metrics

    def calculate_congestion_level(
        self,
        metrics: TrafficMetrics,
    ) -> str:

        if metrics.total_queue_length == 0:
            return "LOW"

        if metrics.total_queue_length <= 3:
            return "MODERATE"

        if metrics.total_queue_length <= 6:
            return "HIGH"

        return "SEVERE"