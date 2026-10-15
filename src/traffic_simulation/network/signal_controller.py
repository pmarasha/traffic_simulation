"""
Network Traffic Signal Controller.

Provides network-level traffic-light control without changing
the existing domain model.
"""

from dataclasses import dataclass
from typing import Dict, List

from traffic_simulation.domain.models import TrafficLight


@dataclass
class SignalGroup:
    """
    Represents a group of traffic lights operating together.
    """

    group_id: str
    light_ids: List[str]
    green_duration: float = 30.0
    yellow_duration: float = 5.0
    red_duration: float = 30.0


@dataclass
class SignalRuntime:
    """
    Runtime information for one traffic signal.

    The existing TrafficLight entity stores the current state.
    This class stores the phase-specific timing required by the
    network controller.
    """

    green_duration: float
    yellow_duration: float
    red_duration: float


class NetworkSignalController:
    """
    Controls traffic signals in the network.

    Signal cycle:

        GREEN → YELLOW → RED → GREEN

    Each phase has its own duration.
    """

    def __init__(self) -> None:
        self.traffic_lights: Dict[str, TrafficLight] = {}
        self.signal_groups: Dict[str, SignalGroup] = {}
        self.runtime: Dict[str, SignalRuntime] = {}

    # ---------------------------------------------------------
    # Traffic lights
    # ---------------------------------------------------------

    def add_light(
        self,
        light_id: str,
        initial_state: str = "RED",
        duration: int = 30,
    ) -> TrafficLight:
        """
        Register a traffic light.

        The duration argument is retained for compatibility.
        Network signal timing is controlled through SignalRuntime.
        """

        if light_id in self.traffic_lights:
            raise ValueError(
                f"Traffic light '{light_id}' already exists."
            )

        valid_states = {
            "RED",
            "YELLOW",
            "GREEN",
        }

        if initial_state not in valid_states:
            raise ValueError(
                f"Invalid traffic-light state "
                f"'{initial_state}'."
            )

        light = TrafficLight(
            light_id=len(self.traffic_lights) + 1,
            state=initial_state,
            duration=duration,
        )

        self.traffic_lights[light_id] = light

        self.runtime[light_id] = SignalRuntime(
            green_duration=float(duration),
            yellow_duration=5.0,
            red_duration=float(duration),
        )

        return light

    # ---------------------------------------------------------
    # Signal groups
    # ---------------------------------------------------------

    def add_signal_group(
        self,
        group_id: str,
        light_ids: List[str],
        green_duration: int = 30,
        yellow_duration: int = 5,
        red_duration: int = 30,
    ) -> SignalGroup:
        """
        Create a signal group.

        All lights in the group will operate together.
        """

        if group_id in self.signal_groups:
            raise ValueError(
                f"Signal group '{group_id}' already exists."
            )

        for light_id in light_ids:
            if light_id not in self.traffic_lights:
                raise KeyError(
                    f"Traffic light '{light_id}' does not exist."
                )

        group = SignalGroup(
            group_id=group_id,
            light_ids=light_ids,
            green_duration=float(green_duration),
            yellow_duration=float(yellow_duration),
            red_duration=float(red_duration),
        )

        self.signal_groups[group_id] = group

        for light_id in light_ids:
            self.runtime[light_id] = SignalRuntime(
                green_duration=float(green_duration),
                yellow_duration=float(yellow_duration),
                red_duration=float(red_duration),
            )

        return group

    # ---------------------------------------------------------
    # Signal update
    # ---------------------------------------------------------

    def update(
        self,
        time_seconds: float,
    ) -> None:
        """
        Advance every traffic signal by the specified time.

        Phase-specific durations are respected.
        """

        if time_seconds <= 0:
            raise ValueError(
                "time_seconds must be greater than zero."
            )

        for light_id, light in self.traffic_lights.items():

            runtime = self.runtime[light_id]

            light.time_in_state += time_seconds

            if light.state == "GREEN":
                duration = runtime.green_duration
                next_state = "YELLOW"

            elif light.state == "YELLOW":
                duration = runtime.yellow_duration
                next_state = "RED"

            else:
                duration = runtime.red_duration
                next_state = "GREEN"

            if light.time_in_state >= duration:
                overflow = (
                    light.time_in_state - duration
                )

                light.change_state(next_state)

                if overflow > 0:
                    self._process_overflow(
                        light,
                        runtime,
                        overflow,
                    )

    def _process_overflow(
        self,
        light: TrafficLight,
        runtime: SignalRuntime,
        overflow: float,
    ) -> None:
        """
        Handle time that crosses a signal-phase boundary.

        This allows a large simulation timestep to cross more
        than one signal phase correctly.
        """

        remaining = overflow

        while remaining > 0:

            if light.state == "GREEN":
                duration = runtime.green_duration
                next_state = "YELLOW"

            elif light.state == "YELLOW":
                duration = runtime.yellow_duration
                next_state = "RED"

            else:
                duration = runtime.red_duration
                next_state = "GREEN"

            if remaining < duration:
                light.time_in_state = remaining
                return

            remaining -= duration
            light.change_state(next_state)

    # ---------------------------------------------------------
    # Manual control
    # ---------------------------------------------------------

    def set_state(
        self,
        light_id: str,
        state: str,
    ) -> None:
        """
        Manually set a traffic-light state.
        """

        if light_id not in self.traffic_lights:
            raise KeyError(
                f"Traffic light '{light_id}' does not exist."
            )

        valid_states = {
            "RED",
            "YELLOW",
            "GREEN",
        }

        if state not in valid_states:
            raise ValueError(
                f"Invalid traffic-light state "
                f"'{state}'. Expected one of "
                f"{sorted(valid_states)}."
            )

        self.traffic_lights[
            light_id
        ].change_state(state)

    # ---------------------------------------------------------
    # Queries
    # ---------------------------------------------------------

    def get_state(
        self,
        light_id: str,
    ) -> str:
        """Return the current state of a traffic light."""

        if light_id not in self.traffic_lights:
            raise KeyError(
                f"Traffic light '{light_id}' does not exist."
            )

        return self.traffic_lights[light_id].state

    def is_green(
        self,
        light_id: str,
    ) -> bool:
        """Return True when the light is green."""

        return self.get_state(light_id) == "GREEN"

    def is_yellow(
        self,
        light_id: str,
    ) -> bool:
        """Return True when the light is yellow."""

        return self.get_state(light_id) == "YELLOW"

    def is_red(
        self,
        light_id: str,
    ) -> bool:
        """Return True when the light is red."""

        return self.get_state(light_id) == "RED"

    def get_all_states(self) -> Dict[str, str]:
        """Return the state of every traffic light."""

        return {
            light_id: light.state
            for light_id, light in self.traffic_lights.items()
        }

    # ---------------------------------------------------------
    # Reset
    # ---------------------------------------------------------

    def reset(self) -> None:
        """Reset all traffic lights to RED."""

        for light in self.traffic_lights.values():
            light.change_state("RED")