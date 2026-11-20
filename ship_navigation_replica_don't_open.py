import tkinter as tk
import math
import time
import random


class ShipNavigationReplica:
    """
    Standalone Tkinter recreation of the supplied ship-navigation screenshot.
    No external packages or image assets are required.
    """

    OCEAN = "#064987"
    ROUTE = "#ff8125"
    TRACK = "#16a7ff"
    PANEL = "#969696"
    PANEL_DARK = "#666666"
    TEXT = "#111111"

    def __init__(self, root):
        self.root = root
        self.root.title("Ship Navigation Simulator - UI Replica")
        self.root.geometry("1366x768")
        self.root.minsize(900, 600)
        self.root.configure(bg="#061c35")

        self.canvas = tk.Canvas(
            root, bg=self.OCEAN, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.heading = 129.5
        self.mag = 118.3
        self.cog = 123.1
        self.sog = 10.3
        self.set_direction = 340.4
        self.drift = 2.2
        self.rot = 1.0
        self.rad = 8.22

        self.route_points_normalized = [
            (0.09, 1.02), (0.17, 0.56), (0.25, 0.36),
            (0.36, 0.24), (0.48, 0.20), (0.60, 0.23),
            (0.72, 0.35), (0.81, 0.55), (0.89, 1.02)
        ]
        self.ship_x = 0.78
        self.ship_y = 0.53
        self.ship_heading = 150.0
        self.started = time.time()
        self.last_time = time.time()
        self.animate = True

        self.canvas.bind("<Configure>", self.on_resize)
        self.root.bind("<Escape>", lambda _e: self.root.destroy())
        self.root.bind("<space>", self.toggle_animation)

        self.draw()

    def on_resize(self, _event=None):
        self.draw()

    def toggle_animation(self, _event=None):
        self.animate = not self.animate

    def xy(self, normalized_point):
        w = max(self.canvas.winfo_width(), 1)
        h = max(self.canvas.winfo_height(), 1)
        return normalized_point[0] * w, normalized_point[1] * h

    def draw_ocean(self, w, h):
        self.canvas.create_rectangle(0, 0, w, h, fill=self.OCEAN, outline="")
        # Subtle patches of reflected light, similar to the reference image.
        random.seed(8)
        for _ in range(180):
            x = random.uniform(w * 0.30, w * 0.73)
            y = random.uniform(h * 0.47, h * 0.78)
            length = random.uniform(1.5, 5.0)
            self.canvas.create_line(
                x, y, x + length, y - random.uniform(0, 1.8),
                fill=random.choice(["#1762a0", "#1a5c96", "#2673ad", "#0d5592"]),
                width=random.choice([1, 1, 2])
            )

    def draw_route(self, w, h):
        points = []
        for p in self.route_points_normalized:
            points.extend(self.xy(p))
        self.canvas.create_line(
            *points, fill=self.ROUTE, width=2.5, smooth=False,
            joinstyle=tk.ROUND
        )

    def draw_ship(self, w, h):
        # Ship is drawn around a local origin, then rotated to its heading.
        cx, cy = self.ship_x * w, self.ship_y * h
        length = min(w, h) * 0.23
        beam = length * 0.20
        # Local coordinates: bow at the top, stern at the bottom.
        local = [
            (0, -length * 0.58),
            (-beam * 0.42, -length * 0.37),
            (-beam * 0.50, length * 0.30),
            (-beam * 0.22, length * 0.55),
            (beam * 0.22, length * 0.55),
            (beam * 0.50, length * 0.30),
            (beam * 0.42, -length * 0.37),
        ]
        angle = math.radians(self.ship_heading)
        # Rotate from the "bow up" drawing orientation.
        rotated = []
        for x, y in local:
            rx = x * math.cos(angle) - y * math.sin(angle)
            ry = x * math.sin(angle) + y * math.cos(angle)
            rotated.extend((cx + rx, cy + ry))

        self.canvas.create_polygon(
            *rotated, fill="#7b4c37", outline="#d5c5b5", width=1.5
        )

        # Deck / cargo hatch rectangles are kept aligned with the ship.
        for i in range(4):
            yy = -length * 0.22 + i * length * 0.17
            hatch = [
                (-beam * 0.27, yy - length * 0.055),
                (beam * 0.27, yy - length * 0.055),
                (beam * 0.27, yy + length * 0.055),
                (-beam * 0.27, yy + length * 0.055),
            ]
            coords = []
            for x, y in hatch:
                rx = x * math.cos(angle) - y * math.sin(angle)
                ry = x * math.sin(angle) + y * math.cos(angle)
                coords.extend((cx + rx, cy + ry))
            self.canvas.create_polygon(
                *coords, fill="#f2eee2", outline="#c5b9a8", width=0.7
            )

        # Bow bridge / superstructure.
        bridge = [
            (-beam * 0.27, -length * 0.43),
            (beam * 0.27, -length * 0.43),
            (beam * 0.24, -length * 0.29),
            (-beam * 0.24, -length * 0.29),
        ]
        coords = []
        for x, y in bridge:
            rx = x * math.cos(angle) - y * math.sin(angle)
            ry = x * math.sin(angle) + y * math.cos(angle)
            coords.extend((cx + rx, cy + ry))
        self.canvas.create_polygon(
            *coords, fill="#d9d4c9", outline="#9f978a", width=0.8
        )

        # Wake trails behind the stern.
        stern_x = cx + (math.sin(angle) * length * 0.52)
        stern_y = cy + (math.cos(angle) * length * 0.52)
        wake_end_x = stern_x + math.sin(angle) * length * 0.85
        wake_end_y = stern_y + math.cos(angle) * length * 0.85
        self.canvas.create_line(
            stern_x, stern_y, wake_end_x, wake_end_y,
            fill="#7ec8f5", width=7, stipple="gray50", capstyle=tk.ROUND
        )
        self.canvas.create_line(
            stern_x, stern_y, wake_end_x, wake_end_y,
            fill="#b3e2ff", width=2, stipple="gray50"
        )

        # Blue track line trailing from the ship.
        track_start = (cx + math.sin(angle) * length * 0.45,
                       cy + math.cos(angle) * length * 0.45)
        track_end = (cx + math.sin(angle) * length * 2.1,
                     cy + math.cos(angle) * length * 2.1)
        self.canvas.create_line(
            *track_start, *track_end, fill=self.TRACK, width=3
        )

    def draw_top_instruments(self, w):
        # Instrument strip from the screenshot.
        labels = [
            ("HDG", f"{self.heading:.1f}°"),
            ("MAG", f"{self.mag:.1f}°"),
            ("COG", f"{self.cog:.1f}°"),
            ("SOG", f"{self.sog:.1f}"),
            ("SET", f"{self.set_direction:.1f}°"),
            ("DRIFT", f"{self.drift:.1f}"),
            ("ROT", f"{self.rot:.0f}"),
            ("RAD", f"{self.rad:.2f}"),
        ]
        x = 8
        y = 10
        box_h = 25
        gap = 5
        available = max(w - 16, 1)
        cell_w = (available - gap * (len(labels) - 1)) / len(labels)
        for label, value in labels:
            self.canvas.create_rectangle(
                x, y, x + cell_w, y + box_h,
                fill="#b8b8b8", outline="#686868"
            )
            self.canvas.create_text(
                x + 5, y + box_h / 2, text=label,
                anchor="w", font=("Arial", 9, "bold"), fill="#202020"
            )
            value_width = min(cell_w * 0.66, 75)
            self.canvas.create_rectangle(
                x + cell_w - value_width - 3, y + 3,
                x + cell_w - 3, y + box_h - 3,
                fill="#f1f1f1", outline="#888888"
            )
            self.canvas.create_text(
                x + cell_w - value_width / 2 - 3, y + box_h / 2,
                text=value, font=("Arial", 10, "bold"), fill="#111111"
            )
            x += cell_w + gap

    def draw_gauge(self, x, y, radius):
        self.canvas.create_oval(
            x-radius, y-radius, x+radius, y+radius,
            fill="#398c96", outline="#4c6d72", width=2
        )
        self.canvas.create_oval(
            x-radius*0.76, y-radius*0.76, x+radius*0.76, y+radius*0.76,
            fill="#d8e0e0", outline="#b0c4c4", width=2
        )
        for deg in range(0, 360, 15):
            a = math.radians(deg - 90)
            inner = radius * (0.80 if deg % 45 else 0.72)
            outer = radius * 0.91
            self.canvas.create_line(
                x + math.cos(a)*inner, y + math.sin(a)*inner,
                x + math.cos(a)*outer, y + math.sin(a)*outer,
                fill="#123f52", width=2 if deg % 45 == 0 else 1
            )
        for deg, txt in [(0, "0"), (90, "90"), (180, "180"), (270, "270")]:
            a = math.radians(deg - 90)
            self.canvas.create_text(
                x + math.cos(a)*radius*0.60,
                y + math.sin(a)*radius*0.60,
                text=txt, font=("Arial", 7, "bold"), fill="#234b55"
            )
        # Heading needle
        a = math.radians(self.heading - 90)
        self.canvas.create_line(
            x, y, x + math.cos(a)*radius*0.55, y + math.sin(a)*radius*0.55,
            fill="#183f8a", width=4, arrow=tk.LAST
        )
        self.canvas.create_rectangle(
            x-radius*0.20, y-radius*0.20, x+radius*0.20, y+radius*0.20,
            fill="#13852b", outline="#222222"
        )
        self.canvas.create_text(
            x, y, text="N", font=("Arial", 9, "bold"), fill="#101010"
        )

    def button(self, x, y, width, height, label, color="#c47a17"):
        self.canvas.create_rectangle(
            x, y, x+width, y+height, fill=color,
            outline="#494949", width=2
        )
        self.canvas.create_text(
            x+width/2, y+height/2, text=label,
            font=("Arial", 8, "bold"), fill="#111111"
        )

    def draw_control_panel(self, w, h):
        # Anchored near the bottom, like the screenshot.
        panel_w = min(w * 0.58, 790)
        panel_h = min(h * 0.29, 220)
        panel_x = (w - panel_w) / 2
        panel_y = h - panel_h + 6

        self.canvas.create_rectangle(
            panel_x, panel_y, panel_x+panel_w, panel_y+panel_h,
            fill=self.PANEL, outline="#777777", width=2
        )
        self.canvas.create_line(
            panel_x, panel_y+30, panel_x+panel_w, panel_y+30,
            fill="#555555", width=2
        )
        self.canvas.create_text(
            panel_x+panel_w*0.50, panel_y+42,
            text="Visual Controls", font=("Arial", 9), fill="#222222"
        )

        # Left column: view buttons and heading dial.
        self.button(panel_x+5, panel_y+36, 82, 19, "Default view")
        self.button(panel_x+93, panel_y+36, 78, 19, "Advanced view")
        self.draw_gauge(panel_x+panel_w*0.13, panel_y+panel_h*0.64,
                        min(panel_h*0.34, panel_w*0.075))

        # Middle controls.
        mx = panel_x + panel_w*0.27
        self.button(mx, panel_y+60, 24, 20, "◀", "#c9c9c9")
        self.button(mx+30, panel_y+60, 68, 20, f"{self.heading:.1f}°", "#eeeeee")
        self.button(mx+104, panel_y+60, 24, 20, "▶", "#c9c9c9")
        self.button(mx+132, panel_y+60, 24, 20, "▼", "#c9c9c9")

        self.button(mx+30, panel_y+104, 70, 22, "10.23", "#f1f1f1")
        self.button(mx+30, panel_y+132, 70, 22, "1.15", "#f1f1f1")
        self.button(mx-2, panel_y+104, 22, 22, "◀", "#c73527")
        self.button(mx+106, panel_y+104, 22, 22, "▶", "#239a42")
        self.button(mx-2, panel_y+132, 22, 22, "◀", "#c73527")
        self.button(mx+106, panel_y+132, 22, 22, "▶", "#239a42")

        # Mode buttons.
        bx = panel_x + panel_w*0.43
        self.button(bx, panel_y+62, 66, 21, "Auto")
        self.button(bx, panel_y+89, 83, 21, "FollowUp")
        self.button(bx, panel_y+116, 83, 21, "Non-FollowUp")
        self.canvas.create_rectangle(
            bx+70, panel_y+62, bx+83, panel_y+83,
            fill="#168c27", outline="#555555"
        )

        # Right-side rudder / control sliders.
        sx = panel_x + panel_w*0.60
        sw = panel_w*0.37
        for row_y in (panel_y+58, panel_y+105):
            self.canvas.create_rectangle(
                sx, row_y, sx+sw, row_y+13,
                fill="#dedede", outline="#777777"
            )
            for i in range(31):
                tx = sx + sw*i/30
                tick_h = 8 if i % 5 == 0 else 4
                self.canvas.create_line(
                    tx, row_y, tx, row_y+tick_h,
                    fill="#666666", width=1
                )
            center = sx + sw/2
            self.canvas.create_line(
                center, row_y-3, center, row_y+17,
                fill="#d02b20", width=2
            )
            self.canvas.create_line(
                center+3, row_y-3, center+3, row_y+17,
                fill="#178c39", width=2
            )

        self.canvas.create_rectangle(
            sx+sw*0.46, panel_y+49, sx+sw*0.50, panel_y+72,
            fill="#a6a6a6", outline="#666666", width=2
        )
        self.button(sx+4, panel_y+145, 58, 24, "PORT", "#c52a20")
        self.button(sx+sw-60, panel_y+145, 58, 24, "STBD", "#269344")
        self.canvas.create_rectangle(
            sx+70, panel_y+151, sx+sw-70, panel_y+164,
            fill="#eeeeee", outline="#888888"
        )
        center = sx+sw/2
        self.canvas.create_line(
            center, panel_y+148, center, panel_y+168,
            fill="#d12b22", width=2
        )
        self.canvas.create_line(
            center+4, panel_y+148, center+4, panel_y+168,
            fill="#168b36", width=2
        )

        # Small status strip along panel bottom.
        self.canvas.create_text(
            panel_x+8, panel_y+panel_h-7,
            text="330°     2.0 kt     22.0°C     10 kts",
            anchor="sw", font=("Arial", 9, "bold"), fill="#183b68"
        )

    def draw(self):
        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 900)
        h = max(self.canvas.winfo_height(), 600)

        self.draw_ocean(w, h)
        self.draw_route(w, h)

        # Tiny navigation/contact markers in the water.
        for x, y, color in [
            (0.165, 0.36, "#85ad50"),
            (0.332, 0.48, "#c34a79"),
            (0.69, 0.46, "#db5279")
        ]:
            self.canvas.create_oval(
                w*x-2, h*y-2, w*x+2, h*y+2, fill=color, outline=""
            )

        # A soft, curved-looking wake trail behind the ship.
        self.draw_ship(w, h)
        self.draw_top_instruments(w)
        self.draw_control_panel(w, h)

        self.canvas.create_text(
            12, h-10, anchor="sw",
            text="SPACE: pause/resume    ESC: exit",
            font=("Arial", 9), fill="#d4e8f9"
        )

        if self.animate:
            # A gentle movement around the ship's initial location.
            elapsed = time.time() - self.started
            self.ship_x = 0.78 + 0.006 * math.sin(elapsed * 0.45)
            self.ship_y = 0.53 + 0.008 * math.cos(elapsed * 0.35)
            self.ship_heading = 150 + 2.0 * math.sin(elapsed * 0.25)

        self.root.after(80, self.draw)


if __name__ == "__main__":
    root = tk.Tk()
    app = ShipNavigationReplica(root)
    root.mainloop()
