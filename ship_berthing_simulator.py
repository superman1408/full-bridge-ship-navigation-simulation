"""
Ship Berthing Simulator — educational 3-DOF model
Python 3.x, standard library only (Tkinter).

Run:
    python ship_berthing_simulator.py

Coordinate conventions:
- World X = east, world Y = north.
- Heading psi is measured counter-clockwise from world +X.
- Body x = forward, body y = port.
- Wind/current directions are the direction TOWARD which they flow, in world degrees.
- Tug angle is relative to the ship's forward axis; positive means toward port.

IMPORTANT:
This is a training prototype, not an operational navigation tool. Coefficients are
illustrative. Validate vessel-specific added mass, damping, wind coefficients,
tug curves, wave loads, shallow-water/bank effects and port geometry before any
engineering or operational use. The wave term is a simple disturbance, not a
validated seakeeping or wave-load model.
"""

import math
import tkinter as tk
from tkinter import ttk

# ----------------------- Unit conversions -----------------------

KNOT_TO_MPS = 0.514444
TONNE_FORCE_TO_N = 1000.0 * 9.80665
DEG = math.pi / 180.0


def clamp(value, low, high):
    return max(low, min(high, value))


def wrap_angle(angle):
    """Return angle in radians in [-pi, pi)."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def world_to_body(x_world, y_world, heading):
    """Rotate a world-frame vector into body axes (forward, port)."""
    c, s = math.cos(heading), math.sin(heading)
    return c * x_world + s * y_world, -s * x_world + c * y_world


def body_to_world(x_body, y_body, heading):
    """Rotate a body-frame vector into world axes (east, north)."""
    c, s = math.cos(heading), math.sin(heading)
    return c * x_body - s * y_body, s * x_body + c * y_body


# ----------------------- Ship physics ---------------------------

class ShipModel:
    """
    Simplified horizontal-plane 3-DOF manoeuvring model.

    State velocities u, v are body-axis velocities relative to the WATER:
      u: surge (m/s), positive forward
      v: sway (m/s), positive port
      r: yaw rate (rad/s), positive counter-clockwise

    For a uniform current, ground velocity is water-relative ship velocity
    plus current velocity. This convention is used consistently for both
    hydrodynamic loads and position integration.
    Simplified rigid-body/added-mass equations:
      mx * du/dt = X + m * v * r
      my * dv/dt = Y - m * u * r
      Iz_eff * dr/dt = N

    The Coriolis terms use rigid-body mass m; mx and my include simplified
    added mass. Hydrodynamic damping uses water-relative velocity.
    """

    def __init__(self):
        # Illustrative 20,000-tonne tanker-like training vessel.
        # Replace these values with vessel-specific data for serious use.
        self.mass = 20_000_000.0       # kg
        self.length = 180.0            # m
        self.beam = 30.0               # m
        self.draft = 10.0              # m

        # Approximate added-mass factors. These are NOT universal constants.
        self.mx = 1.05 * self.mass
        self.my = 1.80 * self.mass
        self.Iz = self.mass * (0.25 * self.length) ** 2 * 1.20

        # Windage area estimates (must be replaced with vessel data).
        self.wind_area_side = 1800.0   # m^2
        self.wind_area_front = 450.0   # m^2
        self.wind_cd_side = 1.0
        self.wind_cd_front = 0.8
        self.rho_air = 1.225           # kg/m^3

        # Water density and illustrative hull resistance coefficients.
        self.rho_water = 1025.0        # kg/m^3
        self.X_linear = 2.0e5          # N/(m/s)
        self.X_quad = 1.0e5            # N/(m/s)^2
        self.Y_linear = 8.0e5          # N/(m/s)
        self.Y_quad = 2.0e6            # N/(m/s)^2
        self.N_linear = 8.0e8          # N m/(rad/s)
        self.N_quad = 1.0e9            # N m/(rad/s)^2

        self.reset()

    def reset(self):
        self.x = -220.0                # m, world east; start before target berth
        self.y = 0.0                   # m, world north
        self.psi = 0.0                 # rad, bow points east
        self.u = 2.5 * KNOT_TO_MPS     # m/s, water-relative body x
        self.v = 0.0                   # m/s, water-relative body y (port)
        self.r = 0.0                   # rad/s
        self.elapsed = 0.0
        self.last_forces = {}

    def calculate_forces(self, settings, t):
        """
        Return body-frame forces (X, Y, N) in N, N, N*m.

        Wind and current settings use world-frame direction TOWARD which
        the air/water moves. Tug angles are relative to the ship's forward axis.
        """
        # Current velocity in world coordinates, then body coordinates.
        current_speed = settings["current_kn"] * KNOT_TO_MPS
        current_dir = settings["current_dir_deg"] * DEG
        current_x = current_speed * math.cos(current_dir)
        current_y = current_speed * math.sin(current_dir)
        current_u_body, current_v_body = world_to_body(
            current_x, current_y, self.psi
        )

        # State u/v are water-relative. Convert to ground velocity by adding
        # the current exactly once; this is used for wind and position updates.
        water_rel_u = self.u
        water_rel_v = self.v
        water_ship_x, water_ship_y = body_to_world(self.u, self.v, self.psi)
        current_x, current_y = body_to_world(
            current_u_body, current_v_body, self.psi
        )
        ship_ground_x = water_ship_x + current_x
        ship_ground_y = water_ship_y + current_y
        ground_u_body = self.u + current_u_body
        ground_v_body = self.v + current_v_body

        # Relative wind = wind velocity - ship ground velocity, in world coordinates.
        wind_speed = settings["wind_kn"] * KNOT_TO_MPS
        wind_dir = settings["wind_dir_deg"] * DEG
        wind_x = wind_speed * math.cos(wind_dir)
        wind_y = wind_speed * math.sin(wind_dir)
        rel_wind_x = wind_x - ship_ground_x
        rel_wind_y = wind_y - ship_ground_y
        wind_u, wind_v = world_to_body(rel_wind_x, rel_wind_y, self.psi)

        # Component-wise quadratic wind drag opposing relative airflow.
        # This simplified projected-area model does not include detailed
        # superstructure geometry or direction-dependent coefficients.
        X_wind = 0.5 * self.rho_air * self.wind_cd_front * self.wind_area_front \
            * abs(wind_u) * wind_u
        Y_wind = 0.5 * self.rho_air * self.wind_cd_side * self.wind_area_side \
            * abs(wind_v) * wind_v

        # Water-relative hydrodynamic resistance / damping.
        # These coefficients are illustrative, not calibrated ship data.
        X_hydro = -(self.X_linear * water_rel_u + self.X_quad * abs(water_rel_u) * water_rel_u)
        Y_hydro = -(self.Y_linear * water_rel_v + self.Y_quad * abs(water_rel_v) * water_rel_v)
        N_hydro = -(self.N_linear * self.r + self.N_quad * abs(self.r) * self.r)

        # Tug forces. Force magnitudes are entered in kN; angles are relative
        # to forward axis. Bow/stern positions create yaw moments.
        X_tug = Y_tug = N_tug = 0.0
        tug_records = []
        for name in ("bow", "stern"):
            magnitude = settings[f"{name}_tug_kn"] * 1000.0
            angle = settings[f"{name}_tug_angle_deg"] * DEG
            tx = magnitude * math.cos(angle)
            ty = magnitude * math.sin(angle)
            x_pos = (0.40 * self.length) if name == "bow" else (-0.40 * self.length)
            y_pos = 0.0
            moment = x_pos * ty - y_pos * tx
            X_tug += tx
            Y_tug += ty
            N_tug += moment
            tug_records.append((name, tx, ty, moment))

        # Simple optional wave disturbance for demonstration only.
        # Not a substitute for diffraction/radiation or validated wave-load data.
        wave_amp = settings["wave_force_kn"] * 1000.0
        wave_period = max(2.0, settings["wave_period_s"])
        wave_dir = settings["wave_dir_deg"] * DEG
        wave_phase = 2.0 * math.pi * t / wave_period
        X_wave = wave_amp * math.cos(wave_dir) * math.sin(wave_phase)
        Y_wave = wave_amp * math.sin(wave_dir) * math.sin(wave_phase)
        X_wave, Y_wave = world_to_body(X_wave, Y_wave, self.psi)
        N_wave = 0.0  # no wave yaw moment modelled here

        # Optional simple longitudinal propulsion/braking input.
        X_prop = settings["propulsion_kn"] * 1000.0
        Y_prop = 0.0
        N_prop = 0.0

        X = X_wind + X_hydro + X_tug + X_wave + X_prop
        Y = Y_wind + Y_hydro + Y_tug + Y_wave + Y_prop
        N = N_hydro + N_tug + N_wave + N_prop

        details = {
            "X_wind": X_wind, "Y_wind": Y_wind,
            "X_hydro": X_hydro, "Y_hydro": Y_hydro, "N_hydro": N_hydro,
            "X_tug": X_tug, "Y_tug": Y_tug, "N_tug": N_tug,
            "X_wave": X_wave, "Y_wave": Y_wave,
            "X_prop": X_prop,
            "X_total": X, "Y_total": Y, "N_total": N,
            "current_u_body": current_u_body,
            "current_v_body": current_v_body,
            "water_rel_u": water_rel_u,
            "water_rel_v": water_rel_v,
            "ship_ground_u_body": ground_u_body,
            "ship_ground_v_body": ground_v_body,
            "ship_ground_x": ship_ground_x,
            "ship_ground_y": ship_ground_y,
            "tug_records": tug_records,
        }
        self.last_forces = details
        return X, Y, N, details

    def step(self, settings, dt):
        """Advance the model by dt seconds using semi-implicit Euler integration."""
        dt = clamp(dt, 0.001, 0.05)
        X, Y, N, details = self.calculate_forces(settings, self.elapsed)

        # 3-DOF equations: inertial coupling uses rigid-body mass; effective
        # surge/sway masses include the simplified added-mass estimates.
        du = (X + self.mass * self.v * self.r) / self.mx
        dv = (Y - self.mass * self.u * self.r) / self.my
        dr = N / self.Iz

        # Integrate rates -> velocities.
        self.u += du * dt
        self.v += dv * dt
        self.r += dr * dt

        # Prevent numerical runaway in this demonstration application.
        self.u = clamp(self.u, -5.0, 5.0)
        self.v = clamp(self.v, -3.0, 3.0)
        self.r = clamp(self.r, -0.15, 0.15)

        # Ground velocity = water-relative ship velocity + current velocity.
        current_speed = settings["current_kn"] * KNOT_TO_MPS
        current_dir = settings["current_dir_deg"] * DEG
        current_x = current_speed * math.cos(current_dir)
        current_y = current_speed * math.sin(current_dir)
        water_x, water_y = body_to_world(self.u, self.v, self.psi)
        ground_x = water_x + current_x
        ground_y = water_y + current_y

        self.x += ground_x * dt
        self.y += ground_y * dt
        self.psi = wrap_angle(self.psi + self.r * dt)
        self.elapsed += dt

        # Ground speed/course are based on actual world displacement velocity.
        self.ground_speed = math.hypot(ground_x, ground_y)
        self.ground_course = math.atan2(ground_y, ground_x)
        return details


# ----------------------- Tkinter simulator UI -------------------

class BerthingSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Ship Berthing Simulator — 3-DOF Training Model")
        self.root.geometry("1180x780")
        self.root.minsize(950, 650)

        self.ship = ShipModel()
        self.target_x = 0.0
        self.target_y = 0.0
        self.target_heading = 0.0
        self.auto_berthing = False
        self.berth_complete = False
        self.running = True
        self.last_tick = None
        self.settings_vars = {}
        self._build_ui()
        self._reset_clock()
        self._tick()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=8)
        outer.pack(fill="both", expand=True)

        left = ttk.Frame(outer)
        left.pack(side="left", fill="y", padx=(0, 10))
        right = ttk.Frame(outer)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="Environment & Controls",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))

        self._add_scale(left, "Wind speed (kn)", "wind_kn", 0, 40, 15, 1)
        self._add_scale(left, "Wind direction TOWARD (°)", "wind_dir_deg", 0, 359, 270, 1)
        self._add_scale(left, "Current speed (kn)", "current_kn", 0, 3, 0.5, 0.1)
        self._add_scale(left, "Current direction TOWARD (°)", "current_dir_deg", 0, 359, 0, 1)
        self._add_scale(left, "Bow tug force (kN)", "bow_tug_kn", 0, 500, 0, 5)
        self._add_scale(left, "Bow tug angle (°)", "bow_tug_angle_deg", -180, 180, 90, 5)
        self._add_scale(left, "Stern tug force (kN)", "stern_tug_kn", 0, 500, 0, 5)
        self._add_scale(left, "Stern tug angle (°)", "stern_tug_angle_deg", -180, 180, 90, 5)
        self._add_scale(left, "Longitudinal propulsion (+)/brake (-) (kN)",
                        "propulsion_kn", -500, 500, 0, 10)
        self._add_scale(left, "Illustrative wave-force amplitude (kN)",
                        "wave_force_kn", 0, 300, 0, 10)
        self._add_scale(left, "Wave period (s)", "wave_period_s", 2, 20, 8, 1)
        self._add_scale(left, "Wave direction TOWARD (°)", "wave_dir_deg", 0, 359, 90, 1)

        buttons = ttk.Frame(left)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Pause / Resume", command=self._toggle).pack(
            side="left", padx=(0, 4))
        ttk.Button(buttons, text="Reset", command=self._reset).pack(side="left")
        self.auto_button = ttk.Button(
            left, text="Auto Berthing: OFF", command=self._toggle_auto
        )
        self.auto_button.pack(fill="x", pady=(0, 6))

        ttk.Label(left, text="Directions are degrees counter-clockwise from east.\n"
                             "Tug angle is relative to the bow direction.",
                  foreground="#555", wraplength=285).pack(anchor="w", pady=(4, 0))

        ttk.Label(right, text="Top-down view (schematic; not to scale)",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.canvas = tk.Canvas(right, bg="#eaf3f8", highlightthickness=1,
                                highlightbackground="#9aabb5")
        self.canvas.pack(fill="both", expand=True, pady=(5, 8))

        self.status = ttk.Label(right, text="", justify="left",
                                font=("Consolas", 10))
        self.status.pack(fill="x", anchor="w")

        self.warning = ttk.Label(
            right,
            text="TRAINING ONLY — not for real navigation or operational berthing decisions.",
            foreground="#a32626", font=("Segoe UI", 10, "bold"))
        self.warning.pack(anchor="w", pady=(5, 0))

    def _add_scale(self, parent, label, key, low, high, initial, resolution):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=2)
        var = tk.DoubleVar(value=initial)
        self.settings_vars[key] = var
        row = ttk.Frame(frame)
        row.pack(fill="x")
        ttk.Label(row, text=label, wraplength=220).pack(side="left", fill="x", expand=True)
        value_label = ttk.Label(row, width=7, text=str(initial))
        value_label.pack(side="right")
        scale = tk.Scale(frame, from_=low, to=high, resolution=resolution,
                         orient="horizontal", showvalue=False, variable=var,
                         length=270, command=lambda value, lab=value_label: lab.config(
                             text=f"{float(value):.1f}"))
        scale.pack(fill="x")

    def _settings(self):
        settings = {key: var.get() for key, var in self.settings_vars.items()}
        if self.auto_berthing:
            settings.update(self._auto_controls(settings))
        return settings

    def _toggle_auto(self):
        self.auto_berthing = not self.auto_berthing
        self.berth_complete = False
        self.auto_button.config(
            text=f"Auto Berthing: {'ON' if self.auto_berthing else 'OFF'}"
        )
        self._reset_clock()

    def _auto_controls(self, environmental_settings):
        """Simple PD-style training controller; not a real ship autopilot."""
        # Ground velocity resolved into the ship's body axes.
        current_speed = environmental_settings["current_kn"] * KNOT_TO_MPS
        current_dir = environmental_settings["current_dir_deg"] * DEG
        cx = current_speed * math.cos(current_dir)
        cy = current_speed * math.sin(current_dir)
        current_u, current_v = world_to_body(cx, cy, self.ship.psi)
        ground_u = self.ship.u + current_u
        ground_v = self.ship.v + current_v

        dx = self.target_x - self.ship.x
        dy = self.target_y - self.ship.y
        distance_x = abs(dx)
        direction = 1.0 if dx >= 0 else -1.0

        # Speed target follows a conservative stopping envelope. The maximum
        # target speed is 3 kn and the desired speed falls near the berth.
        stopping_accel = 0.012  # m/s^2, conservative illustrative setting
        desired_speed = direction * min(
            3.0 * KNOT_TO_MPS,
            math.sqrt(max(0.0, 2.0 * stopping_accel * distance_x)),
        )
        # Small proportional position term prevents drifting through the target.
        if distance_x < 2.0:
            desired_speed = clamp(0.35 * dx, -0.25, 0.25)
        surge_force = self.ship.mx * 0.12 * (desired_speed - ground_u)
        surge_force = clamp(surge_force, -500_000.0, 500_000.0)

        heading_error = wrap_angle(self.target_heading - self.ship.psi)
        desired_yaw_rate = clamp(0.8 * heading_error, -0.06, 0.06)
        yaw_moment = self.ship.Iz * (
            0.003 * heading_error + 0.8 * (desired_yaw_rate - self.ship.r)
        )
        yaw_moment = clamp(yaw_moment, -30_000_000.0, 30_000_000.0)

        desired_sway_speed = clamp(0.08 * dy, -0.25, 0.25)
        sway_force = self.ship.my * 0.10 * (desired_sway_speed - ground_v)
        sway_force = clamp(sway_force, -300_000.0, 300_000.0)

        # Two lateral tug forces can produce both net sway force and yaw moment.
        arm = 0.40 * self.ship.length
        bow_y = 0.5 * (sway_force + yaw_moment / arm)
        stern_y = 0.5 * (sway_force - yaw_moment / arm)
        max_tug = 500_000.0
        bow_y = clamp(bow_y, -max_tug, max_tug)
        stern_y = clamp(stern_y, -max_tug, max_tug)

        def tug_command(lateral_force):
            return abs(lateral_force) / 1000.0, (90.0 if lateral_force >= 0 else -90.0)

        bow_force, bow_angle = tug_command(bow_y)
        stern_force, stern_angle = tug_command(stern_y)
        return {
            "propulsion_kn": surge_force / 1000.0,
            "bow_tug_kn": bow_force,
            "bow_tug_angle_deg": bow_angle,
            "stern_tug_kn": stern_force,
            "stern_tug_angle_deg": stern_angle,
        }

    def _berthing_status(self):
        current = self._settings_without_auto()
        speed = getattr(self.ship, "ground_speed", 0.0)
        dx = self.target_x - self.ship.x
        dy = self.target_y - self.ship.y
        heading_error = abs(math.degrees(wrap_angle(self.target_heading - self.ship.psi)))
        self.berth_complete = (
            abs(dx) <= 2.0 and abs(dy) <= 2.0 and speed <= 0.15
            and heading_error <= 5.0 and abs(math.degrees(self.ship.r)) <= 0.5
        )
        return dx, dy, heading_error

    def _settings_without_auto(self):
        return {key: var.get() for key, var in self.settings_vars.items()}

    def _toggle(self):
        self.running = not self.running
        self._reset_clock()

    def _reset_clock(self):
        self.last_tick = None

    def _reset(self):
        self.ship.reset()
        self.berth_complete = False
        self._reset_clock()

    def _tick(self):
        now = self.root.tk.call("clock", "milliseconds")
        now = int(now)
        if self.last_tick is None:
            dt = 0.02
        else:
            dt = clamp((now - self.last_tick) / 1000.0, 0.001, 0.05)
        self.last_tick = now

        if self.running:
            # Use smaller physics substeps for numerical stability.
            remaining = min(dt, 0.05)
            while remaining > 1e-9:
                h = min(0.01, remaining)
                self.ship.step(self._settings(), h)
                remaining -= h

        self._draw()
        self.root.after(20, self._tick)

    def _draw(self):
        c = self.canvas
        c.delete("all")
        width = max(c.winfo_width(), 400)
        height = max(c.winfo_height(), 300)
        cx, cy = width * 0.5, height * 0.5
        scale = min(width / 500.0, height / 380.0)

        # Grid.
        for x in range(0, width, 40):
            c.create_line(x, 0, x, height, fill="#d7e4eb")
        for y in range(0, height, 40):
            c.create_line(0, y, width, y, fill="#d7e4eb")

        # Fixed world view: berth target and quay do not move or wrap.
        # View window covers approximately x=-300..+100 m and y=-100..+100 m.
        view_scale = min(width / 420.0, height / 230.0)
        px = width * 0.20 + (self.ship.x + 300.0) * view_scale
        py = height * 0.50 - self.ship.y * view_scale
        target_px = width * 0.20 + (self.target_x + 300.0) * view_scale
        target_py = height * 0.50 - self.target_y * view_scale
        quay_y = height * 0.50 - (self.target_y + self.ship.beam / 2.0 + 5.0) * view_scale
        c.create_line(15, quay_y, width - 15, quay_y,
                      fill="#6b8795", width=5)
        c.create_text(25, quay_y - 12, text="QUAY / BERTH", anchor="w",
                      fill="#45606c", font=("Segoe UI", 9, "bold"))
        c.create_line(target_px, target_py - 48, target_px, target_py + 48,
                      fill="#e55d17", width=2, dash=(5, 3))
        c.create_oval(target_px - 5, target_py - 5, target_px + 5, target_py + 5,
                      fill="#e55d17", outline="white")
        c.create_text(target_px + 8, target_py + 18, text="BERTH TARGET (CG)",
                      anchor="w", fill="#a3410c", font=("Segoe UI", 8, "bold"))

        # Ship remains in a fixed world view; no modulo/screen wrapping.
        L = self.ship.length * view_scale * 0.65
        B = self.ship.beam * view_scale * 0.85
        # Body points: bow first, then port/starboard sides, then stern.
        local = [(L / 2, 0), (L / 3, B / 2), (-L / 2, B / 2),
                 (-L / 2, -B / 2), (L / 3, -B / 2)]
        points = []
        for bx, by in local:
            wx, wy = body_to_world(bx, by, self.ship.psi)
            points.extend([px + wx, py - wy])
        c.create_polygon(points, fill="#f5f7fa", outline="#16355d", width=2)
        # Bow direction line.
        bx, by = body_to_world(L * 0.62, 0, self.ship.psi)
        c.create_line(px, py, px + bx, py - by, fill="#e55d17", width=2,
                      arrow=tk.LAST)
        c.create_text(px, py + B / 2 + 12, text="SHIP", fill="#16355d",
                      font=("Segoe UI", 9, "bold"))

        # Current and wind arrows are schematic indicators, not force-scaled.
        wind_dir = self._settings()["wind_dir_deg"] * DEG
        current_dir = self._settings()["current_dir_deg"] * DEG
        for angle, color, label, length in [
            (wind_dir, "#2c7fb8", "Wind", 45),
            (current_dir, "#27945c", "Current", 35),
        ]:
            dx, dy = length * math.cos(angle), length * math.sin(angle)
            x0, y0 = 65, 60 if label == "Wind" else 110
            c.create_line(x0, y0, x0 + dx, y0 - dy, fill=color, width=3,
                          arrow=tk.LAST)
            c.create_text(x0, y0 - 15, text=label, fill=color, anchor="w")

        f = self.ship.last_forces
        speed_kn = getattr(self.ship, "ground_speed", 0.0) / KNOT_TO_MPS
        dx, dy, heading_error = self._berthing_status()
        mode_text = "AUTO BERTHING" if self.auto_berthing else "MANUAL CONTROL"
        berth_text = "BERTHED — within training tolerances" if self.berth_complete else "Approach / alignment in progress"
        course_deg = math.degrees(getattr(self.ship, "ground_course", 0.0)) % 360
        heading_deg = math.degrees(self.ship.psi) % 360
        resultant_xy = math.hypot(f.get("X_total", 0.0), f.get("Y_total", 0.0))
        resultant_angle = math.degrees(math.atan2(
            f.get("Y_total", 0.0), f.get("X_total", 0.0)
        ))
        self.status.config(text=(
            f"Mode: {mode_text}    Status: {berth_text}\n"
            f"Time: {self.ship.elapsed:7.1f} s    "
            f"Position: X={self.ship.x:8.1f} m, Y={self.ship.y:8.1f} m\n"
            f"Berth error: ΔX={dx:7.1f} m, ΔY={dy:6.1f} m, heading error={heading_error:5.1f}°\n"
            f"Heading: {heading_deg:6.1f}°    Ground speed: {speed_kn:5.2f} kn    "
            f"Course over ground: {course_deg:6.1f}°\n"
            f"Water-relative u={self.ship.u:6.3f} m/s, v={self.ship.v:6.3f} m/s, "
            f"yaw rate={math.degrees(self.ship.r):6.3f}°/s\n"
            f"Body resultant: X={f.get('X_total', 0)/1000:8.1f} kN, "
            f"Y={f.get('Y_total', 0)/1000:8.1f} kN, "
            f"Fxy={resultant_xy/1000:7.1f} kN at {resultant_angle:6.1f}°, "
            f"N={f.get('N_total', 0)/1e6:8.2f} MN·m\n"
            f"Water-relative speed components: u={f.get('water_rel_u', 0):6.3f} m/s, "
            f"v={f.get('water_rel_v', 0):6.3f} m/s\n"
            f"Wind force: X={f.get('X_wind', 0)/1000:7.1f}, "
            f"Y={f.get('Y_wind', 0)/1000:7.1f} kN | "
            f"Tug force: X={f.get('X_tug', 0)/1000:7.1f}, "
            f"Y={f.get('Y_tug', 0)/1000:7.1f} kN"
        ))


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    BerthingSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
