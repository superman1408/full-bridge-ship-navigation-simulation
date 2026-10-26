"""Unit tests for the educational ship berthing simulator physics."""
import importlib.util
import math
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("ship_berthing_simulator.py")
spec = importlib.util.spec_from_file_location("ship_berthing_simulator", MODULE_PATH)
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)


def neutral_settings():
    return {
        "wind_kn": 0.0, "wind_dir_deg": 0.0,
        "current_kn": 0.0, "current_dir_deg": 0.0,
        "bow_tug_kn": 0.0, "bow_tug_angle_deg": 0.0,
        "stern_tug_kn": 0.0, "stern_tug_angle_deg": 0.0,
        "wave_force_kn": 0.0, "wave_period_s": 8.0,
        "wave_dir_deg": 0.0, "propulsion_kn": 0.0,
    }


class PhysicsTests(unittest.TestCase):
    def setUp(self):
        self.ship = sim.ShipModel()
        self.ship.u = 0.0
        self.ship.v = 0.0
        self.ship.r = 0.0
        self.ship.psi = 0.0

    def test_world_body_round_trip(self):
        vec = (3.2, -7.1)
        body = sim.world_to_body(*vec, 0.73)
        world = sim.body_to_world(*body, 0.73)
        self.assertAlmostEqual(world[0], vec[0], places=10)
        self.assertAlmostEqual(world[1], vec[1], places=10)

    def test_no_inputs_no_force_when_stationary_in_still_water(self):
        X, Y, N, _ = self.ship.calculate_forces(neutral_settings(), 0.0)
        self.assertAlmostEqual(X, 0.0, places=8)
        self.assertAlmostEqual(Y, 0.0, places=8)
        self.assertAlmostEqual(N, 0.0, places=8)

    def test_eastward_wind_pushes_east_in_this_drag_approximation(self):
        settings = neutral_settings()
        settings.update(wind_kn=10.0, wind_dir_deg=0.0)
        _, _, _, f = self.ship.calculate_forces(settings, 0.0)
        self.assertGreater(f["X_wind"], 0.0)
        self.assertAlmostEqual(f["Y_wind"], 0.0, places=8)

    def test_northward_wind_pushes_toward_port_when_heading_east(self):
        settings = neutral_settings()
        settings.update(wind_kn=10.0, wind_dir_deg=90.0)
        _, _, _, f = self.ship.calculate_forces(settings, 0.0)
        self.assertAlmostEqual(f["X_wind"], 0.0, delta=1e-6)
        self.assertGreater(f["Y_wind"], 0.0)

    def test_bow_tug_port_force_creates_positive_yaw_moment(self):
        settings = neutral_settings()
        settings.update(bow_tug_kn=100.0, bow_tug_angle_deg=90.0)
        _, Y, N, f = self.ship.calculate_forces(settings, 0.0)
        self.assertAlmostEqual(Y, 100_000.0, delta=1e-6)
        self.assertGreater(N, 0.0)
        self.assertAlmostEqual(N, 0.40 * self.ship.length * 100_000.0, delta=1e-6)

    def test_equal_port_tugs_at_bow_and_stern_cancel_yaw_moment(self):
        settings = neutral_settings()
        settings.update(bow_tug_kn=100.0, bow_tug_angle_deg=90.0,
                        stern_tug_kn=100.0, stern_tug_angle_deg=90.0)
        _, Y, N, _ = self.ship.calculate_forces(settings, 0.0)
        self.assertAlmostEqual(Y, 200_000.0, delta=1e-6)
        self.assertAlmostEqual(N, 0.0, delta=1e-6)

    def test_uniform_current_changes_ground_motion_not_water_relative_hull_load(self):
        settings = neutral_settings()
        settings.update(current_kn=1.0, current_dir_deg=0.0)
        _, _, _, f = self.ship.calculate_forces(settings, 0.0)
        # u/v are defined relative to the water, so a ship with u=0 has no
        # water-relative hull damping even when the water itself is moving.
        self.assertAlmostEqual(f["water_rel_u"], 0.0, places=6)
        self.assertAlmostEqual(f["X_hydro"], 0.0, places=6)
        self.assertAlmostEqual(f["ship_ground_u_body"], sim.KNOT_TO_MPS, places=6)
        # Position integration should carry the stationary-in-water ship with
        # the current, rather than counting the current as a fictitious force.
        x_before = self.ship.x
        self.ship.step(settings, 0.01)
        self.assertGreater(self.ship.x, x_before)

    def test_resultant_is_vector_magnitude(self):
        settings = neutral_settings()
        settings.update(bow_tug_kn=100.0, bow_tug_angle_deg=0.0,
                        stern_tug_kn=100.0, stern_tug_angle_deg=90.0)
        X, Y, _, _ = self.ship.calculate_forces(settings, 0.0)
        self.assertAlmostEqual(math.hypot(X, Y), math.hypot(100_000.0, 100_000.0), delta=1e-6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
