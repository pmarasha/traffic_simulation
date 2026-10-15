"""
Tests for the network traffic signal controller.

These tests verify:
    - traffic-light registration
    - GREEN timing
    - YELLOW timing
    - RED timing
    - complete signal cycles
    - signal groups
    - manual state changes
    - invalid states
    - reset behavior
"""


import pytest

from traffic_simulation.network.signal_controller import (
    NetworkSignalController,
)


# ---------------------------------------------------------
# Traffic light creation
# ---------------------------------------------------------


def test_add_traffic_light():
    controller = NetworkSignalController()

    light = controller.add_light(
        "MAIN-LIGHT",
        initial_state="GREEN",
        duration=30,
    )

    assert light.state == "GREEN"
    assert controller.get_state("MAIN-LIGHT") == "GREEN"


def test_duplicate_traffic_light_is_rejected():
    controller = NetworkSignalController()

    controller.add_light("MAIN-LIGHT")

    with pytest.raises(ValueError):
        controller.add_light("MAIN-LIGHT")


def test_invalid_initial_state_is_rejected():
    controller = NetworkSignalController()

    with pytest.raises(ValueError):
        controller.add_light(
            "MAIN-LIGHT",
            initial_state="BLUE",
        )


# ---------------------------------------------------------
# GREEN phase
# ---------------------------------------------------------


def test_green_phase_lasts_thirty_seconds():
    controller = NetworkSignalController()

    controller.add_light(
        "MAIN-LIGHT",
        initial_state="GREEN",
        duration=30,
    )

    controller.update(29)

    assert controller.get_state("MAIN-LIGHT") == "GREEN"

    controller.update(1)

    assert controller.get_state("MAIN-LIGHT") == "YELLOW"


# ---------------------------------------------------------
# YELLOW phase
# ---------------------------------------------------------


def test_yellow_phase_lasts_five_seconds():
    controller = NetworkSignalController()

    controller.add_light(
        "MAIN-LIGHT",
        initial_state="GREEN",
        duration=30,
    )

    controller.update(30)

    assert controller.get_state("MAIN-LIGHT") == "YELLOW"

    controller.update(4)

    assert controller.get_state("MAIN-LIGHT") == "YELLOW"

    controller.update(1)

    assert controller.get_state("MAIN-LIGHT") == "RED"


# ---------------------------------------------------------
# RED phase
# ---------------------------------------------------------


def test_red_phase_lasts_thirty_seconds():
    controller = NetworkSignalController()

    controller.add_light(
        "MAIN-LIGHT",
        initial_state="GREEN",
        duration=30,
    )

    controller.update(30)
    controller.update(5)

    assert controller.get_state("MAIN-LIGHT") == "RED"

    controller.update(29)

    assert controller.get_state("MAIN-LIGHT") == "RED"

    controller.update(1)

    assert controller.get_state("MAIN-LIGHT") == "GREEN"


# ---------------------------------------------------------
# Complete signal cycle
# ---------------------------------------------------------


def test_complete_signal_cycle_is_thirty_five_seconds_to_red():
    controller = NetworkSignalController()

    controller.add_light(
        "MAIN-LIGHT",
        initial_state="GREEN",
        duration=30,
    )

    controller.update(30)

    assert controller.get_state("MAIN-LIGHT") == "YELLOW"

    controller.update(5)

    assert controller.get_state("MAIN-LIGHT") == "RED"


def test_complete_signal_cycle_returns_to_green():
    controller = NetworkSignalController()

    controller.add_light(
        "MAIN-LIGHT",
        initial_state="GREEN",
        duration=30,
    )

    controller.update(65)

    assert controller.get_state("MAIN-LIGHT") == "GREEN"


# ---------------------------------------------------------
# Signal groups
# ---------------------------------------------------------


def test_signal_group_controls_multiple_lights():
    controller = NetworkSignalController()

    controller.add_light(
        "NORTH-LIGHT",
        initial_state="GREEN",
        duration=30,
    )

    controller.add_light(
        "SOUTH-LIGHT",
        initial_state="GREEN",
        duration=30,
    )

    controller.add_signal_group(
        "NORTH-SOUTH",
        [
            "NORTH-LIGHT",
            "SOUTH-LIGHT",
        ],
        green_duration=30,
        yellow_duration=5,
        red_duration=30,
    )

    controller.update(30)

    assert controller.get_state("NORTH-LIGHT") == "YELLOW"
    assert controller.get_state("SOUTH-LIGHT") == "YELLOW"

    controller.update(5)

    assert controller.get_state("NORTH-LIGHT") == "RED"
    assert controller.get_state("SOUTH-LIGHT") == "RED"


def test_duplicate_signal_group_is_rejected():
    controller = NetworkSignalController()

    controller.add_light("LIGHT-1")

    controller.add_signal_group(
        "GROUP-1",
        ["LIGHT-1"],
    )

    with pytest.raises(ValueError):
        controller.add_signal_group(
            "GROUP-1",
            ["LIGHT-1"],
        )


def test_signal_group_requires_existing_lights():
    controller = NetworkSignalController()

    with pytest.raises(KeyError):
        controller.add_signal_group(
            "GROUP-1",
            ["MISSING-LIGHT"],
        )


# ---------------------------------------------------------
# State helpers
# ---------------------------------------------------------


def test_is_green():
    controller = NetworkSignalController()

    controller.add_light(
        "LIGHT-1",
        initial_state="GREEN",
    )

    assert controller.is_green("LIGHT-1") is True
    assert controller.is_yellow("LIGHT-1") is False
    assert controller.is_red("LIGHT-1") is False


def test_is_yellow():
    controller = NetworkSignalController()

    controller.add_light(
        "LIGHT-1",
        initial_state="GREEN",
        duration=30,
    )

    controller.update(30)

    assert controller.is_green("LIGHT-1") is False
    assert controller.is_yellow("LIGHT-1") is True
    assert controller.is_red("LIGHT-1") is False


def test_is_red():
    controller = NetworkSignalController()

    controller.add_light(
        "LIGHT-1",
        initial_state="GREEN",
        duration=30,
    )

    controller.update(35)

    assert controller.is_green("LIGHT-1") is False
    assert controller.is_yellow("LIGHT-1") is False
    assert controller.is_red("LIGHT-1") is True


def test_get_all_states():
    controller = NetworkSignalController()

    controller.add_light(
        "LIGHT-1",
        initial_state="GREEN",
    )

    controller.add_light(
        "LIGHT-2",
        initial_state="RED",
    )

    states = controller.get_all_states()

    assert states == {
        "LIGHT-1": "GREEN",
        "LIGHT-2": "RED",
    }


# ---------------------------------------------------------
# Manual state changes
# ---------------------------------------------------------


def test_manual_state_change():
    controller = NetworkSignalController()

    controller.add_light(
        "LIGHT-1",
        initial_state="RED",
    )

    controller.set_state(
        "LIGHT-1",
        "GREEN",
    )

    assert controller.get_state("LIGHT-1") == "GREEN"


def test_invalid_manual_state_is_rejected():
    controller = NetworkSignalController()

    controller.add_light("LIGHT-1")

    with pytest.raises(ValueError):
        controller.set_state(
            "LIGHT-1",
            "BLUE",
        )


# ---------------------------------------------------------
# Invalid operations
# ---------------------------------------------------------


def test_missing_light_state_raises_error():
    controller = NetworkSignalController()

    with pytest.raises(KeyError):
        controller.get_state("MISSING-LIGHT")


def test_missing_light_green_check_raises_error():
    controller = NetworkSignalController()

    with pytest.raises(KeyError):
        controller.is_green("MISSING-LIGHT")


def test_update_requires_positive_time():
    controller = NetworkSignalController()

    controller.add_light("LIGHT-1")

    with pytest.raises(ValueError):
        controller.update(0)

    with pytest.raises(ValueError):
        controller.update(-1)


# ---------------------------------------------------------
# Reset
# ---------------------------------------------------------


def test_reset_returns_all_lights_to_red():
    controller = NetworkSignalController()

    controller.add_light(
        "LIGHT-1",
        initial_state="GREEN",
    )

    controller.add_light(
        "LIGHT-2",
        initial_state="YELLOW",
    )

    controller.reset()

    assert controller.get_state("LIGHT-1") == "RED"
    assert controller.get_state("LIGHT-2") == "RED"


# ---------------------------------------------------------
# Large timestep handling
# ---------------------------------------------------------


def test_large_timestep_processes_multiple_phases():
    controller = NetworkSignalController()

    controller.add_light(
        "LIGHT-1",
        initial_state="GREEN",
        duration=30,
    )

    controller.update(65)

    assert controller.get_state("LIGHT-1") == "GREEN"
    assert (
        controller.traffic_lights[
            "LIGHT-1"
        ].time_in_state
        == 0
    )