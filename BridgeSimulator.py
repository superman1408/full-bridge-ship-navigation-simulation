"""Full Bridge — ship navigation simulator (Tkinter, standard library only).

Run with: python3 full_bridge_simulator.py
Training defaults: four harbour tugs, a channel-relative wind review, and a 3 kn berth-entry speed gate.
Use the applicable port/vessel pilotage plan for real operations.
"""
import math
import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone

BG = "#07111c"
PANEL = "#0d1b29"
PANEL_DARK = "#091521"
LINE = "#203648"
TEXT = "#d9e8f2"
MUTED = "#7690a4"
CYAN = "#50d8e8"
GREEN = "#70e0a5"
AMBER = "#ffcb68"
RED = "#ff707b"


class BridgeSimulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Full Bridge — Ship Navigation Simulation")
        self.geometry("1460x1000")
        self.minsize(1120, 760)
        self.configure(bg=BG)
        self.heading = tk.IntVar(value=45)
        self.throttle = tk.IntVar(value=39)
        self.mode = tk.StringVar(value="AUTO PILOT")
        self.tug_fast = [tk.BooleanVar(value=False) for _ in range(4)]
        self.phase_index = 0
        self.phase_mode = "PREVIEW"
        self.route_progress = 0.0
        self.playing = False
        self.session_active = False
        self.training_playback = False
        self.playback_mode = "PREVIEW"
        self.last_playback_time = 0.0
        self.play_progress = tk.DoubleVar(value=0)
        self.play_rate = tk.StringVar(value="1×")
        self.phase_label = None
        self.distance_label = None
        self.scenario_id = "A"
        self.scenario_flags = {}
        self.scenario_result = None
        self.scenario_combo = None
        self.advance_button = None
        self.wind_metric = None
        self.channel_inputs = {}
        self.channel_outputs = {}
        self.rate_buttons = []
        self.session_button = None
        self.session_status = None
        self.clock_label = None
        self.heading_value = None
        self.speed_value = None
        self.gate_value = None
        self.tug_value = None
        self.chart = None
        self.radar = None
        self.sweep_angle = 0
        self._style()
        self._build()
        self._refresh()
        self._tick()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TScale", background=PANEL, troughcolor="#192f3e")
        style.configure("TCheckbutton", background=PANEL, foreground=TEXT,
                        font=("TkDefaultFont", 10))
        style.map("TCheckbutton", background=[("active", PANEL)])
        style.configure("TRadiobutton", background=PANEL, foreground=TEXT,
                        font=("TkDefaultFont", 9))
        style.map("TRadiobutton", background=[("active", PANEL)])

    def _card(self, parent, title, tag=""):
        frame = tk.Frame(parent, bg=PANEL, highlightbackground=LINE,
                         highlightthickness=1)
        header = tk.Frame(frame, bg=PANEL_DARK, height=37)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title.upper(), bg=PANEL_DARK, fg="#a7bdcc",
                 font=("TkDefaultFont", 9, "bold"), padx=12).pack(side="left")
        if tag:
            tk.Label(header, text=tag, bg=PANEL_DARK, fg=MUTED,
                     font=("TkFixedFont", 9), padx=12).pack(side="right")
        return frame

    def _button(self, parent, text, command, color=TEXT):
        return tk.Button(parent, text=text, command=command, bg="#122637",
                         fg=color, activebackground="#1a3548", activeforeground=CYAN,
                         relief="flat", highlightthickness=1,
                         highlightbackground="#2a485c", padx=11, pady=7,
                         font=("TkFixedFont", 10), cursor="hand2")

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=15, pady=(13, 8))
        tk.Label(top, text="⌁  FULL BRIDGE", bg=BG, fg=TEXT,
                 font=("TkDefaultFont", 16, "bold")).pack(side="left")
        tk.Label(top, text="SHIP NAVIGATION SIMULATION", bg=BG, fg=MUTED,
                 font=("TkDefaultFont", 9)).pack(side="left", padx=14, pady=(6, 0))
        self.clock_label = tk.Label(top, text="SIMULATION LIVE   ·   UTC", bg=BG,
                                    fg=GREEN, font=("TkFixedFont", 10))
        self.clock_label.pack(side="right")
        tk.Frame(self, bg=LINE, height=1).pack(fill="x", padx=15, pady=(0, 10))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        body.columnconfigure(0, weight=0, minsize=245)
        body.columnconfigure(1, weight=1, minsize=430)
        body.columnconfigure(2, weight=0, minsize=305)
        body.rowconfigure(0, weight=1)
        self._left_column(body).grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        center = self._center_column(body)
        center.grid(row=0, column=1, sticky="nsew", padx=5)
        self._right_column(body).grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", padx=15, pady=(0, 10))
        tk.Label(footer, text="SIMULATION ENVIRONMENT · TRAINING USE",
                 bg=BG, fg=MUTED, font=("TkFixedFont", 9)).pack(side="left")
        tk.Label(footer, text="NO ACTIVE ALARMS", bg=BG, fg=GREEN,
                 font=("TkFixedFont", 9)).pack(side="right")

    def _left_column(self, parent):
        col = tk.Frame(parent, bg=BG)
        voyage = self._card(col, "Voyage data", "LNGC · TRAINING VESSEL")
        voyage.pack(fill="x", pady=(0, 10))
        grid = tk.Frame(voyage, bg=PANEL)
        grid.pack(fill="x", padx=10, pady=9)
        self.sog_label = self._metric(grid, "SOG", "12.4", "kn", 0, 0, CYAN)
        self.cog_label = self._metric(grid, "COG", "045", "°", 0, 1)
        self.wind_metric = self._metric(grid, "WIND", "35", "kn", 1, 0, AMBER)
        self._metric(grid, "VISIBILITY", "8.2", "NM", 1, 1)
        position = tk.Frame(voyage, bg="#0d2030", highlightbackground="#183247",
                            highlightthickness=1)
        position.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(position, text="SCENARIO POSITION\nPILOT BOARDING STATION · SCHEMATIC",
                 justify="left", bg="#0d2030", fg=TEXT,
                 font=("TkFixedFont", 10), padx=9, pady=8).pack(anchor="w")
        tk.Label(position, text="● SCHEMATIC", bg="#0d2030", fg=GREEN,
                 font=("TkFixedFont", 9), padx=9, pady=8).pack(anchor="w")

        compass = self._card(col, "Magnetic compass", "DEVIATION −1.2°")
        compass.pack(fill="both", expand=True, pady=(0, 10))
        self.compass = tk.Canvas(compass, width=205, height=225, bg=PANEL,
                                 highlightthickness=0)
        self.compass.pack(fill="both", expand=True, padx=5, pady=5)
        self.compass.bind("<Configure>", lambda _e: self._draw_compass())
        self.heading_value = tk.Label(compass, text="045° TRUE", bg=PANEL,
                                      fg=CYAN, font=("TkFixedFont", 17))
        self.heading_value.pack(pady=(0, 5))
        self.mode_label = tk.Label(compass, text="HEADING MODE · AUTO PILOT",
                                   bg=PANEL, fg=MUTED, font=("TkFixedFont", 9))
        self.mode_label.pack(pady=(0, 10))

        depth = self._card(col, "Echo sounder · simulated", "ILLUSTRATIVE ONLY")
        depth.pack(fill="x")
        tk.Label(depth, text="184.6 m", bg=PANEL, fg=CYAN,
                 font=("TkFixedFont", 23), padx=12, pady=10).pack(anchor="w")
        # tk.Label(depth, text="UNDER KEEL CLEARANCE     179.8 m",
        #          bg=PANEL, fg=GREEN, font=("TkFixedFont", 9), padx=12,
        #          pady=(0, 10)).pack(anchor="w")
        tk.Label(depth, text="UNDER KEEL CLEARANCE     179.8 m",
            bg=PANEL, fg=GREEN, font=("TkFixedFont", 9), padx=12,
            pady=0).pack(anchor="w", pady=(0, 10))
        return col

    def _metric(self, parent, label, value, unit, row, col, color=TEXT):
        box = tk.Frame(parent, bg="#0d2030", highlightbackground="#183247",
                       highlightthickness=1)
        box.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        parent.columnconfigure(col, weight=1)
        tk.Label(box, text=label, bg="#0d2030", fg=MUTED,
                 font=("TkDefaultFont", 8, "bold"), padx=8, pady=7).pack(anchor="w")
        value_label = tk.Label(box, text=f"{value} {unit}", bg="#0d2030", fg=color,
                               font=("TkFixedFont", 15), padx=8, pady=7)
        value_label.pack(anchor="w")
        return value_label

    def _center_column(self, parent):
        col = tk.Frame(parent, bg=BG)
        col.rowconfigure(0, weight=1)
        col.columnconfigure(0, weight=1)
        chart_card = self._card(col, "Electronic chart display", "ENC · SCALE 1:72,000")
        chart_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.chart = tk.Canvas(chart_card, bg="#0a1c27", highlightthickness=0)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda _e: self._draw_chart())

        lower = tk.Frame(col, bg=BG)
        lower.grid(row=1, column=0, sticky="ew")
        lower.columnconfigure(0, weight=1)
        lower.columnconfigure(1, weight=1)
        radar_card = self._card(lower, "X-band radar", "3.0 NM · RELATIVE")
        radar_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.radar = tk.Canvas(radar_card, bg=PANEL, height=170, highlightthickness=0)
        self.radar.pack(fill="both", expand=True)
        self.radar.bind("<Configure>", lambda _e: self._draw_radar())
        engine = self._card(lower, "Engine telegraph", "M/E")
        engine.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.rpm_label = tk.Label(engine, text="SHAFT RPM   612 rpm", bg=PANEL,
                                  fg=TEXT, font=("TkFixedFont", 10))
        self.rpm_label.pack(anchor="w", padx=13, pady=(15, 8))
        self.rpm_canvas = tk.Canvas(engine, height=12, bg="#1a3040", highlightthickness=0)
        self.rpm_canvas.pack(fill="x", padx=13)
        self.thrust_label = tk.Label(engine, text="THRUST   39%\n\nRUDDER   0.0°",
                                     bg=PANEL, fg=MUTED, justify="left",
                                     font=("TkFixedFont", 10))
        self.thrust_label.pack(anchor="w", padx=13, pady=12)
        return col

    def _right_column(self, parent):
        col = tk.Frame(parent, bg=BG)
        control = self._card(col, "Helm control", "STEERING")
        control.pack(fill="x", pady=(0, 10))
        row = tk.Frame(control, bg=PANEL)
        row.pack(fill="x", padx=10, pady=(12, 5))
        self._button(row, "◀ 5°", lambda: self._turn(-5)).pack(side="left")
        self.course_label = tk.Label(row, text="045°", bg=PANEL, fg=CYAN,
                                     font=("TkFixedFont", 21))
        self.course_label.pack(side="left", expand=True)
        self._button(row, "5° ▶", lambda: self._turn(5)).pack(side="right")
        tk.Label(control, text="COURSE SELECT", bg=PANEL, fg=MUTED,
                 font=("TkDefaultFont", 8, "bold"), padx=12).pack(anchor="w", pady=(6, 0))
        ttk.Scale(control, from_=0, to=359, variable=self.heading,
                  command=lambda _v: self._refresh()).pack(fill="x", padx=12, pady=5)
        tk.Label(control, text="ENGINE ORDER", bg=PANEL, fg=MUTED,
                 font=("TkDefaultFont", 8, "bold"), padx=12).pack(anchor="w", pady=(5, 0))
        speed_row = tk.Frame(control, bg=PANEL)
        speed_row.pack(fill="x", padx=10, pady=5)
        self._button(speed_row, "−", lambda: self._set_throttle(self.throttle.get()-5)).pack(side="left")
        ttk.Scale(speed_row, from_=0, to=100, variable=self.throttle,
                  command=lambda _v: self._refresh()).pack(side="left", fill="x", expand=True, padx=7)
        self._button(speed_row, "+", lambda: self._set_throttle(self.throttle.get()+5)).pack(side="left")
        for mode in ("AUTO PILOT", "HEADING", "TRACK"):
            ttk.Radiobutton(control, text=mode, value=mode, variable=self.mode,
                            command=self._refresh).pack(side="left", padx=9, pady=(4, 12))

        tug = self._card(col, "LNGC berth tug simulation", "DAHEJ · USER SCENARIO")
        tug.pack(fill="both", expand=True, pady=(0, 10))
        tk.Label(tug, text="INJECT A STUDY SCENARIO", bg=PANEL, fg=MUTED,
                 font=("TkDefaultFont", 8, "bold"), padx=10).pack(anchor="w", pady=(8, 2))
        self.scenario_combo = ttk.Combobox(
            tug, state="readonly", width=34,
            values=("A · 35 kn wind · limits unknown", "B · wind data invalid",
                    "C · one tug unavailable", "D · speed above training gate",
                    "E · authority missing", "F · control input failure",
                    "G · exercise interlocks satisfied"))
        self.scenario_combo.current(0)
        self.scenario_combo.pack(fill="x", padx=10, pady=(0, 5))
        self.scenario_combo.bind("<<ComboboxSelected>>", self._scenario_changed)
        self.scenario_result = tk.Label(tug, text="", bg="#321e20", fg="#ffb3b7",
                                        justify="left", wraplength=275,
                                        font=("TkFixedFont", 9), padx=9, pady=8)
        self.scenario_result.pack(fill="x", padx=9, pady=4)
        self.wind_state = tk.Label(tug, text="FROM SSW · LIMIT UNKNOWN", bg=PANEL,
                                   fg=AMBER, font=("TkFixedFont", 8))
        self.wind_state.pack(anchor="w", padx=10, pady=3)
        self._build_channel_review(tug)
        tk.Label(tug, text="PILOT BOARDING STATION → PETRONET LNG BERTH\nSchematic training phases · no charted track",
                 bg=PANEL, fg=MUTED, justify="left", font=("TkFixedFont", 9),
                 padx=10, pady=5).pack(anchor="w")
        phase_box = tk.Frame(tug, bg="#102333", highlightbackground="#214153", highlightthickness=1)
        phase_box.pack(fill="x", padx=10, pady=6)
        self.phase_label = tk.Label(phase_box, text="Pilot Boarding Station", bg="#102333",
                                    fg=CYAN, font=("TkFixedFont", 10))
        self.phase_label.pack(side="left", padx=8, pady=8)
        self.distance_label = tk.Label(phase_box, text="2.5 NM*", bg="#102333",
                                       fg=TEXT, font=("TkFixedFont", 9))
        self.distance_label.pack(side="right", padx=8)
        session_row = tk.Frame(tug, bg=PANEL)
        session_row.pack(fill="x", padx=10, pady=(2, 4))
        self.session_button = tk.Button(session_row, text="START SIMULATION",
                                        command=self._toggle_session, bg="#164334",
                                        fg=GREEN, activebackground="#20553e",
                                        relief="flat", font=("TkFixedFont", 9, "bold"),
                                        padx=8, pady=7, cursor="hand2")
        self.session_button.pack(side="left", fill="x", expand=True)
        self.session_status = tk.Label(session_row, text="SESSION STOPPED", bg=PANEL,
                                       fg=AMBER, font=("TkFixedFont", 8))
        self.session_status.pack(side="right", padx=(6, 0))
        playrow = tk.Frame(tug, bg=PANEL)
        playrow.pack(fill="x", padx=10, pady=(3, 2))
        self.play_button = self._button(playrow, "▶ PLAY SCHEMATIC", self._toggle_playback, CYAN)
        self.play_button.pack(side="left", fill="x", expand=True)
        self._button(playrow, "RESET", self._reset_playback, TEXT).pack(side="left", padx=(5, 0))
        rate_row = tk.Frame(playrow, bg=PANEL)
        rate_row.pack(side="right", padx=(5, 0))
        for rate in ("1×", "2×", "3×", "6×"):
            button = tk.Button(rate_row, text=rate, command=lambda r=rate: self._set_play_rate(r),
                                bg="#1b4952" if rate == self.play_rate.get() else "#122637",
                                fg=CYAN if rate == self.play_rate.get() else TEXT,
                                activebackground="#1b4952", relief="flat",
                                highlightthickness=1, highlightbackground="#2a485c",
                                padx=5, pady=5, font=("TkFixedFont", 8), cursor="hand2")
            button.pack(side="left", padx=1)
            self.rate_buttons.append((rate, button))
        self.progress_label = tk.Label(tug, text="PATH POSITION · SCHEMATIC   0%",
                                       bg=PANEL, fg=CYAN, font=("TkFixedFont", 8))
        self.progress_label.pack(anchor="w", padx=10, pady=(2, 0))
        ttk.Scale(tug, from_=0, to=1000, variable=self.play_progress,
                  command=self._scrub_path).pack(fill="x", padx=10, pady=(0, 5))
        tk.Label(tug, text="Visual-only playback runs during HOLD. Towlines show connection state; no tug force is modeled.",
                 bg=PANEL, fg=MUTED, justify="left", wraplength=275,
                 font=("TkDefaultFont", 8)).pack(fill="x", padx=10, pady=(0, 4))
        self.advance_button = self._button(tug, "PHASE ADVANCE HELD", self._advance_phase,
                                           GREEN)
        self.advance_button.pack(fill="x", padx=10, pady=5)
        stations = ("Tug A · forward station · 65 t BP", "Tug B · forward station · 65 t BP",
                    "Tug C · aft station · 65 t BP", "Tug D · aft station · 65 t BP")
        for var, text in zip(self.tug_fast, stations):
            ttk.Checkbutton(tug, text=text, variable=var,
                            command=self._refresh).pack(anchor="w", padx=10, pady=3)
        gate = tk.Frame(tug, bg=PANEL)
        gate.pack(fill="x", padx=10, pady=7)
        tk.Label(gate, text="SIM SPEED GATE", bg=PANEL, fg=MUTED,
                 font=("TkDefaultFont", 8, "bold")).pack(side="left")
        self.gate_value = tk.Label(gate, text="REDUCE TO ≤ 3.0 KN", bg=PANEL,
                                   fg=AMBER, font=("TkFixedFont", 9))
        self.gate_value.pack(side="right")
        self.tug_value = tk.Label(tug, text="0 / 4 TUGS CONNECTED", bg=PANEL,
                                  fg=AMBER, font=("TkFixedFont", 10, "bold"))
        self.tug_value.pack(anchor="w", padx=10, pady=3)
        self.entry_button = tk.Button(tug, text="CHECK SIM INTERLOCKS",
                                      command=self._confirm_entry, bg="#321e20",
                                      fg="#ffb3b7", activebackground="#4a292b",
                                      relief="flat", font=("TkDefaultFont", 9, "bold"),
                                      padx=8, pady=9, cursor="hand2")
        self.entry_button.pack(fill="x", padx=10, pady=7)
        tk.Label(tug, text="*Illustrative distances and tug stations only. The 500 m diameter circle is an unscaled display overlay, not the vessel’s measured turning circle. The jetty and parallel alongside route are schematic, with no real berth geometry. This does not model tide/current, hydrodynamics, or port limits; controls do not grant berth clearance.",
                 bg=PANEL, fg=MUTED, justify="left", wraplength=275,
                 font=("TkDefaultFont", 8)).pack(fill="x", padx=10, pady=(0, 10))
        self._load_scenario("A")
        return col

    def _build_channel_review(self, parent):
        """Show wind decomposition and a transparent, user-input tug comparison."""
        box = tk.Frame(parent, bg="#0b1d2b", highlightbackground="#294356",
                       highlightthickness=1)
        box.pack(fill="x", padx=9, pady=6)
        tk.Label(box, text="CHANNEL / TUG POWER REVIEW · INPUT-BASED",
                 bg="#0b1d2b", fg=CYAN, font=("TkFixedFont", 8, "bold"),
                 padx=7, pady=5).pack(anchor="w")
        tk.Label(box, text="Wind from SSW (202.5°T), 35 kn. Enter channel axis (true bearing).",
                 bg="#0b1d2b", fg=MUTED, justify="left", wraplength=280,
                 font=("TkDefaultFont", 8), padx=7).pack(anchor="w", pady=(0, 4))
        grid = tk.Frame(box, bg="#0b1d2b")
        grid.pack(fill="x", padx=6)
        fields = (("Channel axis · °T", "axis"), ("Channel width · m", "width"),
                  ("Vessel beam · m", "beam"), ("Windage area · m²", "area"),
                  ("Drag coefficient · Cd", "cd"), ("Required effective BP · tf", "required"),
                  ("Available effective BP · tf", "available"))
        for index, (label, key) in enumerate(fields):
            row, col = divmod(index, 2)
            cell = tk.Frame(grid, bg="#0b1d2b")
            cell.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
            tk.Label(cell, text=label, bg="#0b1d2b", fg=MUTED,
                     font=("TkDefaultFont", 7)).pack(anchor="w")
            var = tk.StringVar(value="")
            self.channel_inputs[key] = var
            entry = tk.Entry(cell, textvariable=var, bg=PANEL_DARK, fg=TEXT,
                             insertbackground=TEXT, relief="flat",
                             highlightthickness=1, highlightbackground=LINE,
                             font=("TkFixedFont", 8))
            entry.pack(fill="x", pady=(2, 0))
            var.trace_add("write", lambda *_args: self._channel_review())
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        out = tk.Frame(box, bg="#0b1d2b")
        out.pack(fill="x", padx=7, pady=(5, 3))
        for key, title in (("cross", "Cross-channel wind"), ("along", "Along-channel wind"),
                           ("load", "Lateral wind-load estimate"),
                           ("occupancy", "Beam / channel-width ratio"),
                           ("bp", "Effective BP comparison")):
            row = tk.Frame(out, bg="#0b1d2b")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=title + ":", bg="#0b1d2b", fg=MUTED,
                     font=("TkDefaultFont", 7), anchor="w").pack(side="left")
            value = tk.Label(row, text="UNRESOLVED", bg="#0b1d2b", fg=AMBER,
                             font=("TkFixedFont", 7), anchor="e", wraplength=160)
            value.pack(side="right")
            self.channel_outputs[key] = value
        tk.Label(box, text="4 × 65 tf = 260 tf nominal only; not effective combined pull. Load estimate is simplified and does not establish tug demand or clearance.",
                 bg="#0b1d2b", fg=MUTED, justify="left", wraplength=280,
                 font=("TkDefaultFont", 7), padx=7, pady=4).pack(anchor="w")
        self._channel_review()

    def _channel_review(self):
        if not self.channel_outputs:
            return
        def value(key):
            raw = self.channel_inputs[key].get().strip()
            try:
                number = float(raw)
                return number if math.isfinite(number) else None
            except ValueError:
                return None
        axis, width, beam = value("axis"), value("width"), value("beam")
        area, cd = value("area"), value("cd")
        required, available = value("required"), value("available")
        wind_valid = (self.scenario_id == "A" and
                      self.scenario_flags.get("wind_valid", False))
        if not wind_valid:
            self.channel_outputs["cross"].config(text="35 KN SSW INPUT NOT ACTIVE", fg=AMBER)
            self.channel_outputs["along"].config(text="UNAVAILABLE", fg=AMBER)
            self.channel_outputs["load"].config(text="NOT CALCULATED", fg=AMBER)
        elif axis is None or not 0 <= axis < 360:
            self.channel_outputs["cross"].config(text="NEED CHANNEL AXIS", fg=AMBER)
            self.channel_outputs["along"].config(text="UNRESOLVED", fg=AMBER)
            self.channel_outputs["load"].config(text="NEED AREA + Cd", fg=AMBER)
        else:
            delta = math.radians(202.5 - axis)
            cross = 35 * abs(math.sin(delta))
            along = 35 * abs(math.cos(delta))
            self.channel_outputs["cross"].config(text=f"{cross:.1f} kn", fg=CYAN)
            self.channel_outputs["along"].config(text=f"{along:.1f} kn", fg=CYAN)
            if area and area > 0 and cd and cd > 0:
                force_kn = (0.5 * 1.225 * (cross * 0.514444) ** 2 * cd * area) / 1000
                force_tf = force_kn / 9.80665
                self.channel_outputs["load"].config(
                    text=f"{force_kn:.1f} kN / {force_tf:.1f} tf", fg=CYAN)
            else:
                self.channel_outputs["load"].config(text="NEED AREA + Cd", fg=AMBER)
        if width and width > 0 and beam and beam > 0:
            self.channel_outputs["occupancy"].config(
                text=f"{100 * beam / width:.1f}% · geometry only", fg=CYAN)
        else:
            self.channel_outputs["occupancy"].config(text="NEED BEAM + WIDTH", fg=AMBER)
        if required is not None and available is not None and required >= 0 and available >= 0:
            result = "MEETS" if available >= required else "BELOW"
            self.channel_outputs["bp"].config(
                text=f"{available:.0f}/{required:.0f} tf {result} entered value · NOT CLEARANCE",
                fg=AMBER if available < required else CYAN)
        else:
            self.channel_outputs["bp"].config(
                text="NOT ASSESSED · APPROVED INPUTS REQUIRED", fg=AMBER)

    def _scenario_changed(self, _event=None):
        self._load_scenario(self.scenario_combo.get()[:1])

    def _load_scenario(self, scenario_id):
        self.scenario_id = scenario_id
        self.playing = False
        self.training_playback = False
        self.session_active = False
        self.session_button.config(text="START SIMULATION")
        self.session_status.config(text="SESSION STOPPED")
        cases = {
            "A": ("35", "kn", "FROM SSW · LIMIT UNKNOWN", [False]*4, 12.4, True, False, False, True),
            "B": ("INVALID", "sensor", "WIND INPUT LOST", [True]*4, 2.5, False, True, True, True),
            "C": ("EXERCISE", "envelope", "SYNTHETIC CONDITIONS", [True, True, True, False], 2.5, True, True, True, True),
            "D": ("EXERCISE", "envelope", "SYNTHETIC CONDITIONS", [True]*4, 4.2, True, True, True, True),
            "E": ("EXERCISE", "envelope", "AUTHORITY NOT CONFIRMED", [True]*4, 2.5, True, True, False, True),
            "F": ("EXERCISE", "envelope", "CONTROL INPUT FAILURE", [True]*4, 2.5, True, True, True, False),
            "G": ("EXERCISE", "envelope", "SYNTHETIC AUTHORIZED EXERCISE", [True]*4, 2.5, True, True, True, True),
        }
        wind, unit, direction, tugs, speed, wind_valid, wind_verified, authorized, control_valid = cases[scenario_id]
        self.wind_metric.config(text=f"{wind} {unit}")
        self.wind_state.config(text=direction)
        self.scenario_flags = {"wind_valid": wind_valid, "wind_verified": wind_verified,
                               "authorized": authorized, "control_valid": control_valid}
        self._channel_review()
        for var, connected in zip(self.tug_fast, tugs):
            var.set(connected)
        self.throttle.set(round(speed / 0.318))
        self.phase_index = 0
        self.phase_mode = "PREVIEW"
        self.route_progress = 0.0
        self.playing = False
        self.play_button.config(text="▶ PLAY SCHEMATIC")
        self.play_progress.set(0)
        self.phase_label.config(text="PREVIEW · Pilot Boarding Station")
        self.distance_label.config(text="2.5 NM*")
        self._refresh()

    def _advance_phase(self):
        if not self.session_active or self.scenario_id != "G" or not self._scenario_ready():
            return
        self.playing = False
        self.training_playback = False
        self.play_button.config(text="▶ PLAY SCHEMATIC", state=tk.NORMAL)
        self.phase_mode = "TRAINING"
        self._set_route_progress(min(1.0, (self.phase_index + 1) / 4), "TRAINING")

    def _toggle_session(self):
        if self.session_active:
            self.playing = False
            self.training_playback = False
            self.session_active = False
            self.play_button.config(text="▶ PLAY SCHEMATIC", state=tk.NORMAL)
            self.phase_mode = "ABORTED · HOLD"
            self._set_route_progress(self.route_progress, self.phase_mode)
            self.session_button.config(text="START SIMULATION")
            self._update_tug_gate(int(float(self.throttle.get())) * 0.318)
            self.session_status.config(text="SESSION ABORTED · HOLD")
            return
        self.session_active = True
        ready = self.scenario_id == "G" and self._scenario_ready()
        self.session_button.config(text="ABORT SIMULATION")
        if ready:
            self.session_status.config(text="TRAINING PLAYBACK ACTIVE")
            self.training_playback = True
            self._begin_playback("TRAINING")
        else:
            self.session_status.config(text="SESSION ACTIVE · SAFE HOLD")
        self._update_tug_gate(int(float(self.throttle.get())) * 0.318)

    def _begin_playback(self, mode):
        if self.route_progress >= 1:
            self._set_route_progress(0, mode)
        self.playback_mode = mode
        self.playing = True
        self.last_playback_time = time.monotonic()
        self.play_button.config(text="Ⅱ TRAINING RUN" if mode == "TRAINING" else "Ⅱ PAUSE PREVIEW",
                                state=tk.DISABLED if mode == "TRAINING" else tk.NORMAL)
        self._playback_tick()

    def _set_route_progress(self, progress, mode="PREVIEW"):
        self.route_progress = max(0.0, min(1.0, float(progress)))
        self.phase_mode = mode
        self.phase_index = min(3, int(self.route_progress * 4))
        names = ("Pilot Boarding Station", "Pilotage Transit · Schematic",
                 "Berth Approach · Tug Assist", "Alongside · Training End State")
        distances = ("2.5 NM*", "1.2 NM*", "0.4 NM*", "0.0 NM*")
        self.phase_label.config(text=f"{mode} · {names[self.phase_index]}")
        self.distance_label.config(text=distances[self.phase_index])
        self.progress_label.config(text=f"PATH POSITION · SCHEMATIC   {self.route_progress*100:.0f}%")
        self.play_progress.set(self.route_progress * 1000)
        self._draw_chart()

    def _scrub_path(self, value):
        if not hasattr(self, "play_button"):
            return
        if self.training_playback:
            return
        self.playing = False
        self.play_button.config(text="▶ PLAY SCHEMATIC")
        self._set_route_progress(float(value) / 1000, "PREVIEW")

    def _toggle_playback(self):
        if self.training_playback:
            return
        if self.playing:
            self.playing = False
            self.play_button.config(text="▶ PLAY SCHEMATIC")
            return
        self._begin_playback("PREVIEW")

    def _set_play_rate(self, rate):
        self.play_rate.set(rate)
        for button_rate, button in self.rate_buttons:
            active = button_rate == rate
            button.config(bg="#1b4952" if active else "#122637",
                          fg=CYAN if active else TEXT)

    def _playback_tick(self):
        if not self.playing:
            return
        now = time.monotonic()
        elapsed = now - self.last_playback_time
        self.last_playback_time = now
        multiplier = {"1×": 1, "2×": 2, "3×": 3, "6×": 6}.get(self.play_rate.get(), 1)
        progress = self.route_progress + elapsed * multiplier / 30
        if progress >= 1:
            progress = 1
            self.playing = False
            if self.training_playback:
                self.training_playback = False
                self.session_status.config(text="TRAINING RUN COMPLETE · SIM ONLY")
                self.play_button.config(text="▶ PLAY SCHEMATIC", state=tk.NORMAL)
            else:
                self.play_button.config(text="▶ PLAY SCHEMATIC")
        self._set_route_progress(progress, self.playback_mode)
        self._update_tug_gate(int(float(self.throttle.get())) * 0.318)
        if self.playing:
            self.after(33, self._playback_tick)

    def _reset_playback(self):
        if self.training_playback:
            return
        self.playing = False
        self.play_button.config(text="▶ PLAY SCHEMATIC")
        self._set_route_progress(0, "PREVIEW")

    def _scenario_ready(self):
        return (all(var.get() for var in self.tug_fast)
                and int(float(self.throttle.get())) * 0.318 <= 3
                and all(self.scenario_flags.values()))

    def _turn(self, delta):
        self.heading.set((self.heading.get() + delta) % 360)
        self._refresh()

    def _set_throttle(self, value):
        self.throttle.set(max(0, min(100, int(value))))
        self._refresh()

    def _refresh(self):
        h = int(float(self.heading.get())) % 360
        throttle = int(float(self.throttle.get()))
        speed = throttle * 0.318
        if self.course_label:
            self.course_label.config(text=f"{h:03d}°")
            self.heading_value.config(text=f"{h:03d}° TRUE")
            self.mode_label.config(text=f"HEADING MODE · {self.mode.get()}")
            self.sog_label.config(text=f"{speed:.1f} kn")
            self.cog_label.config(text=f"{h:03d} °")
            self.rpm_label.config(text=f"SHAFT RPM   {180 + int(throttle*11.1)} rpm")
            self.thrust_label.config(text=f"THRUST   {throttle}%\n\nRUDDER   0.0°")
            self.rpm_canvas.delete("all")
            w = max(1, self.rpm_canvas.winfo_width())
            self.rpm_canvas.create_rectangle(0, 0, w*throttle/100, 12,
                                             fill=GREEN, outline="")
        self._update_tug_gate(speed)
        self._draw_compass()
        self._draw_chart()

    def _update_tug_gate(self, speed):
        if not self.tug_value:
            return
        connected = sum(var.get() for var in self.tug_fast)
        tugs_ready = connected == 4
        speed_ready = speed <= 3.0
        self.tug_value.config(text=f"{connected} / 4 TUGS CONNECTED",
                              fg=GREEN if tugs_ready else AMBER)
        self.gate_value.config(text="WITHIN SIM GATE" if speed_ready else "REDUCE TO ≤ 3.0 KN",
                               fg=GREEN if speed_ready else AMBER)
        reasons = []
        if not self.scenario_flags.get("wind_valid", False):
            reasons.append("wind data invalid")
        if not self.scenario_flags.get("wind_verified", False):
            reasons.append("wind direction/limit unverified")
        if connected < 4:
            reasons.append(f"{connected}/4 tugs connected")
        if not speed_ready:
            reasons.append("speed above 3 kn exercise gate")
        if not self.scenario_flags.get("authorized", False):
            reasons.append("exercise authority missing")
        if not self.scenario_flags.get("control_valid", False):
            reasons.append("critical control input failed")
        gate_ready = self.scenario_id == "G" and not reasons
        if self.training_playback and not gate_ready:
            self.playing = False
            self.training_playback = False
            self.session_active = False
            self.play_button.config(text="▶ PLAY SCHEMATIC", state=tk.NORMAL)
            self.session_button.config(text="START SIMULATION")
            self.session_status.config(text="AUTO-ABORT · INTERLOCK LOST")
        allowed = self.session_active and gate_ready
        if allowed:
            result = "PASS · TRAINING PLAYBACK ACTIVE. SCHEMATIC ONLY; NO REAL CLEARANCE."
            result_bg, result_fg = "#102c25", GREEN
        elif gate_ready:
            result = "READY · START SIMULATION TO BEGIN TRAINING PLAYBACK."
            result_bg, result_fg = "#102333", CYAN
        elif not self.scenario_flags.get("control_valid", True):
            result = "SAFE-FAIL · ABORT / HOLD. " + " · ".join(reasons)
            result_bg, result_fg = "#321e20", "#ffb3b7"
        elif not reasons:
            result = "CASE INPUTS RESOLVED · SELECT G FOR POSITIVE CONTROL; PLAYBACK LOCKED."
            result_bg, result_fg = "#102333", CYAN
        else:
            result = "FAIL-SAFE PASS · HOLD. " + " · ".join(reasons)
            result_bg, result_fg = "#321e20", "#ffb3b7"
        self.scenario_result.config(text=result, bg=result_bg, fg=result_fg)
        self.advance_button.config(state=(tk.NORMAL if allowed else tk.DISABLED),
                                   text=("ADVANCE TRAINING PHASE" if allowed else "PHASE ADVANCE HELD"))
        self.entry_button.config(text="CHECK SIM INTERLOCKS")
        if self.session_active and not allowed:
            self.session_status.config(text="SESSION ACTIVE · SAFE HOLD")
        elif self.session_active and allowed and self.training_playback:
            self.session_status.config(text="TRAINING PLAYBACK ACTIVE")
        elif not self.session_active and self.session_status.cget("text") not in (
                "SESSION ABORTED · HOLD", "AUTO-ABORT · INTERLOCK LOST"):
            self.session_status.config(text="SESSION STOPPED")

    def _confirm_entry(self):
        self._update_tug_gate(int(float(self.throttle.get())) * 0.318)

    def _draw_compass(self):
        if not self.compass:
            return
        c = self.compass
        c.delete("all")
        w, h = max(c.winfo_width(), 190), max(c.winfo_height(), 190)
        cx, cy, r = w/2, h/2, min(w, h)*.42
        c.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#0a1722", outline="#365366", width=2)
        for deg in range(0, 360, 15):
            a = math.radians(deg-90)
            inner = r*.84 if deg % 45 == 0 else r*.9
            c.create_line(cx+math.cos(a)*inner, cy+math.sin(a)*inner,
                          cx+math.cos(a)*r*.97, cy+math.sin(a)*r*.97,
                          fill="#7290a1", width=2 if deg % 45 == 0 else 1)
        c.create_text(cx, cy-r*.68, text="N", fill="#91adbe", font=("TkFixedFont", 10, "bold"))
        a = math.radians(int(self.heading.get())-90)
        x, y = cx+math.cos(a)*r*.66, cy+math.sin(a)*r*.66
        c.create_line(cx, cy, x, y, fill=RED, width=3, arrow="last")
        c.create_oval(cx-5, cy-5, cx+5, cy+5, fill=TEXT, outline="#31566a")

    def _draw_chart(self):
        if not self.chart:
            return
        c = self.chart
        c.delete("all")
        w, h = max(c.winfo_width(), 300), max(c.winfo_height(), 300)
        for x in range(0, w, 48):
            c.create_line(x, 0, x, h, fill="#173142")
        for y in range(0, h, 48):
            c.create_line(0, y, w, y, fill="#173142")
        # Simplified land/contour shapes for a training display.
        c.create_oval(-w*.15, h*.67, w*.36, h*1.2, fill="#153331", outline="#37645c")
        c.create_oval(-w*.17, h*.63, w*.39, h*1.24, outline="#37645c")
        c.create_oval(w*.76, -h*.17, w*1.1, h*.25, fill="#193b3c", outline="#37645c")
        route = ((.12, .82), (.35, .66), (.56, .52), (.70, .43),
                 (.76, .38), (.82, .29), (.88, .20))
        scaled = min(self.route_progress, .999999) * (len(route)-1)
        segment = min(len(route)-2, int(scaled))
        fraction = scaled - segment
        if self.route_progress >= 1:
            segment, fraction = len(route)-2, 1.0
        a, b = route[segment], route[segment+1]
        px, py = a[0] + (b[0]-a[0])*fraction, a[1] + (b[1]-a[1])*fraction
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy) or 1
        ux, uy = dx/length, dy/length
        track = [(w*x, h*y) for x, y in route]
        # The overlay is schematic: it has no geographic/chart scale.
        basin_x, basin_y, basin_r = w*.70, h*.42, min(w, h)*.125
        c.create_oval(basin_x-basin_r, basin_y-basin_r,
                      basin_x+basin_r, basin_y+basin_r,
                      outline=AMBER, dash=(5, 4), width=2)
        c.create_text(basin_x, basin_y-basin_r-7,
                      text="TURNING BASIN Ø500 m*", fill=AMBER,
                      font=("TkFixedFont", 8, "bold"))
        # Jetty face and fenders run parallel to the final alongside leg.
        j0, j1 = (w*.80, h*.35), (w*.98, h*.08)
        c.create_line(*j0, *j1, fill="#c5d5df", width=8, capstyle=tk.ROUND)
        c.create_line(*j0, *j1, fill="#7893a4", width=2)
        jdx, jdy = j1[0]-j0[0], j1[1]-j0[1]
        jlen = math.hypot(jdx, jdy) or 1
        fnx, fny = -jdy/jlen, jdx/jlen
        for step in range(1, 7):
            t = step/7
            fx, fy = j0[0]+jdx*t, j0[1]+jdy*t
            c.create_line(fx-fnx*6, fy-fny*6, fx+fnx*6, fy+fny*6,
                          fill=AMBER, width=2)
        c.create_text(w*.84, h*.055, text="JETTY FACE / FENDERS",
                      fill=AMBER, anchor="w", font=("TkFixedFont", 8))
        c.create_text(w*.67, h*.58, text="*500 m DIAMETER · OVERLAY ONLY",
                      fill=AMBER, anchor="w", font=("TkFixedFont", 7))
        c.create_line(*[v for point in track for v in point], fill=CYAN,
                      dash=(6, 6), width=2, smooth=True)
        if self.route_progress > 0:
            trace = track[:segment+1] + [(w*px, h*py)]
            if self.route_progress >= 1:
                trace.append(track[-1])
            c.create_line(*[v for point in trace for v in point],
                          fill=GREEN, width=3, capstyle=tk.ROUND,
                          joinstyle=tk.ROUND, smooth=True)
        for i, (tx, ty) in enumerate(track[:-1]):
            color = GREEN if i < self.phase_index else AMBER if i == self.phase_index else MUTED
            c.create_oval(tx-5, ty-5, tx+5, ty+5, fill=color, outline=color)
        c.create_text(track[0][0]+8, track[0][1]+12, text="PILOT BOARDING",
                      fill=TEXT, anchor="w", font=("TkFixedFont", 8))
        c.create_text(w*.84, h*.27, text="PARALLEL ALONGSIDE · SCHEMATIC",
                      fill=AMBER, anchor="w", font=("TkFixedFont", 8))
        c.create_text(w*.27, h*.28, text="✣  TRAINING CONTACT", fill=RED,
                      font=("TkFixedFont", 9))
        cx, cy = w*px, h*py
        # Top-down LNG carrier: tapered hull, four membrane tank blocks, aft house.
        screen_dx, screen_dy = ux*w, uy*h
        screen_len = math.hypot(screen_dx, screen_dy) or 1
        hx, hy = screen_dx/screen_len, screen_dy/screen_len
        nx, ny = -hy, hx
        angle = math.atan2(hx, -hy)
        vessel_scale = min(w, h)
        def local_polygon(coords, fill, outline, width=1):
            rotated = []
            for lx, ly in coords:
                rx = lx*math.cos(angle)-ly*math.sin(angle)
                ry = lx*math.sin(angle)+ly*math.cos(angle)
                rotated.extend((cx+rx, cy+ry))
            c.create_polygon(*rotated, fill=fill, outline=outline, width=width)
        k = vessel_scale/180
        hull = [(-4*k, 20*k), (-3.8*k, -9*k), (-2.5*k, -19*k),
                (0, -25*k), (2.5*k, -19*k), (3.8*k, -9*k), (4*k, 20*k),
                (2.5*k, 24*k), (-2.5*k, 24*k)]
        local_polygon(hull, "#c9e1eb", CYAN, 2)
        local_polygon([(-3*k, 17*k), (-2.8*k, -8*k), (0, -21*k),
                       (2.8*k, -8*k), (3*k, 17*k), (0, 21*k)],
                      "#18374a", "#7299aa", 1)
        for y, half in ((-10, 2.3), (-3, 2.5), (4, 2.5), (11, 2.3)):
            local_polygon([(-half*k, (y-2.4)*k), (half*k, (y-2.4)*k),
                           (half*k, (y+2.4)*k), (-half*k, (y+2.4)*k)],
                          "#bddbe5", "#5aaaba", 1)
        local_polygon([(-4.5*k, 14*k), (4.5*k, 14*k), (3.8*k, 20*k),
                       (0, 22*k), (-3.8*k, 20*k)], "#e0a866", "#ffd48e", 1)
        local_polygon([(-2*k, 15*k), (2*k, 15*k), (2*k, 18*k), (-2*k, 18*k)],
                      "#d8eef4", "#789aaa", 1)
        longitudinal, lateral = vessel_scale*.09, vessel_scale*.065
        tug_layout = ((1, -1), (1, 1), (-1, -1), (-1, 1))
        for index, (fore_aft, side) in enumerate(tug_layout):
            tx = cx + hx*longitudinal*fore_aft + nx*lateral*side
            ty = cy + hy*longitudinal*fore_aft + ny*lateral*side
            ax = cx + hx*longitudinal*.62*fore_aft + nx*lateral*.42*side
            ay = cy + hy*longitudinal*.62*fore_aft + ny*lateral*.42*side
            tug_color = GREEN if self.tug_fast[index].get() else "#52697a"
            line_options = {"fill": tug_color, "width": 2}
            if not self.tug_fast[index].get():
                line_options["dash"] = (3, 3)
            c.create_line(ax, ay, tx, ty, **line_options)
            tug_angle = angle
            tug_len, tug_beam = vessel_scale*.043, vessel_scale*.014
            def tug_poly(coords, fill, outline, width=1):
                vertices = []
                for lx, ly in coords:
                    rx = lx*math.cos(tug_angle)-ly*math.sin(tug_angle)
                    ry = lx*math.sin(tug_angle)+ly*math.cos(tug_angle)
                    vertices.extend((tx+rx, ty+ry))
                c.create_polygon(*vertices, fill=fill, outline=outline, width=width)
            tug_poly([(-tug_beam, tug_len*.48), (-tug_beam, -tug_len*.25),
                      (-tug_beam*.55, -tug_len*.48), (0, -tug_len*.58),
                      (tug_beam*.55, -tug_len*.48), (tug_beam, -tug_len*.25),
                      (tug_beam, tug_len*.48), (0, tug_len*.58)],
                     "#122b3d", tug_color, 2)
            tug_poly([(-tug_beam*.55, -tug_len*.08), (tug_beam*.55, -tug_len*.08),
                      (tug_beam*.55, tug_len*.20), (-tug_beam*.55, tug_len*.20)],
                     "#d3e5ed", tug_color, 1)
        c.create_oval(cx-68, cy-68, cx+68, cy+68, outline="#1f5560")
        c.create_text(12, 12, anchor="nw", text="DAHEJ · SCHEMATIC · NOT FOR NAVIGATION",
                      fill="#a6bdc9", font=("TkFixedFont", 9))
        c.create_line(12, 29, 34, 29, fill=GREEN, width=3)
        c.create_text(40, 29, anchor="w", text="VESSEL TRACK · SIMULATED",
                      fill=GREEN, font=("TkFixedFont", 8))
        c.create_text(12, h-12, anchor="sw", text=f"{self.phase_mode} · PATH {self.route_progress*100:.0f}% · SCHEMATIC ONLY",
                      fill=MUTED, font=("TkFixedFont", 9))

    def _draw_radar(self):
        if not self.radar:
            return
        c = self.radar
        c.delete("all")
        w, h = max(c.winfo_width(), 150), max(c.winfo_height(), 150)
        r = min(w, h)*.4
        cx, cy = w/2, h/2
        for scale in (.33, .66, 1):
            rr = r*scale
            c.create_oval(cx-rr, cy-rr, cx+rr, cy+rr, outline="#236057")
        c.create_line(cx-r, cy, cx+r, cy, fill="#277068")
        c.create_line(cx, cy-r, cx, cy+r, fill="#277068")
        a = math.radians(self.sweep_angle)
        c.create_line(cx, cy, cx+math.cos(a)*r, cy+math.sin(a)*r,
                      fill=GREEN, width=2)
        for bx, by, color in ((.42, -.35, GREEN), (-.35, .21, GREEN), (.15, .63, AMBER)):
            x, y = cx+bx*r, cy+by*r
            c.create_oval(x-3, y-3, x+3, y+3, fill=color, outline="")

    def _tick(self):
        self.clock_label.config(text="● SIMULATION LIVE   ·   UTC " +
                                datetime.now(timezone.utc).strftime("%H:%M:%S"))
        self.sweep_angle = (self.sweep_angle + 4) % 360
        self._draw_radar()
        self.after(100, self._tick)


if __name__ == "__main__":
    BridgeSimulator().mainloop()
