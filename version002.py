
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
        self.heading = 45.0
        
        
        
        # ==================================================
        # 7A. TUG CONFIGURATION
        # ==================================================

        # Tug bollard pull and efficiency
        self.tug_bollard_pull_tf = 70.0  # tonnes-force per tug
        self.tug_efficiency = 0.75       # 75% assumed efficiency

        # Tug positions are measured relative to the vessel CG.
        #
        # Local coordinate system:
        # +X = Bow (forward)
        # -X = Stern (aft)
        # +Y = Starboard
        # -Y = Port
        #
        # These are preliminary positions from our
        # earlier manual calculation.

        self.tug_config = [
            
            {
                "name": "Tug 1",

                # Ship attachment point
                "x_m": 138.0,
                "y_m": 9.4,

                # Tugboat centre position
                "tug_x_m": 138.0,
                "tug_y_m": 40.0,

                "pull_angle_deg": 25.0,
                "longitudinal_sign": -1,
                "transverse_sign": 1
            },

            {
                "name": "Tug 2",
                "x_m": 138.0,
                "y_m": -9.4,
                
                # Tugboat centre position
                "tug_x_m": 138.0,
                "tug_y_m": -40.0,
                
                "pull_angle_deg": 30.0,
                "longitudinal_sign": -1,
                "transverse_sign": 1
            },

            {
                "name": "Tug 3",
                "x_m": -138.0,
                "y_m": 24.5,
                
                # Tugboat centre position
                "tug_x_m": -138.0,
                "tug_y_m": 40.0,
                
                "pull_angle_deg": 25.0,
                "longitudinal_sign": 1,
                "transverse_sign": 1
            },

            {
                "name": "Tug 4",
                "x_m": -138.0,
                "y_m": -24.5,
                
                # Tugboat centre position
                "tug_x_m": -138.0,
                "tug_y_m": -40.0,
                
                "pull_angle_deg": 30.0,
                "longitudinal_sign": 1,
                "transverse_sign": 1
            }
        ]

        # Display the configured tug data once at startup.
        print("\n========== TUG CONFIGURATION ==========")

        for tug in self.tug_config:
            print(
                f"{tug['name']}: "
                f"Position=({tug['x_m']}, {tug['y_m']}) m | "
                f"Angle={tug['pull_angle_deg']} degrees | "
                f"BP={self.tug_bollard_pull_tf} tf"
            )

        print("======================================\n")
        
        
        # Independent tug steering
        self.tug_turn_rate = 30.0  # degrees per second
        self.tug_rotation_keys = {
            "Tug 1": ("a", "d"), # Left, Right 
            "Tug 2": ("j", "l"), # Left, Right
            "Tug 3": ("f", "h"), # Left, Right
            "Tug 4": ("k", "semicolon")  # Left, Right
        }
        
        # Independent tug movement settings
        self.tug_move_speed = 2.0  # metres per second

        # Forward and backward movement keys
        self.tug_movement_keys = {
            "Tug 1": ("w", "s"),
            "Tug 2": ("t", "g"),
            "Tug 3": ("i", "m"),
            "Tug 4": ("y", "n")
        }
        
        # ---------------------------------
        # Towline configuration
        # ---------------------------------
        
        # Maximum deployed towline length per tug
        self.towline_length_m = 50.0  # metres
        
        
        self.initialize_tug_positions()
        
        self.calculate_tug_forces()
        
        
        # ==================================================
        # STAGE 3: TUG GRAPHICS SETTINGS
        # ==================================================

        self.tug_length_px = 28
        self.tug_beam_px = 12

        # Store canvas IDs for each tug
        self.tug_canvas_items = []


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

        # Visual wind animation speed (pixels per update)
        self.wind_visual_speed = 1.6

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
        self.ship_speed = 0.0

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

        # Draw and animate ocean current
        self.draw_ocean_current()

        # Draw and animate wind independently of the ocean current
        self.draw_wind()

        # Draw vessel over the environmental animations
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
        
        
        # self.test_vessel_coordinates()
        self.draw_tugs()

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
        
        # Update saved tug positions around the ship centre
        for tug in self.tug_config:

            tug["canvas_x"] = (
                cx + (tug["canvas_x"] - cx) * factor
            )

            tug["canvas_y"] = (
                cy + (tug["canvas_y"] - cy) * factor
            )

        # Scale the ship drawing around its centre
        self.canvas.scale("ship", cx, cy, factor, factor)
        # self.canvas.scale("tug", cx, cy, factor, factor)

        self.zoom_level = new_zoom
        
        # Redraw tugs and towlines using updated positions
        self.draw_tugs()
        
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
        
        # Restore tug positions around the ship centre
        cx = self.ship_center_x
        cy = self.ship_center_y

        for tug in self.tug_config:

            tug["canvas_x"] = (
                cx + (tug["canvas_x"] - cx) * factor
            )

            tug["canvas_y"] = (
                cy + (tug["canvas_y"] - cy) * factor
            )

        self.canvas.scale(
            "ship",
            self.ship_center_x,
            self.ship_center_y,
            factor,
            factor
        )

        self.zoom_level = 1.0
        # Redraw tugs and towlines at original zoom
        self.draw_tugs()
        self.draw_grid()
        self.draw_scale_indicator()
        self.zoom_label.config(text="Zoom: 100%")
        
        


    # -------------------------------
    # 1. Ship drawing
    # -------------------------------
    def draw_ship(self):

        c = self.canvas

        cx = self.ship_center_x
        cy = self.ship_center_y

        half_length = SHIP_LENGTH / 2
        half_beam = SHIP_BEAM / 2

        # Convert heading into radians.
        # Original drawing points EAST (90 degrees).
        angle = math.radians(self.heading - 90)
        
        
        def rotate_point(x, y):
            """
            Correct the original ship drawing coordinates,
            then rotate around the vessel reference centre.
            """

            # 1. Shift the original drawing towards its geometric centre
            x = x - (half_length * 0.25)

            # 2. Expand the longitudinal dimension to the full LOA
            x = x * (4.0 / 3.0)

            # 3. Rotate the corrected coordinates
            rotated_x = x * math.cos(angle) - y * math.sin(angle)
            rotated_y = x * math.sin(angle) + y * math.cos(angle)

            # 4. Return final canvas coordinates
            return cx + rotated_x, cy + rotated_y
        
        

        def rotate_coordinates(points):
            result = []

            for x, y in points:
                rx, ry = rotate_point(x, y)
                result.extend([rx, ry])

            return result

        # ---------------------------------
        # 1. Outer hull
        # ---------------------------------

        # hull_points = [
        #     (half_length, 0),
        #     (half_length * 0.72, -half_beam * 0.65),
        #     (-half_length * 0.25, -half_beam),
        #     (-half_length * 0.42, -half_beam * 0.85),
        #     (-half_length * 0.50, 0),
        #     (-half_length * 0.42, half_beam * 0.85),
        #     (-half_length * 0.25, half_beam),
        #     (half_length * 0.72, half_beam * 0.65)
        # ]
        
        
        # Local ship coordinates
        hull_points = [

            # Bow centre
            (half_length, 0),

            # Upper bow curve
            (half_length * 0.98, -half_beam * 0.20),
            (half_length * 0.94, -half_beam * 0.40),
            (half_length * 0.88, -half_beam * 0.54),
            (half_length * 0.80, -half_beam * 0.62),

            # Upper bow shoulder
            (half_length * 0.72, -half_beam * 0.65),

            # Upper stern
            (-half_length * 0.25, -half_beam),
            (-half_length * 0.42, -half_beam * 0.85),

            # Stern centre
            (-half_length * 0.50, 0),

            # Lower stern
            (-half_length * 0.42, half_beam * 0.85),
            (-half_length * 0.25, half_beam),

            # Lower bow shoulder
            (half_length * 0.72, half_beam * 0.65),

            # Lower bow curve
            (half_length * 0.80, half_beam * 0.62),
            (half_length * 0.88, half_beam * 0.54),
            (half_length * 0.94, half_beam * 0.40),
            (half_length * 0.98, half_beam * 0.20)
        ]

        # c.create_polygon(
        #     rotate_coordinates(hull_points),
        #     fill="gray",
        #     outline="black",
        #     tags="ship"
        # )
        
        # Create the ship polygon on the canvas 
        c.create_polygon(
            rotate_coordinates(hull_points),
            fill="gray",
            outline="black",
            width=2,
            smooth=True,
            splinesteps=3,
            tags="ship"
        )

        
        # ---------------------------------
        # 2. Inner deck
        # ---------------------------------

        deck_points = [

            # Bow centre
            (half_length * 0.91, 0),

            # Upper deck bow curve
            (half_length * 0.89, -half_beam * 0.16),
            (half_length * 0.86, -half_beam * 0.32),
            (half_length * 0.81, -half_beam * 0.44),
            (half_length * 0.75, -half_beam * 0.51),

            # Upper bow shoulder
            (half_length * 0.65, -half_beam * 0.52),

            # Upper stern
            (-half_length * 0.25, -half_beam * 0.78),
            (-half_length * 0.38, -half_beam * 0.65),

            # Stern centre
            (-half_length * 0.43, 0),

            # Lower stern
            (-half_length * 0.38, half_beam * 0.65),
            (-half_length * 0.25, half_beam * 0.78),

            # Lower bow shoulder
            (half_length * 0.65, half_beam * 0.52),

            # Lower deck bow curve
            (half_length * 0.75, half_beam * 0.51),
            (half_length * 0.81, half_beam * 0.44),
            (half_length * 0.86, half_beam * 0.32),
            (half_length * 0.89, half_beam * 0.16)
        ]

        c.create_polygon(
            rotate_coordinates(deck_points),
            fill="#254c60",
            outline="#8bb8ca",
            width=2,
            smooth=True,
            splinesteps=12,
            tags="ship"
        )


        # ---------------------------------
        # 3. Four LNG tanks
        # ---------------------------------

        tank_width = 48
        tank_height = 48

        for i in range(4):

            tank_x = -45 + i * 55
            tank_y = 0

            tank_points = [
                (tank_x - tank_width / 2, tank_y - tank_height / 2),
                (tank_x + tank_width / 2, tank_y - tank_height / 2),
                (tank_x + tank_width / 2, tank_y + tank_height / 2),
                (tank_x - tank_width / 2, tank_y + tank_height / 2)
            ]

            c.create_polygon(
                rotate_coordinates(tank_points),
                fill="#b8dce8",
                outline="#e8f7fc",
                width=2,
                tags="ship"
            )

            text_x, text_y = rotate_point(tank_x, tank_y)

            c.create_text(
                text_x,
                text_y,
                text=f"LNG {i + 1}",
                fill="#173748",
                font=("Arial", 9, "bold"),
                angle=math.degrees(angle),
                tags="ship"
            )

        # ---------------------------------
        # 4. Bridge near the stern
        # ---------------------------------

        bridge_x = -half_length * 0.42

        bridge_points = [
            (bridge_x - 22, -27),
            (bridge_x + 15, -27),
            (bridge_x + 15, 27),
            (bridge_x - 22, 27)
        ]

        c.create_polygon(
            rotate_coordinates(bridge_points),
            fill="#f0c477",
            outline="#fff0c8",
            width=2,
            tags="ship"
        )

        bridge_inner_points = [
            (bridge_x - 16, -19),
            (bridge_x - 5, -19),
            (bridge_x - 5, 19),
            (bridge_x - 16, 19)
        ]

        c.create_polygon(
            rotate_coordinates(bridge_inner_points),
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
    # 4. Draw wind arrows
    def draw_wind(self):
        """Draw animated wind-flow arrows across the canvas."""

        self.wind_items = []

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1:
            canvas_width = WINDOW_WIDTH
        if canvas_height <= 1:
            canvas_height = WINDOW_HEIGHT

        spacing_x = 140
        spacing_y = 120
        arrow_length = 32

        # Wind direction is the direction TOWARDS which the wind blows.
        angle = math.radians(self.wind_direction)
        dx = math.sin(angle) * arrow_length
        dy = -math.cos(angle) * arrow_length

        for x in range(60, canvas_width, spacing_x):
            for y in range(110, canvas_height, spacing_y):
                item = self.canvas.create_line(
                    x,
                    y,
                    x + dx,
                    y + dy,
                    fill="#f4e6b5",
                    width=2,
                    dash=(5, 4),
                    arrow=tk.LAST,
                    tags=("wind",)
                )
                self.wind_items.append(item)

        # The ship is drawn after the wind, so it naturally appears above it.
        self.animate_wind()


    # -------------------------------
    # 5. Wind animation update
    def animate_wind(self):
        """Move wind arrows continuously in the selected wind direction."""

        angle = math.radians(self.wind_direction)

        move_x = math.sin(angle) * self.wind_visual_speed
        move_y = -math.cos(angle) * self.wind_visual_speed

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1:
            width = WINDOW_WIDTH
        if height <= 1:
            height = WINDOW_HEIGHT

        margin = 45

        for item in self.wind_items:
            self.canvas.move(item, move_x, move_y)

            coords = self.canvas.coords(item)
            if len(coords) < 4:
                continue

            x1, y1, x2, y2 = coords

            # Wrap horizontally when the arrow leaves the canvas.
            if x1 > width + margin:
                self.canvas.move(item, -width - 2 * margin, 0)
            elif x2 < -margin:
                self.canvas.move(item, width + 2 * margin, 0)

            # Wrap vertically when the arrow leaves the canvas.
            if y1 > height + margin:
                self.canvas.move(item, 0, -height - 2 * margin)
            elif y2 < -margin:
                self.canvas.move(item, 0, height + 2 * margin)

        self.after(50, self.animate_wind)


    # -------------------------------
    # 4. Keyboard input handling
    def key_down(self, event):
        self.keys_pressed.add(event.keysym)
        
        

    def key_up(self, event):
        self.keys_pressed.discard(event.keysym)
        
        

    def update_tug_headings(self, dt):
        """Rotate each tug independently using keyboard controls."""

        for tug in self.tug_config:

            tug_name = tug["name"]

            # Get the left and right rotation keys for this tug
            left_key, right_key = self.tug_rotation_keys[tug_name]

            # Rotate left (port)
            if left_key in self.keys_pressed and right_key not in self.keys_pressed:

                tug["heading"] -= self.tug_turn_rate * dt

            # Rotate right (starboard)
            elif right_key in self.keys_pressed and left_key not in self.keys_pressed:

                tug["heading"] += self.tug_turn_rate * dt

            # Keep heading between 0 and 360 degrees
            tug["heading"] %= 360

    
    #------------------------------- Tug movement update -------------------------------
    def update_tug_movement(self, dt):
        """Move each tug independently according to its own heading."""

        for tug in self.tug_config:

            tug_name = tug["name"]

            # Check whether movement keys are configured for this tug
            if tug_name not in self.tug_movement_keys:
                continue

            forward_key, backward_key = self.tug_movement_keys[tug_name]

            # Determine movement direction
            movement = 0

            if forward_key in self.keys_pressed and backward_key not in self.keys_pressed:
                movement = 1

            elif backward_key in self.keys_pressed and forward_key not in self.keys_pressed:
                movement = -1

            # No movement command
            if movement == 0:
                continue

            # Convert tug heading into radians
            heading_rad = math.radians(tug["heading"])

            # Calculate movement distance in metres
            distance = self.tug_move_speed * dt * movement

            # Convert movement into canvas pixels
            pixel_distance = (
                distance
                * self.pixels_per_meter
                * self.zoom_level
            )

            # Calculate movement along the tug's heading
            dx = pixel_distance * math.sin(heading_rad)
            dy = -pixel_distance * math.cos(heading_rad)

            # Update independent tug position
            tug["canvas_x"] += dx
            tug["canvas_y"] += dy
        
        
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
        
        
        apparent_wind_direction = (
            math.degrees(
                math.atan2(relative_wind_x, -relative_wind_y)
            ) % 360
        )

        print(f"Apparent wind speed: {relative_wind_speed:.3f} m/s")
        print(f"Apparent wind direction: {apparent_wind_direction:.2f}°")
        
        
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
        
        # Update individual tug headings
        self.update_tug_headings(dt)
        
        # Update independent tug movement
        self.update_tug_movement(dt)
        
        # Update tugboat positions after ship movement and rotation
        self.draw_tugs()


        # 8. CONTINUE THE SIMULATION
        self.after(30, self.update_ship)
        
        
        
    
    # ==================================================
    # STAGE 3.1: DRAW ONE TUGBOAT
    # ==================================================

    def draw_one_tug(self, center_x, center_y, heading, tug_name):

        # half_length = self.tug_length_px / 2
        # half_beam = self.tug_beam_px / 2
        
        # Apply the current zoom level to tugboat dimensions
        zoom = self.zoom_level

        half_length = (self.tug_length_px * zoom) / 2
        half_beam = (self.tug_beam_px * zoom) / 2

        # Scale the bow and stern shape details
        bow_offset = 7 * zoom
        stern_offset = 4 * zoom

    #   Define the tugboat shape as a polygon
        points = [
            (0, -half_length),
            (half_beam, -half_length + bow_offset),
            (half_beam, half_length - stern_offset),
            (0, half_length),
            (-half_beam, half_length - stern_offset),
            (-half_beam, -half_length + bow_offset)
        ]

        # Rotate the tugboat according to its heading
        angle_rad = math.radians(heading)

        rotated_points = []

        for x, y in points:

            rotated_x = (
                x * math.cos(angle_rad)
                - y * math.sin(angle_rad)
            )

            rotated_y = (
                x * math.sin(angle_rad)
                + y * math.cos(angle_rad)
            )

            rotated_points.extend([
                center_x + rotated_x,
                center_y + rotated_y
            ])

        # Draw tugboat hull
        hull = self.canvas.create_polygon(
            rotated_points,
            fill="#008000",
            outline="white",
            width=1,
            tags=("tug",)
        )

        # Draw tug name
        label = self.canvas.create_text(
            center_x,
            center_y + 22 * zoom,
            text=tug_name,
            fill="white",
            font=("Arial", max(6, int(8 * zoom)), "bold"),
            tags=("tug",)
        )

        return [hull, label]
    
    
    
    # ==================================================
    # STAGE 3.2: CONVERT VESSEL POSITION TO CANVAS
    # ==================================================

    def vessel_to_canvas(self, local_x, local_y):

        # Convert ship heading into radians
        heading_rad = math.radians(self.heading)

        # Convert vessel-local position into canvas position
        rotated_x = (
            local_x * math.sin(heading_rad)
            + local_y * math.cos(heading_rad)
        )

        rotated_y = (
            -local_x * math.cos(heading_rad)
            + local_y * math.sin(heading_rad)
        )

        # Convert metres into pixels
        # pixel_x = rotated_x * self.pixels_per_meter
        # pixel_y = rotated_y * self.pixels_per_meter
        
        pixel_x = rotated_x * self.pixels_per_meter * self.zoom_level
        pixel_y = rotated_y * self.pixels_per_meter * self.zoom_level

        # Add ship centre position
        canvas_x = self.ship_center_x + pixel_x
        canvas_y = self.ship_center_y + pixel_y

        return canvas_x, canvas_y
    
    
    
    # ==================================================
    # STAGE 3.3: TEST VESSEL COORDINATES
    # ==================================================

    def test_vessel_coordinates(self):

        original_heading = self.heading

        print("\n========== COORDINATE TEST ==========")

        # Test 1: Ship heading North
        self.heading = 0

        bow_x, bow_y = self.vessel_to_canvas(100, 0)
        starboard_x, starboard_y = self.vessel_to_canvas(0, 100)

        print("\nShip heading: 0 degrees (North)")
        print(
            f"Bow position: "
            f"X={bow_x - self.ship_center_x:.2f}, "
            f"Y={bow_y - self.ship_center_y:.2f} pixels"
        )
        print(
            f"Starboard position: "
            f"X={starboard_x - self.ship_center_x:.2f}, "
            f"Y={starboard_y - self.ship_center_y:.2f} pixels"
        )

        # Test 2: Ship heading East
        self.heading = 90

        bow_x, bow_y = self.vessel_to_canvas(100, 0)
        starboard_x, starboard_y = self.vessel_to_canvas(0, 100)

        print("\nShip heading: 90 degrees (East)")
        print(
            f"Bow position: "
            f"X={bow_x - self.ship_center_x:.2f}, "
            f"Y={bow_y - self.ship_center_y:.2f} pixels"
        )
        print(
            f"Starboard position: "
            f"X={starboard_x - self.ship_center_x:.2f}, "
            f"Y={starboard_y - self.ship_center_y:.2f} pixels"
        )

        # Restore the original heading
        self.heading = original_heading

        print("\n====================================\n")
        
        
    
    # ==================================================
    # STAGE 3.4: DRAW ALL FOUR TUGBOATS
    # ==================================================
        
    # def draw_tugs(self):

    #     self.canvas.delete("tug")
    #     self.tug_canvas_items = []

    #     for tug in self.tug_config:

    #         # Use tugboat centre coordinates
    #         tug_x, tug_y = self.vessel_to_canvas(
    #             tug["tug_x_m"],
    #             tug["tug_y_m"]
    #         )

    #         tug_items = self.draw_one_tug(
    #             tug_x,
    #             tug_y,
    #             self.heading,
    #             tug["name"]
    #         )

    #         self.tug_canvas_items.append(tug_items)

    #     # Draw all towlines once, after positioning the tugs
    #     self.draw_towlines()
    
    
    
    def draw_tugs(self):

        self.canvas.delete("tug")
        self.tug_canvas_items = []

        for tug in self.tug_config:

            # Use the saved independent canvas position
            tug_x = tug["canvas_x"]
            tug_y = tug["canvas_y"]

            tug_items = self.draw_one_tug(
                tug_x,
                tug_y,
                # self.heading,
                tug["heading"],
                tug["name"]
            )

            self.tug_canvas_items.append(tug_items)

        # Redraw towlines after positioning all tugs
        self.draw_towlines()


    def draw_towlines(self):

        # Remove previous towlines
        self.canvas.delete("towline")

        # Vessel heading in radians
        # heading_rad = math.radians(self.heading)

        for tug in self.tug_config:
            
            # Vessel heading in radians
            # Individual tug heading in radians
            heading_rad = math.radians(tug["heading"])

            # 1. Ship attachment point
            ship_x, ship_y = self.vessel_to_canvas(
                tug["x_m"],
                tug["y_m"]
            )

            # 2. Tugboat centre position
            # tug_x, tug_y = self.vessel_to_canvas(
            #     tug["tug_x_m"],
            #     tug["tug_y_m"]
            # )
            
            # 2. Tugboat centre position
            # Use saved independent canvas coordinates
            tug_x = tug["canvas_x"]
            tug_y = tug["canvas_y"]

            # 3. Distance from tug centre to its hull edge
            half_beam = (
                self.tug_beam_px
                * self.zoom_level
                / 2
            )

            # 4. Determine which side faces the Q-Max
            # if tug["tug_y_m"] > 0:
            #     inward_direction = -1
            # else:
            #     inward_direction = 1
            
            
            
            # 4. Determine which side of the tug faces the Q-Max

            # Vector from tug centre towards ship attachment
            dx = ship_x - tug_x
            dy = ship_y - tug_y

            # Project this direction onto the tug's beam axis
            toward_ship = (
                dx * math.cos(heading_rad)
                + dy * math.sin(heading_rad)
            )

            # Select the inward-facing side
            if toward_ship >= 0:
                inward_direction = 1
            else:
                inward_direction = -1


            # 5. Calculate inward-facing hull connection point
            connection_x = (
                tug_x
                + inward_direction * half_beam * math.cos(heading_rad)
            )

            connection_y = (
                tug_y
                + inward_direction * half_beam * math.sin(heading_rad)
            )
            
            
            # 6. Calculate actual towline distance in pixels
            distance_px = math.hypot(
                connection_x - ship_x,
                connection_y - ship_y
            )

            # Convert canvas distance into metres
            display_scale = (
                self.pixels_per_meter * self.zoom_level
            )

            distance_m = distance_px / display_scale

            # Save the calculated distance for this tug
            tug["towline_distance_m"] = distance_m

            # Determine whether the towline has reached its limit
            tug["towline_status"] = (
                "TAUT"
                if distance_m >= self.towline_length_m
                else "SLACK"
            )

            # 7. Draw towline
            # self.canvas.create_line(
            #     ship_x, ship_y,
            #     connection_x, connection_y,
            #     fill="#f5a623",
            #     width=max(1, 2 * self.zoom_level),
            #     tags=("towline",)
            # )
            
            # 7. Draw towline based on its status

            if tug["towline_status"] == "TAUT":

                # TAUT towline: straight red line
                self.canvas.create_line(
                    ship_x, ship_y,
                    connection_x, connection_y,
                    fill="#ff3333",
                    width=max(1, 2 * self.zoom_level),
                    tags=("towline",)
                )

            else:

                # SLACK towline: slightly curved orange line

                # Midpoint between ship and tug connection
                mid_x = (ship_x + connection_x) / 2
                mid_y = (ship_y + connection_y) / 2

                # Calculate perpendicular direction
                line_dx = connection_x - ship_x
                line_dy = connection_y - ship_y

                line_length = math.hypot(line_dx, line_dy)

                if line_length > 0:

                    # Small curve offset
                    curve_amount = 8 * self.zoom_level

                    curve_x = mid_x - (line_dy / line_length) * curve_amount
                    curve_y = mid_y + (line_dx / line_length) * curve_amount

                else:
                    curve_x = mid_x
                    curve_y = mid_y

                # Draw curved slack towline
                self.canvas.create_line(
                    ship_x, ship_y,
                    curve_x, curve_y,
                    connection_x, connection_y,
                    fill="#f5a623",
                    width=max(1, 2 * self.zoom_level),
                    smooth=True,
                    splinesteps=24,
                    tags=("towline",)
                )
    
            # print(
            #     tug["name"],
            #     "Distance:", round(tug["towline_distance_m"], 2), "m",
            #     "Status:", tug["towline_status"]
            # )

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
            
            
    
    # ==================================================
    # STAGE 2: TUG FORCE CALCULATION
    # ==================================================

    def calculate_tug_forces(self):

        print("\n========== TUG FORCE CALCULATION ==========")

        # 1. Calculate effective bollard pull
        effective_bp = (
            self.tug_bollard_pull_tf * self.tug_efficiency
        )

        print(f"Effective BP per tug: {effective_bp:.2f} tf")

        # 2. Store calculated results
        self.tug_force_results = []

        # 3. Calculate force components for each tug
        for tug in self.tug_config:

            # Convert pulling angle from degrees to radians
            angle_rad = math.radians(tug["pull_angle_deg"])

            # Calculate force magnitudes
            longitudinal_force = effective_bp * math.sin(angle_rad)

            transverse_force = effective_bp * math.cos(angle_rad)

            # Apply direction signs
            longitudinal_force *= tug["longitudinal_sign"]

            transverse_force *= tug["transverse_sign"]

            # Store the results
            result = {
                "name": tug["name"],
                "Fx_tf": longitudinal_force,
                "Fy_tf": transverse_force
            }

            self.tug_force_results.append(result)

            # Display individual tug results
            print(
                f"{tug['name']}: "
                f"Fx = {longitudinal_force:+.2f} tf | "
                f"Fy = {transverse_force:+.2f} tf"
            )

        # 4. Calculate total tug forces
        total_fx = sum(
            tug["Fx_tf"] for tug in self.tug_force_results
        )

        total_fy = sum(
            tug["Fy_tf"] for tug in self.tug_force_results
        )

        print("-------------------------------------------")
        print(f"Total longitudinal force: {total_fx:+.2f} tf")
        print(f"Total transverse force:   {total_fy:+.2f} tf")

        print("===========================================\n")
        
        
        
    def initialize_tug_positions(self):
        """Calculate and save the initial canvas position of each tug."""

        for tug in self.tug_config:

            tug_x, tug_y = self.vessel_to_canvas(
                tug["tug_x_m"],
                tug["tug_y_m"]
            )

            # Save independent canvas coordinates
            tug["canvas_x"] = tug_x
            tug["canvas_y"] = tug_y
            
            # Give each tug its own initial heading
            tug["heading"] = self.heading
            
            # tug["heading"] = self.heading

            # Temporary test: rotate only Tug 1 by 45 degrees
            # if tug["name"] == "Tug 1":
            #     tug["heading"] = (self.heading + 45) % 360
            # Temporary test: END


# -------------------------------
# Main program entry point
#--------------------------------

if __name__ == "__main__":
    app = QMaxShipCanvas()
    app.mainloop()
