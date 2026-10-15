import time

from traffic_simulation.domain.models import TrafficSystem


class SimulationEngine:
    def __init__(self, traffic_system: TrafficSystem, time_step: float = 1.0):
        self.traffic_system = traffic_system
        self.time_step = time_step
        self.running = False

    def step(self) -> None:
        self.traffic_system.update(self.time_step)

    def start(self, steps: int = 10, delay: float = 0.1) -> None:
        self.running = True

        for _ in range(steps):
            if not self.running:
                break

            self.step()

            time.sleep(delay)

        self.running = False

    def stop(self) -> None:
        self.running = False