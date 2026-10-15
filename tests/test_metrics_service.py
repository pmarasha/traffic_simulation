from traffic_simulation.domain.metrics import (
    ApproachMetrics,
    TrafficMetrics,
)
from traffic_simulation.domain.models import (
    Intersection,
    RoadApproach,
    TrafficLight,
    TrafficSystem,
    TrafficVehicle,
)
from traffic_simulation.simulation.metrics_service import (
    MetricsService,
)


def create_test_traffic_system():
    """Create a small traffic system for testing metrics."""

    traffic_system = TrafficSystem()

    intersection = Intersection(
        intersection_id=1,
        name="Test Intersection",
    )

    traffic_light = TrafficLight(
        light_id=1,
        state="RED",
        duration=30,
    )

    approach = RoadApproach(
        approach_id=1,
        road_name="Test Road",
        direction="north",
        stop_position=100.0,
        traffic_light=traffic_light,
    )

    approach.add_vehicle(
        TrafficVehicle(
            vehicle_id=1,
            speed=10,
            position=100,
            vehicle_type="car",
            waiting_time=10,
        )
    )

    approach.add_vehicle(
        TrafficVehicle(
            vehicle_id=2,
            speed=8,
            position=100,
            vehicle_type="combi",
            waiting_time=5,
        )
    )

    approach.add_vehicle(
        TrafficVehicle(
            vehicle_id=3,
            speed=12,
            position=50,
            vehicle_type="truck",
            waiting_time=0,
        )
    )

    intersection.add_traffic_light(traffic_light)
    intersection.add_approach(approach)

    traffic_system.add_intersection(intersection)

    return traffic_system


def test_metrics_service_returns_traffic_metrics():
    """MetricsService should return a TrafficMetrics object."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    assert isinstance(metrics, TrafficMetrics)


def test_total_vehicle_count():
    """Metrics should correctly count all vehicles."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    assert metrics.total_vehicles == 3


def test_queue_length():
    """Metrics should correctly calculate the queue length."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    assert metrics.total_queue_length == 2


def test_total_waiting_time():
    """Metrics should calculate total waiting time."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    assert metrics.total_waiting_time == 15


def test_average_waiting_time():
    """Metrics should calculate average waiting time."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    assert metrics.average_waiting_time == 5


def test_approach_metrics_are_created():
    """Metrics should contain data for each road approach."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    assert "Test Road" in metrics.approach_metrics

    approach_metrics = metrics.approach_metrics["Test Road"]

    assert isinstance(
        approach_metrics,
        ApproachMetrics,
    )


def test_approach_vehicle_count():
    """Approach metrics should contain vehicle count."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    approach_metrics = metrics.approach_metrics["Test Road"]

    assert approach_metrics.traffic_volume == 3


def test_approach_queue_length():
    """Approach metrics should contain queue length."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    approach_metrics = metrics.approach_metrics["Test Road"]

    assert approach_metrics.queue_length == 2


def test_signal_state():
    """Approach metrics should contain the traffic-light state."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    approach_metrics = metrics.approach_metrics["Test Road"]

    assert approach_metrics.signal_state == "RED"


def test_approach_waiting_time():
    """Approach metrics should contain total waiting time."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    approach_metrics = metrics.approach_metrics["Test Road"]

    assert approach_metrics.total_waiting_time == 15


def test_approach_average_waiting_time():
    """Approach metrics should calculate average waiting time."""

    traffic_system = create_test_traffic_system()

    service = MetricsService()

    metrics = service.collect(traffic_system)

    approach_metrics = metrics.approach_metrics["Test Road"]

    assert approach_metrics.average_waiting_time == 5


def test_low_congestion():
    """No queued vehicles should result in LOW congestion."""

    metrics = TrafficMetrics(
        total_queue_length=0,
    )

    service = MetricsService()

    congestion = service.calculate_congestion_level(metrics)

    assert congestion == "LOW"


def test_moderate_congestion():
    """Small queues should result in MODERATE congestion."""

    metrics = TrafficMetrics(
        total_queue_length=3,
    )

    service = MetricsService()

    congestion = service.calculate_congestion_level(metrics)

    assert congestion == "MODERATE"


def test_high_congestion():
    """Larger queues should result in HIGH congestion."""

    metrics = TrafficMetrics(
        total_queue_length=6,
    )

    service = MetricsService()

    congestion = service.calculate_congestion_level(metrics)

    assert congestion == "HIGH"


def test_severe_congestion():
    """Very large queues should result in SEVERE congestion."""

    metrics = TrafficMetrics(
        total_queue_length=7,
    )

    service = MetricsService()

    congestion = service.calculate_congestion_level(metrics)

    assert congestion == "SEVERE"


def test_simulation_time_is_captured():
    """Metrics should capture the current simulation time."""

    traffic_system = create_test_traffic_system()

    traffic_system.simulation_time = 25.0

    service = MetricsService()

    metrics = service.collect(traffic_system)

    assert metrics.simulation_time == 25.0