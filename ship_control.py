
import tkinter as tk
from tkinter import ttk
import math


# -------------------------------
# Q-Max Ship Canvas - Step 1
# Drawing only; no ship physics yet
# -------------------------------

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650

SHIP_LENGTH = 500
SHIP_BEAM = 78


# -------------------------------
# Physical unit conversions
# -------------------------------

KNOT_TO_MPS = 0.514444
MPS_TO_KNOT = 1 / KNOT_TO_MPS


class QMaxShipCanvas(tk.Tk):

        
    def __init__(self):
        super().__init__()

        # ==================================================
        # 1. MAIN WINDOW SETTINGS
        # ==================================================

        self.title("Q-Max LNG Carrier Simulator")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.configure(bg="#0b1924")

        # ==================================================
        # 2. CARGO CALCULATOR DEFAULT SETTINGS
        # ==================================================

        self.cargo_capacity = tk.DoubleVar(value=266000.0)
        self.cargo_loading = tk.DoubleVar(value=80.0)
        self.lng_density = tk.DoubleVar(value=450.0)
        self.lng_temperature = tk.DoubleVar(value=-162.0)
        self.max_fill_limit = tk.DoubleVar(value=98.5)
        self.cargo_tank_count = tk.IntVar(value=4)

        # Cargo calculator window and tank variables
        self.cargo_window = None
        self.tank_loading_vars = []
        self.tank_result_labels = []

        # ==================================================
        # 3. MENU BAR
        # ==================================================

        menu_bar = tk.Menu(self)

        cargo_menu = tk.Menu(menu_bar, tearoff=0)

        cargo_menu.add_command(
            label="Cargo Calculator",
            command=self.open_cargo_calculator
        )

        menu_bar.add_cascade(
            label="Cargo",
            menu=cargo_menu
        )

        self.config(menu=menu_bar)

        # ==================================================
        # 4. ZOOM SETTINGS
        # ==================================================

        self.zoom_level = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 2.0
        self.zoom_step = 0.15

        zoom_frame = tk.Frame(self, bg="#0b1924")
        zoom_frame.pack(side="top", fill="x")

        tk.Button(
            zoom_frame,
            text=" + Zoom In ",
            command=lambda: self.zoom_ship(1 + self.zoom_step),
            bg="#254c60",
            fg="white",
            activebackground="#356b80",
            relief="flat"
        ).pack(side="left", padx=5, pady=5)

        tk.Button(
            zoom_frame,
            text=" - Zoom Out ",
            command=lambda: self.zoom_ship(1 / (1 + self.zoom_step)),
            bg="#254c60",
            fg="white",
            activebackground="#356b80",
            relief="flat"
        ).pack(side="left", padx=5, pady=5)

        tk.Button(
            zoom_frame,
            text=" Reset Zoom ",
            command=self.reset_zoom,
            bg="#37664c",
            fg="white",
            activebackground="#4a805f",
            relief="flat"
        ).pack(side="left", padx=5, pady=5)

        self.zoom_label = tk.Label(
            zoom_frame,
            text="Zoom: 100%",
            bg="#0b1924",
            fg="#b8dce8",
            font=("Arial", 10, "bold")
        )

        self.zoom_label.pack(side="left", padx=10)

        # ==================================================
        # 5. VESSEL DIMENSIONS AND GEOGRAPHIC SCALE
        # ==================================================

        # Actual Q-Max vessel dimensions
        self.ship_length_m = 345.0
        self.ship_beam_m = 53.8

        # Drawing scale at 100% zoom
        self.pixels_per_meter = SHIP_LENGTH / self.ship_length_m

        # Geographic grid: each square represents 100 metres
        self.grid_size_m = 100.0

        self.grid_color = "#315467"
        self.grid_tag = "grid"

        # Initial grid spacing in screen pixels
        self.grid_spacing = (
            self.grid_size_m * self.pixels_per_meter * self.zoom_level
        )

        # ==================================================
        # 6. CANVAS CREATION
        # ==================================================

        self.canvas = tk.Canvas(
            self,
            bg="#12394a",
            highlightthickness=0
        )

        self.canvas.pack(fill="both", expand=True)

        # ==================================================
        # 7. SHIP INITIAL POSITION AND HEADING
        # ==================================================

        self.ship_center_x = 250
        self.ship_center_y = 400

        # Direction: 0 = North, 90 = East,
        # 180 = South, 270 = West
        self.heading = 90.0

        # ==================================================
        # 8. OCEAN CURRENT SETTINGS
        # ==================================================

        # Direction towards which the current flows
        self.current_direction = 45.0
        self.current_speed = 1.5  # knots

        # Visual animation speed (pixels per update)
        self.current_visual_speed = 0.8

        # ==================================================
        # 9. WIND SETTINGS
        # ==================================================

        # Direction towards which the wind blows
        self.wind_direction = 45.0
        self.wind_speed = 32.0  # knots

        # Approximate vessel windage properties
        self.windage_area = 12000.0       # m²
        self.air_density = 1.225          # kg/m³
        self.wind_drag_coefficient = 1.0

        # Approximate effective vessel mass
        self.vessel_mass = 150_000_000.0  # kg

        # Wind-induced drift velocity (m/s)
        self.wind_velocity_x = 0.0
        self.wind_velocity_y = 0.0

        # Simplified wind model tuning factor
        self.wind_effect_scale = 8.0

        # ==================================================
        # 10. SHIP MOVEMENT AND PROPULSION SETTINGS
        # ==================================================

        # Initial ship speed (10 knots = 5.14444 m/s)
        self.ship_speed = 5.14444

        # Maximum propulsion speed: 10 knots
        self.max_speed = self.knots_to_mps(10.0)

        # Acceleration and braking
        self.acceleration = 0.15  # m/s²
        self.braking = 0.20       # m/s²

        # Water resistance coefficient
        # Retained for the future propulsion/resistance model.
        # It is not currently applied in the simplified speed update.
        self.water_drag = 0.08

        # Initial speed over ground
        self.speed_over_ground = 0.0

        # ==================================================
        # 11. RUDDER AND TURNING SETTINGS
        # ==================================================

        self.max_rudder_angle = 35.0
        self.rudder_angle = 0.0
        self.rudder_command = 0.0

        # Rudder movement speed (degrees/second)
        self.rudder_rate = 10.0

        # Vessel turning characteristics
        self.max_turn_rate = 3.0
        self.rate_of_turn = 0.0
        self.turn_inertia = 3.5

        # ==================================================
        # 12. KEYBOARD INPUT SETTINGS
        # ==================================================

        self.keys_pressed = set()

        # ==================================================
        # 13. DRAW ENVIRONMENT AND SHIP
        # ==================================================

        # Draw ocean current behind the vessel
        self.draw_ocean_current()

        # Draw vessel over the ocean current
        self.draw_ship()

        # ==================================================
        # 14. NAVIGATION SPEED DISPLAY
        # ==================================================

        self.speed_readout = self.canvas.create_text(
            25,
            80,
            text="STW: 0.00 kn | SOG: 0.00 kn",
            fill="white",
            anchor="nw",
            font=("Arial", 11, "bold")
        )

        # ==================================================
        # 15. KEYBOARD EVENT BINDINGS
        # ==================================================

        self.bind("<KeyPress>", self.key_down)
        self.bind("<KeyRelease>", self.key_up)

        self.focus_set()

        # ==================================================
        # 16. START SHIP PHYSICS SIMULATION
        # ==================================================

        self.after(30, self.update_ship)

        # ==================================================
        # 17. TEMPORARY UNIT CONVERSION TEST
        # ==================================================

        current_mps = self.knots_to_mps(self.current_speed)

        print("----- UNIT CONVERSION TEST -----")

        print(f"Current speed: {self.current_speed:.2f} knots")
        print(f"Current speed: {current_mps:.4f} m/s")

        print(f"Pixels per metre: {self.pixels_per_meter:.4f}")

        print(
            f"100 metres in pixels: "
            f"{self.meters_to_pixels(100):.2f}"
        )

        print(
            f"100 pixels in metres: "
            f"{self.pixels_to_meters(100):.2f}"
        )

        
    
    # -------------------------------
    # Unit conversion functions
    # -------------------------------

    def knots_to_mps(self, knots):
        """Convert speed from knots to metres per second."""
        return knots * KNOT_TO_MPS


    def mps_to_knots(self, speed_mps):
        """Convert speed from metres per second to knots."""
        return speed_mps * MPS_TO_KNOT


    def meters_to_pixels(self, distance_m):
        """Convert real-world distance into canvas pixels."""
        return distance_m * self.pixels_per_meter * self.zoom_level


    def pixels_to_meters(self, distance_pixels):
        """Convert canvas pixels into real-world distance."""
        return distance_pixels / (
            self.pixels_per_meter * self.zoom_level
        )
    
    def draw_scale_indicator(self):
        """Display a scale bar in metres at the bottom-left."""

        self.canvas.delete("scale_indicator")

        # Current display scale, including zoom
        pixels_per_meter = self.pixels_per_meter * self.zoom_level

        # Scale bar represents 100 metres
        scale_distance_m = 100
        bar_length = scale_distance_m * pixels_per_meter

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1:
            width = WINDOW_WIDTH

        if height <= 1:
            height = WINDOW_HEIGHT

        x = 25
        y = height - 35

        self.canvas.create_line(
            x, y, x + bar_length, y,
            fill="white",
            width=4,
            tags="scale_indicator"
        )

        # End markers
        for px in (x, x + bar_length):
            self.canvas.create_line(
                px, y - 7, px, y + 7,
                fill="white",
                width=2,
                tags="scale_indicator"
            )

        self.canvas.create_text(
            x + bar_length / 2,
            y - 15,
            text=f"{scale_distance_m} m",
            fill="white",
            font=("Arial", 10, "bold"),
            tags="scale_indicator"
        )

        self.canvas.create_text(
            x,
            y + 15,
            text=f"Scale: {pixels_per_meter:.3f} px/m",
            fill="white",
            anchor="w",
            font=("Arial", 9),
            tags="scale_indicator"
        )

        self.canvas.tag_raise("scale_indicator")

        
        
    
    
    def draw_grid(self):
        """Draw a grid where each square represents 100 metres."""

        self.canvas.delete("grid")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1:
            width = WINDOW_WIDTH

        if height <= 1:
            height = WINDOW_HEIGHT

        spacing = (
            self.grid_size_m
            * self.pixels_per_meter
            * self.zoom_level
        )

        # Keep grid spacing within a usable screen range.
        if spacing < 5:
            return

        # Draw vertical grid lines.
        x = 0
        while x <= width:
            self.canvas.create_line(
                x, 0, x, height,
                fill=self.grid_color,
                width=1,
                tags="grid"
            )
            x += spacing

        # Draw horizontal grid lines.
        y = 0
        while y <= height:
            self.canvas.create_line(
                0, y, width, y,
                fill=self.grid_color,
                width=1,
                tags="grid"
            )
            y += spacing

        self.canvas.tag_lower("grid")
        self.draw_scale_indicator()

        
    # -------------------------------
    # Canvas zoom functions
    # ------------------------------- 
    def zoom_ship(self, factor):
        """Zoom the ship around its current centre."""

        new_zoom = self.zoom_level * factor

        if not self.min_zoom <= new_zoom <= self.max_zoom:
            return

        cx = self.ship_center_x
        cy = self.ship_center_y

        # Scale the ship drawing around its centre
        self.canvas.scale("ship", cx, cy, factor, factor)

        self.zoom_level = new_zoom
        
        self.draw_grid()
        self.draw_scale_indicator()

        self.zoom_label.config(
            text=f"Zoom: {self.zoom_level * 100:.0f}%"
        )
        

    def reset_zoom(self):
        """Return the ship to its original drawing scale."""

        if self.zoom_level == 1.0:
            return

        factor = 1.0 / self.zoom_level

        self.canvas.scale(
            "ship",
            self.ship_center_x,
            self.ship_center_y,
            factor,
            factor
        )

        self.zoom_level = 1.0
        self.draw_grid()
        self.draw_scale_indicator()
        self.zoom_label.config(text="Zoom: 100%")
        
        


    # -------------------------------
    # 1. Ship drawing
    def draw_ship(self):

        c = self.canvas

        cx = self.ship_center_x
        cy = self.ship_center_y

        # Ship dimensions
        half_length = SHIP_LENGTH / 2
        half_beam = SHIP_BEAM / 2

        # ---------------------------------
        # 1. Outer hull - HORIZONTAL
        # Bow points RIGHT
        # Stern points LEFT
        # ---------------------------------

        hull = [
            cx + half_length, cy,                  # Bow
            cx + half_length * 0.72, cy - half_beam * 0.65,
            cx - half_length * 0.25, cy - half_beam,
            cx - half_length * 0.42, cy - half_beam * 0.85,
            cx - half_length * 0.50, cy,           # Stern
            cx - half_length * 0.42, cy + half_beam * 0.85,
            cx - half_length * 0.25, cy + half_beam,
            cx + half_length * 0.72, cy + half_beam * 0.65
        ]

        c.create_polygon(
            hull,
            fill="gray",
            outline="black",
            tags="ship"
        )

        # ---------------------------------
        # 2. Inner deck area
        # ---------------------------------

        c.create_polygon(
            cx + half_length * 0.91, cy,
            cx + half_length * 0.65, cy - half_beam * 0.52,
            cx - half_length * 0.25, cy - half_beam * 0.78,
            cx - half_length * 0.38, cy - half_beam * 0.65,
            cx - half_length * 0.43, cy,
            cx - half_length * 0.38, cy + half_beam * 0.65,
            cx - half_length * 0.25, cy + half_beam * 0.78,
            cx + half_length * 0.65, cy + half_beam * 0.52,
            fill="#254c60",
            outline="#8bb8ca",
            width=2,
            tags="ship"
        )

        # ---------------------------------
        # 3. Four LNG cargo tanks
        # Arrange them along the ship's length
        # ---------------------------------
        
        tank_width = 48
        tank_height = 48

        for i in range(4):
            tank_x = cx - 45 + i * 55
            tank_y = cy

            c.create_rectangle(
                tank_x - tank_width / 2,
                cy - tank_height / 2,
                tank_x + tank_width / 2,
                cy + tank_height / 2,
                fill="#b8dce8",
                outline="#e8f7fc",
                width=2,
                tags="ship"
            )

            c.create_text(
                tank_x,
                cy,
                text=f"LNG {i + 1}",
                fill="#173748",
                font=("Arial", 9, "bold"),
                tags="ship"
            )

        # ---------------------------------
        # 4. Bridge near the stern
        # Stern is on the LEFT
        # ---------------------------------
        bridge_x = cx - half_length * 0.42

        c.create_rectangle(
            bridge_x - 22,
            cy - 27,
            bridge_x + 15,
            cy + 27,
            fill="#f0c477",
            outline="#fff0c8",
            width=2,
            tags="ship"
        )

        c.create_rectangle(
            bridge_x - 16,
            cy - 19,
            bridge_x - 5,
            cy + 19,
            fill="#18313e",
            outline="#d6e8ef",
            tags="ship"
        )

        # ---------------------------------
        # 5. Ship information
        # ---------------------------------

        c.create_text(
            25, 25,
            text="Q-MAX LNG CARRIER | TOP VIEW",
            fill="white",
            anchor="nw",
            font=("Arial", 15, "bold")
        )

        c.create_text(
            25, 52,
            text="LOA: 345 m  |  Beam: 53.8 m",
            fill="#b8dce8",
            anchor="nw",
            font=("Arial", 11)
        )

    
    # -------------------------------
    # 2. Draw ocean current arrows
    def draw_ocean_current(self):
        """Draw ocean-current arrows pointing in the selected direction."""

        self.current_items = []

        canvas_width = WINDOW_WIDTH
        canvas_height = WINDOW_HEIGHT

        spacing = 100
        arrow_length = 28

        # Convert current direction to radians
        angle = math.radians(self.current_direction)

        # Calculate arrow direction (0° = North, 90° = East)
        dx = math.sin(angle) * arrow_length
        dy = -math.cos(angle) * arrow_length

        for x in range(40, canvas_width, spacing):
            for y in range(40, canvas_height, spacing):

                item = self.canvas.create_line(
                    x,
                    y,
                    x + dx,
                    y + dy,
                    fill="#54c8e8",
                    width=2,
                    arrow=tk.LAST,
                    tags="current"
                )

                self.current_items.append(item)

        self.animate_ocean_current()
        self.draw_scale_indicator()


# -------------------------------
# 3. Ocean current animation update
    def animate_ocean_current(self):
        """Animate the water in the selected current direction."""

        angle = math.radians(self.current_direction)

        dx = math.sin(angle) * self.current_visual_speed
        dy = -math.cos(angle) * self.current_visual_speed

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1:
            width = WINDOW_WIDTH
        if height <= 1:
            height = WINDOW_HEIGHT

        for item in self.current_items:
            self.canvas.move(item, dx, dy)

            coords = self.canvas.coords(item)

            if not coords:
                continue

            x1, y1, x2, y2 = coords

            # Wrap arrows around the canvas edges
            if x1 > width:
                self.canvas.move(item, -width - 40, 0)
            elif x2 < 0:
                self.canvas.move(item, width + 40, 0)

            if y1 > height:
                self.canvas.move(item, 0, -height - 40)
            elif y2 < 0:
                self.canvas.move(item, 0, height + 40)

        self.after(50, self.animate_ocean_current)
        self.draw_grid()
        
        
    # -------------------------------
    # 4. Keyboard input handling
    def key_down(self, event):
        self.keys_pressed.add(event.keysym)
        
        

    def key_up(self, event):
        self.keys_pressed.discard(event.keysym)
        
        
        
    #-------------------------------
    # 5. Ship rotation 
    def rotate_ship(self, angle_degrees):
        """Rotate the ship's drawing around its centre."""

        angle = math.radians(angle_degrees)

        cx = self.ship_center_x
        cy = self.ship_center_y

        for item in list(self.canvas.find_withtag("ship")):
            item_type = self.canvas.type(item)
            coords = self.canvas.coords(item)

            # Rotate polygon points
            if item_type == "polygon":
                new_coords = []

                for i in range(0, len(coords), 2):
                    x, y = coords[i], coords[i + 1]

                    dx = x - cx
                    dy = y - cy

                    new_x = cx + dx * math.cos(angle) - dy * math.sin(angle)
                    new_y = cy + dx * math.sin(angle) + dy * math.cos(angle)

                    new_coords.extend([new_x, new_y])

                self.canvas.coords(item, *new_coords)

            # Convert rectangles into polygons so they can rotate
            elif item_type == "rectangle":
                x1, y1, x2, y2 = coords

                points = [
                    (x1, y1), (x2, y1),
                    (x2, y2), (x1, y2)
                ]

                rotated = []
                for x, y in points:
                    dx, dy = x - cx, y - cy
                    rotated.extend([
                        cx + dx * math.cos(angle) - dy * math.sin(angle),
                        cy + dx * math.sin(angle) + dy * math.cos(angle)
                    ])

                options = self.canvas.itemconfigure(item)
                fill = options["fill"][-1]
                outline = options["outline"][-1]
                width = options["width"][-1]

                self.canvas.delete(item)
                self.canvas.create_polygon(
                    *rotated,
                    fill=fill,
                    outline=outline,
                    width=width,
                    tags="ship"
                )

            # Rotate text position (text itself remains horizontal)
            elif item_type == "text":
                x, y = coords
                dx, dy = x - cx, y - cy

                self.canvas.coords(
                    item,
                    cx + dx * math.cos(angle) - dy * math.sin(angle),
                    cy + dx * math.sin(angle) + dy * math.cos(angle)
                )


    # -------------------------------
    # 6. Ship physics update
    
    def update_ship(self):
        # Simulation time step: 30 milliseconds
        dt = 0.03
        
        # 1. ENGINE AND SPEED

        if "Up" in self.keys_pressed:

            # Engine accelerates the ship
            self.ship_speed += self.acceleration * dt

        elif "Down" in self.keys_pressed:

            # Apply braking
            self.ship_speed -= self.braking * dt

        else:

            # No acceleration or braking command.
            # Maintain the existing speed for now.
            pass

        # Keep the ship moving forward only
        self.ship_speed = max(
            0.0,
            min(self.max_speed, self.ship_speed)
        )

        print(
            f"Ship speed: {self.ship_speed:.3f} m/s | "
            f"{self.mps_to_knots(self.ship_speed):.2f} knots"
        )

        # 2. RUDDER COMMAND
        # Left = port rudder; Right = starboard rudder
        self.rudder_command = 0.0

        if "Left" in self.keys_pressed and "Right" not in self.keys_pressed:
            self.rudder_command = -self.max_rudder_angle

        elif "Right" in self.keys_pressed and "Left" not in self.keys_pressed:
            self.rudder_command = self.max_rudder_angle

        # 3. RUDDER LAG
        # Actual rudder follows the command gradually instead of instantly
        rudder_difference = self.rudder_command - self.rudder_angle
        max_rudder_change = self.rudder_rate * dt

        rudder_change = max(
            -max_rudder_change,
            min(max_rudder_change, rudder_difference)
        )

        self.rudder_angle += rudder_change

        # 4. HYDRODYNAMIC TURNING
        # Less forward speed means less rudder effectiveness
        speed_factor = self.ship_speed / self.max_speed

        target_turn_rate = (
            self.max_turn_rate
            * (self.rudder_angle / self.max_rudder_angle)
            * speed_factor
        )

        # Turning inertia: actual rate of turn approaches its target gradually
        turn_response = min(1.0, dt / self.turn_inertia)

        self.rate_of_turn += (
            target_turn_rate - self.rate_of_turn
        ) * turn_response

        
        
        #------------------NEW CODE BELOW-------------------
        
        # Calculate the heading change based on the rate of turn
        
        # 5. CALCULATE THE CURVED MOVEMENT

        # Calculate heading during this frame
        heading_change = self.rate_of_turn * dt
        movement_heading = self.heading + heading_change / 2.0

        angle = math.radians(movement_heading)

        # --------------------------------
        # A. Ship velocity through water
        # --------------------------------

        # ship_speed is currently measured in pixels/second.
        # Convert it into metres/second.
        # ship_speed_mps = self.ship_speed / self.pixels_per_meter
        ship_speed_mps = self.ship_speed

        ship_velocity_x = ship_speed_mps * math.sin(angle)
        ship_velocity_y = -ship_speed_mps * math.cos(angle)

        # --------------------------------
        # B. Ocean current velocity
        # --------------------------------

        current_angle = math.radians(self.current_direction)
        current_speed_mps = self.knots_to_mps(self.current_speed)

        current_velocity_x = (
            current_speed_mps * math.sin(current_angle)
        )

        current_velocity_y = (
            -current_speed_mps * math.cos(current_angle)
        )

        # --------------------------------
        # C. Wind velocity
        # --------------------------------

        wind_angle = math.radians(self.wind_direction)
        wind_speed_mps = self.knots_to_mps(self.wind_speed)

        wind_velocity_x = wind_speed_mps * math.sin(wind_angle)
        wind_velocity_y = -wind_speed_mps * math.cos(wind_angle)

        # Estimate vessel ground velocity before wind acceleration
        base_velocity_x = ship_velocity_x + current_velocity_x
        base_velocity_y = ship_velocity_y + current_velocity_y

        # Include existing wind-induced drift
        base_velocity_x += self.wind_velocity_x
        base_velocity_y += self.wind_velocity_y

        # --------------------------------
        # D. Relative wind velocity
        # --------------------------------

        relative_wind_x = wind_velocity_x - base_velocity_x
        relative_wind_y = wind_velocity_y - base_velocity_y

        relative_wind_speed = math.sqrt(
            relative_wind_x ** 2 + relative_wind_y ** 2
        )

        # --------------------------------
        # E. Wind force
        # --------------------------------

        wind_force = (
            0.5
            * self.air_density
            * self.wind_drag_coefficient
            * self.windage_area
            * relative_wind_speed ** 2
        )

        if relative_wind_speed > 0.001:

            wind_force_x = (
                wind_force
                * relative_wind_x
                / relative_wind_speed
            )

            wind_force_y = (
                wind_force
                * relative_wind_y
                / relative_wind_speed
            )

        else:
            wind_force_x = 0.0
            wind_force_y = 0.0

        # --------------------------------
        # F. Wind acceleration
        # --------------------------------

        wind_acceleration_x = (
            wind_force_x / self.vessel_mass
        ) * self.wind_effect_scale

        wind_acceleration_y = (
            wind_force_y / self.vessel_mass
        ) * self.wind_effect_scale

        self.wind_velocity_x += wind_acceleration_x * dt
        self.wind_velocity_y += wind_acceleration_y * dt

        # Hydrodynamic damping of wind-induced drift
        wind_damping = 0.10

        self.wind_velocity_x *= max(0.0, 1.0 - wind_damping * dt)
        self.wind_velocity_y *= max(0.0, 1.0 - wind_damping * dt)

        # --------------------------------
        # G. Total ground velocity
        # --------------------------------

        ground_velocity_x = (
            ship_velocity_x
            + current_velocity_x
            + self.wind_velocity_x
        )

        ground_velocity_y = (
            ship_velocity_y
            + current_velocity_y
            + self.wind_velocity_y
        )
        
        
        # Calculate Speed Over Ground in knots
        self.speed_over_ground = (
            math.sqrt(
                ground_velocity_x ** 2
                + ground_velocity_y ** 2
            ) / 0.514444
        )
        
        
        print("\n--- VELOCITY DEBUG ---")

        print(f"Ship X: {ship_velocity_x:.3f} m/s")
        print(f"Ship Y: {ship_velocity_y:.3f} m/s")

        print(f"Current X: {current_velocity_x:.3f} m/s")
        print(f"Current Y: {current_velocity_y:.3f} m/s")

        print(f"Wind drift X: {self.wind_velocity_x:.3f} m/s")
        print(f"Wind drift Y: {self.wind_velocity_y:.3f} m/s")

        print(f"Ground X: {ground_velocity_x:.3f} m/s")
        print(f"Ground Y: {ground_velocity_y:.3f} m/s")

        print(f"SOG: {self.speed_over_ground:.3f} knots")

        
        
        self.canvas.itemconfig(
            self.speed_readout,
            text=(
                f"STW: {self.mps_to_knots(self.ship_speed):.2f} kn"
                f" | SOG: {self.speed_over_ground:.2f} kn"
            )
        )

        # Convert ground movement into canvas pixels
        # dx = ground_velocity_x * self.pixels_per_meter * dt
        # dy = ground_velocity_y * self.pixels_per_meter * dt
        
        # --------------------------------
        # Convert physical movement into screen pixels
        # --------------------------------

        # Effective display scale changes with zoom.
        display_pixels_per_meter = (
            self.pixels_per_meter * self.zoom_level
        )

        # Convert ground velocity (m/s) into screen movement (pixels).
        dx = (
            ground_velocity_x
            * display_pixels_per_meter
            * dt
        )

        dy = (
            ground_velocity_y
            * display_pixels_per_meter
            * dt
        )



        #--------------new code above End here-------------------
        
        
        # 6. ROTATE THE SHIP'S DRAWING
        if abs(heading_change) > 0.0001:
            self.rotate_ship(heading_change)

        # 7. MOVE THE WHOLE SHIP
        # screen_dx = dx * self.zoom_level
        # screen_dy = dy * self.zoom_level
        
        screen_dx = dx
        screen_dy = dy

        self.canvas.move("ship", screen_dx, screen_dy)

        # Update the ship's drawing centre
        self.ship_center_x += screen_dx
        self.ship_center_y += screen_dy
        
        
        # Update the vessel's heading
        self.heading = (self.heading + heading_change) % 360


        # 8. CONTINUE THE SIMULATION
        self.after(30, self.update_ship)


    # -------------------------------
    # 7. LNG Cargo Calculator  
    def open_cargo_calculator(self):
        """Open the LNG cargo calculator without changing the ship canvas."""

        # Reuse the existing calculator window if it is already open.
        if self.cargo_window is not None and self.cargo_window.winfo_exists():
            self.cargo_window.lift()
            return

        self.cargo_window = tk.Toplevel(self)
        self.cargo_window.title("Q-Max LNG Cargo Calculator")
        self.cargo_window.geometry("760x700")
        self.cargo_window.minsize(650, 550)

        window = self.cargo_window

        # Main layout
        main = ttk.Frame(window, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Q-MAX LNG CARGO CONFIGURATION",
            font=("Arial", 15, "bold")
        ).pack(anchor="w", pady=(0, 12))

        # Vessel/cargo input fields
        inputs = ttk.LabelFrame(
            main,
            text="Vessel and cargo properties",
            padding=10
        )
        inputs.pack(fill="x", pady=(0, 10))

        fields = [
            ("Total cargo capacity (m³)", self.cargo_capacity),
            ("Default loading (%)", self.cargo_loading),
            ("LNG density (kg/m³)", self.lng_density),
            ("LNG temperature (°C)", self.lng_temperature),
            ("Maximum fill limit (%)", self.max_fill_limit),
            ("Number of cargo tanks", self.cargo_tank_count),
        ]

        for row, (label_text, variable) in enumerate(fields):
            ttk.Label(inputs, text=label_text).grid(
                row=row, column=0, sticky="w", padx=5, pady=4
            )

            entry = ttk.Entry(
                inputs,
                textvariable=variable,
                width=16
            )
            entry.grid(row=row, column=1, sticky="e", padx=5, pady=4)

        inputs.columnconfigure(0, weight=1)

        # Tank configuration table
        tank_frame = ttk.LabelFrame(
            main,
            text="Individual tank configuration",
            padding=8
        )
        tank_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.tank_rows_frame = ttk.Frame(tank_frame)
        self.tank_rows_frame.pack(fill="both", expand=True)

        # Summary results
        results = ttk.LabelFrame(
            main,
            text="Calculated cargo summary",
            padding=10
        )
        results.pack(fill="x")

        self.cargo_volume_label = ttk.Label(results, text="Cargo volume: —")
        self.cargo_volume_label.pack(anchor="w", pady=2)

        self.cargo_mass_label = ttk.Label(results, text="Cargo mass: —")
        self.cargo_mass_label.pack(anchor="w", pady=2)

        self.remaining_capacity_label = ttk.Label(
            results, text="Remaining capacity: —"
        )
        self.remaining_capacity_label.pack(anchor="w", pady=2)

        self.cargo_warning_label = ttk.Label(
            results, text="", foreground="red"
        )
        self.cargo_warning_label.pack(anchor="w", pady=(5, 0))

        # Changing tank count rebuilds the table.
        self.cargo_tank_count.trace_add(
            "write", self._rebuild_tank_rows
        )

        # Changes to these properties recalculate the results.
        for variable in (
            self.cargo_capacity,
            self.cargo_loading,
            self.lng_density,
            self.lng_temperature,
            self.max_fill_limit,
        ):
            variable.trace_add("write", self._refresh_cargo_calculation)

        self._rebuild_tank_rows()
        self._refresh_cargo_calculation()

        window.protocol("WM_DELETE_WINDOW", self._close_cargo_calculator)

# -------------------------------
# 8. Close cargo calculator
    def _close_cargo_calculator(self):
        """Close the calculator and remove its window reference."""

        if self.cargo_window is not None:
            self.cargo_window.destroy()

        self.cargo_window = None
        self.tank_loading_vars = []
        self.tank_result_labels = []

# -------------------------------
# 9. Rebuild tank rows
    def _rebuild_tank_rows(self, *_):
        """Create one editable loading row for each cargo tank."""

        if self.cargo_window is None or not self.cargo_window.winfo_exists():
            return

        try:
            count = self.cargo_tank_count.get()
            if not 1 <= count <= 20:
                return
        except (tk.TclError, ValueError):
            return

        # Remove the previous table.
        for widget in self.tank_rows_frame.winfo_children():
            widget.destroy()

        self.tank_loading_vars = []
        self.tank_result_labels = []

        headings = [
            "Tank",
            "Capacity (m³)",
            "Loading (%)",
            "Volume (m³)",
            "Mass (t)",
        ]

        for column, heading in enumerate(headings):
            ttk.Label(
                self.tank_rows_frame,
                text=heading,
                font=("Arial", 9, "bold")
            ).grid(row=0, column=column, padx=4, pady=5, sticky="w")

        for index in range(count):
            row = index + 1

            ttk.Label(
                self.tank_rows_frame,
                text=f"Tank {index + 1}"
            ).grid(row=row, column=0, padx=4, pady=3, sticky="w")

            capacity_label = ttk.Label(self.tank_rows_frame, text="—")
            capacity_label.grid(row=row, column=1, padx=4, pady=3)

            loading_var = tk.DoubleVar(value=self.cargo_loading.get())
            loading_entry = ttk.Entry(
                self.tank_rows_frame,
                textvariable=loading_var,
                width=9
            )
            loading_entry.grid(row=row, column=2, padx=4, pady=3)

            volume_label = ttk.Label(self.tank_rows_frame, text="—")
            volume_label.grid(row=row, column=3, padx=4, pady=3)

            mass_label = ttk.Label(self.tank_rows_frame, text="—")
            mass_label.grid(row=row, column=4, padx=4, pady=3)

            self.tank_loading_vars.append(loading_var)
            self.tank_result_labels.append(
                (capacity_label, volume_label, mass_label)
            )

            loading_var.trace_add(
                "write", self._refresh_cargo_calculation
            )

        self._refresh_cargo_calculation()

# -------------------------------
# 10. Refresh cargo calculation
    def _refresh_cargo_calculation(self, *_):
        """Calculate cargo volume and mass for all tanks."""

        if self.cargo_window is None or not self.cargo_window.winfo_exists():
            return

        try:
            capacity = self.cargo_capacity.get()
            density = self.lng_density.get()
            temperature = self.lng_temperature.get()
            fill_limit = self.max_fill_limit.get()
            count = self.cargo_tank_count.get()

            if capacity <= 0 or density <= 0:
                raise ValueError

            if not 1 <= count <= 20:
                raise ValueError

            if not 0 < fill_limit <= 100:
                raise ValueError

            if not -200 <= temperature <= 0:
                raise ValueError

            if len(self.tank_loading_vars) != count:
                self._rebuild_tank_rows()
                return

            tank_capacity = capacity / count
            total_volume = 0.0
            warnings = []

            for index, loading_var in enumerate(self.tank_loading_vars):
                loading = loading_var.get()

                if not 0 <= loading <= 100:
                    raise ValueError

                volume = tank_capacity * loading / 100.0
                mass_tonnes = volume * density / 1000.0

                total_volume += volume

                capacity_label, volume_label, mass_label = (
                    self.tank_result_labels[index]
                )

                capacity_label.config(text=f"{tank_capacity:,.1f}")
                volume_label.config(text=f"{volume:,.1f}")
                mass_label.config(text=f"{mass_tonnes:,.1f}")

                if loading > fill_limit:
                    warnings.append(
                        f"Tank {index + 1} exceeds the fill limit "
                        f"({loading:.1f}% > {fill_limit:.1f}%)."
                    )

            total_mass = total_volume * density / 1000.0
            remaining = capacity - total_volume
            overall_loading = total_volume / capacity * 100.0

            self.cargo_volume_label.config(
                text=f"Cargo volume: {total_volume:,.1f} m³ "
                    f"({overall_loading:.2f}% overall)"
            )

            self.cargo_mass_label.config(
                text=f"Cargo mass: {total_mass:,.1f} tonnes"
            )

            self.remaining_capacity_label.config(
                text=f"Remaining capacity: {remaining:,.1f} m³"
            )

            if warnings:
                warning_text = "\n".join(warnings)
                self.cargo_warning_label.config(
                    text=warning_text,
                    foreground="red"
                )
            else:
                self.cargo_warning_label.config(
                    text="All tank loading percentages are within the "
                        "configured fill limit.",
                    foreground="green"
                )

        except (tk.TclError, ValueError, ZeroDivisionError):
            self.cargo_volume_label.config(text="Cargo volume: check inputs")
            self.cargo_mass_label.config(text="Cargo mass: check inputs")
            self.remaining_capacity_label.config(
                text="Remaining capacity: check inputs"
            )
            self.cargo_warning_label.config(
                text="Enter valid numeric values. Tank loading must be 0–100%.",
                foreground="red"
            )

# -------------------------------
# Main program entry point
if __name__ == "__main__":
    app = QMaxShipCanvas()
    app.mainloop()
