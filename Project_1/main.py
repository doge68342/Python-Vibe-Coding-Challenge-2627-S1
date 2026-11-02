"""Lumen Run: collect the night lights and stay ahead of the storm."""

import math
import json
import random
import time
from pathlib import Path
import tkinter as tk


WIDTH = 960
HEIGHT = 640
GOAL = 20
ROUND_SECONDS = 55
DIFFICULTIES = (
	{"name": "Easy", "lives": 4, "seconds": 70, "speed": 0.78, "starting_storms": 2, "storm_every": 6, "max_storms": 5},
	{"name": "Normal", "lives": 3, "seconds": 55, "speed": 1.0, "starting_storms": 3, "storm_every": 5, "max_storms": 6},
	{"name": "Hard", "lives": 2, "seconds": 45, "speed": 1.25, "starting_storms": 4, "storm_every": 4, "max_storms": 100000000000000},
)


class LumenRun:
	def __init__(self, root):
		self.root = root
		self.root.title("Lumen Run")
		self.root.resizable(False, False)
		self.root.configure(bg="#080b18")

		self.canvas = tk.Canvas(
			root,
			width=WIDTH,
			height=HEIGHT,
			bg="#080b18",
			highlightthickness=0,
		)
		self.canvas.pack()

		self.random = random.Random()
		self.keys = set()
		self.difficulty_index = 1
		self.mode = "timed"
		self.save_path = Path.home() / ".lumen_run_save.json"
		self.wallet = self._load_wallet()
		self.pending_upgrades = {"wing": 0, "dash": 0, "time": 0}
		self.market_message = ""
		self.state = "title"
		self.last_tick = time.monotonic()
		self.stars = []
		self._draw_background()
		self._reset_run()

		self.root.bind_all("<KeyPress>", self._key_down)
		self.root.bind_all("<KeyRelease>", self._key_up)
		self._tick()

	def _load_wallet(self):
		try:
			data = json.loads(self.save_path.read_text(encoding="utf-8"))
			return max(0, int(data.get("wallet", 0)))
		except (OSError, ValueError, TypeError, AttributeError):
			return 0

	def _save_wallet(self):
		try:
			self.save_path.write_text(
				json.dumps({"wallet": self.wallet}, indent=2) + "\n",
				encoding="utf-8",
			)
		except OSError:
			pass

	def _open_market(self):
		self._reset_run()
		self.storms.clear()
		self.state = "market"
		self.market_message = "Choose an upgrade, then head out."

	def _buy_upgrade(self, upgrade):
		items = {
			"wing": ("Extra wing", 8, 2),
			"dash": ("Swift dash", 6, 1),
			"time": ("Time charm", 6, 1),
		}
		name, price, limit = items[upgrade]
		if upgrade == "time" and self.mode == "endless":
			self.market_message = "The Time Charm only works in timed mode."
		elif self.pending_upgrades[upgrade] >= limit:
			self.market_message = f"{name} is already at its limit."
		elif self.wallet < price:
			self.market_message = f"You need {price - self.wallet} more lights for {name}."
		else:
			self.wallet -= price
			self.pending_upgrades[upgrade] += 1
			self._save_wallet()
			self.market_message = f"{name} added to this run."

	def _begin_run(self):
		self._reset_run()
		self.lives += self.pending_upgrades["wing"]
		if self.mode == "timed":
			self.seconds_left += self.pending_upgrades["time"] * 10
		self.dash_recharge = 0.65 if self.pending_upgrades["dash"] else 1.0
		self.pending_upgrades = {"wing": 0, "dash": 0, "time": 0}
		self.spawn_delay = 4.0
		self.storm_warnings = []
		self.pending_storm_spawns = 0
		self.storm_spawn_gap = 0.0
		self.state = "countdown"

	def _update_countdown(self, delta):
		self._move_player(delta)
		self.spawn_delay = max(0, self.spawn_delay - delta)
		for particle in self.particles[:]:
			particle[0] += particle[2] * delta
			particle[1] += particle[3] * delta
			particle[4] -= delta
			if particle[4] <= 0:
				self.particles.remove(particle)
		if self.spawn_delay <= 0:
			settings = DIFFICULTIES[self.difficulty_index]
			self.pending_storm_spawns = settings["starting_storms"]
			self.state = "playing"

	def _draw_background(self):
		canvas = self.canvas
		top = (7, 10, 26)
		bottom = (27, 31, 65)
		bands = 64
		for index in range(bands):
			amount = index / (bands - 1)
			color = "#" + "".join(
				f"{round(start + (end - start) * amount):02x}"
				for start, end in zip(top, bottom)
			)
			y1 = index * HEIGHT / bands
			y2 = (index + 1) * HEIGHT / bands + 1
			canvas.create_rectangle(0, y1, WIDTH, y2, fill=color, outline="", tags="background")

		for _ in range(90):
			x = self.random.randrange(WIDTH)
			y = self.random.randrange(30, 430)
			radius = self.random.choice((1, 1, 1, 2))
			color = self.random.choice(("#59618b", "#8e9bc5", "#d8c8ed"))
			self.stars.append((x, y, radius, color))
			canvas.create_oval(
				x - radius, y - radius, x + radius, y + radius,
				fill=color, outline="", tags="background",
			)

		canvas.create_oval(718, 54, 854, 190, fill="#343b66", outline="", tags="background")
		canvas.create_oval(732, 45, 858, 171, fill="#f2d9a8", outline="", tags="background")
		canvas.create_oval(762, 73, 786, 97, fill="#e2c99e", outline="", tags="background")
		canvas.create_oval(809, 119, 827, 137, fill="#e2c99e", outline="", tags="background")
		canvas.create_oval(777, 136, 789, 148, fill="#e2c99e", outline="", tags="background")

		canvas.create_polygon(
			0, 405, 105, 319, 202, 389, 328, 292, 460, 396,
			577, 321, 707, 399, 839, 304, 960, 382, 960, HEIGHT, 0, HEIGHT,
			fill="#171b3b", outline="", tags="background",
		)
		canvas.create_polygon(
			0, 463, 133, 387, 261, 467, 397, 371, 555, 468,
			700, 389, 838, 471, 960, 403, 960, HEIGHT, 0, HEIGHT,
			fill="#10172e", outline="", tags="background",
		)
		canvas.create_rectangle(0, 493, WIDTH, HEIGHT, fill="#0c1428", outline="", tags="background")
		for x in range(-20, WIDTH + 40, 42):
			height = self.random.randrange(18, 54)
			canvas.create_rectangle(
				x, 500 - height, x + 3, 500,
				fill="#27314b", outline="", tags="background",
			)
		canvas.create_line(0, 500, WIDTH, 500, fill="#374363", width=2, tags="background")

	def _reset_run(self):
		self.player_x = WIDTH / 2
		self.player_y = HEIGHT - 100
		self.facing_x = 1.0
		self.facing_y = 0.0
		self.score = 0
		settings = DIFFICULTIES[self.difficulty_index]
		self.lives = settings["lives"]
		self.seconds_left = settings["seconds"]
		self.invulnerable = 0.0
		self.dash_time = 0.0
		self.dash_cooldown = 0.0
		self.dash_recharge = 1.0
		self.motes = []
		self.storms = []
		self.storm_warnings = []
		self.pending_storm_spawns = 0
		self.storm_spawn_gap = 0.0
		self.particles = []
		for _ in range(5):
			self._spawn_mote()

	def _spawn_mote(self):
		self.motes.append({
			"x": self.random.randrange(55, WIDTH - 55),
			"y": self.random.randrange(125, HEIGHT - 75),
			"phase": self.random.random() * math.tau,
		})

	def _spawn_storm(self):
		for _ in range(12):
			x = self.random.randrange(70, WIDTH - 70)
			y = self.random.randrange(145, HEIGHT - 70)
			if math.hypot(self.player_x - x, self.player_y - y) >= 180:
				break
		self.storm_warnings.append({"x": x, "y": y, "ttl": 1.15, "phase": 0.0})

	def _create_storm(self, x, y):
		angle = self.random.random() * math.tau
		settings = DIFFICULTIES[self.difficulty_index]
		speed = (self.random.uniform(68, 108) + self.score * 1.5) * settings["speed"]
		self.storms.append({
			"x": x,
			"y": y,
			"vx": math.cos(angle) * speed,
			"vy": math.sin(angle) * speed,
			"radius": self.random.randrange(16, 23),
			"phase": self.random.random() * math.tau,
		})

	def _key_down(self, event):
		key = event.keysym.lower()
		if key in self.keys:
			return
		self.keys.add(key)

		if self.state == "title" and key in ("left", "a"):
			self.difficulty_index = (self.difficulty_index - 1) % len(DIFFICULTIES)
		elif self.state == "title" and key in ("right", "d"):
			self.difficulty_index = (self.difficulty_index + 1) % len(DIFFICULTIES)
		elif self.state == "title" and key == "m":
			self.mode = "endless" if self.mode == "timed" else "timed"
		elif self.state == "title" and key in ("return", "space"):
			self._open_market()
		elif self.state == "market" and key in ("1", "2", "3"):
			self._buy_upgrade({"1": "wing", "2": "dash", "3": "time"}[key])
		elif self.state == "market" and key in ("return", "space"):
			self._begin_run()
		elif self.state in ("won", "lost") and key in ("return", "space", "r"):
			self._open_market()
		elif key == "escape":
			self.state = "title"
		elif key == "p" and self.state == "playing":
			self.state = "paused"
		elif key == "p" and self.state == "paused":
			self.state = "playing"
			self.last_tick = time.monotonic()
		elif key == "space" and self.state == "playing" and self.dash_cooldown <= 0:
			self.dash_time = 0.19
			self.dash_cooldown = self.dash_recharge

	def _key_up(self, event):
		self.keys.discard(event.keysym.lower())

	def _move_player(self, delta):
		horizontal = int(bool(self.keys & {"right", "d"})) - int(bool(self.keys & {"left", "a"}))
		vertical = int(bool(self.keys & {"down", "s"})) - int(bool(self.keys & {"up", "w"}))
		if horizontal or vertical:
			length = math.hypot(horizontal, vertical)
			self.facing_x = horizontal / length
			self.facing_y = vertical / length

		speed = 600 if self.dash_time > 0 else 235
		self.player_x += self.facing_x * speed * delta if self.dash_time > 0 else horizontal / max(1, math.hypot(horizontal, vertical)) * speed * delta
		self.player_y += self.facing_y * speed * delta if self.dash_time > 0 else vertical / max(1, math.hypot(horizontal, vertical)) * speed * delta
		self.player_x = min(WIDTH - 28, max(28, self.player_x))
		self.player_y = min(HEIGHT - 34, max(112, self.player_y))

	def _burst(self, x, y, color, count=12):
		for _ in range(count):
			angle = self.random.random() * math.tau
			speed = self.random.uniform(35, 155)
			lifetime = self.random.uniform(0.35, 0.75)
			self.particles.append([
				x, y, math.cos(angle) * speed, math.sin(angle) * speed,
				lifetime, lifetime, color,
			])

	def _update(self, delta):
		if self.mode == "timed":
			self.seconds_left -= delta
		self.invulnerable = max(0, self.invulnerable - delta)
		self.dash_time = max(0, self.dash_time - delta)
		self.dash_cooldown = max(0, self.dash_cooldown - delta)
		self._move_player(delta)

		for storm in self.storms:
			storm["x"] += storm["vx"] * delta
			storm["y"] += storm["vy"] * delta
			if storm["x"] < 35 or storm["x"] > WIDTH - 35:
				storm["vx"] *= -1
			if storm["y"] < 120 or storm["y"] > HEIGHT - 35:
				storm["vy"] *= -1
			storm["phase"] += delta * 3

		self.storm_spawn_gap = max(0, self.storm_spawn_gap - delta)
		for warning in self.storm_warnings[:]:
			warning["ttl"] -= delta
			warning["phase"] += delta * 8
			if warning["ttl"] <= 0:
				self._create_storm(warning["x"], warning["y"])
				self.storm_warnings.remove(warning)
		if self.pending_storm_spawns and not self.storm_warnings and self.storm_spawn_gap <= 0:
			self._spawn_storm()
			self.pending_storm_spawns -= 1
			self.storm_spawn_gap = 0.45

		for mote in self.motes[:]:
			mote["phase"] += delta * 2.4
			if math.hypot(self.player_x - mote["x"], self.player_y - mote["y"]) < 27:
				self.motes.remove(mote)
				self.score += 1
				self.wallet += 1
				self._save_wallet()
				self._burst(mote["x"], mote["y"], "#ffe19a")
				self._spawn_mote()
				settings = DIFFICULTIES[self.difficulty_index]
				active_storm_count = len(self.storms) + len(self.storm_warnings) + self.pending_storm_spawns
				if self.score % settings["storm_every"] == 0 and active_storm_count < settings["max_storms"]:
					self.pending_storm_spawns += 1

		if self.invulnerable <= 0:
			for storm in self.storms:
				if math.hypot(self.player_x - storm["x"], self.player_y - storm["y"]) < storm["radius"] + 11:
					self.lives -= 1
					self.invulnerable = 1.25
					self._burst(self.player_x, self.player_y, "#ff8296", 18)
					if self.lives <= 0:
						self.state = "lost"
					break

		for particle in self.particles[:]:
			particle[0] += particle[2] * delta
			particle[1] += particle[3] * delta
			particle[4] -= delta
			if particle[4] <= 0:
				self.particles.remove(particle)

		if self.mode == "timed" and self.score >= GOAL:
			self.state = "won"
		elif self.mode == "timed" and self.seconds_left <= 0 and self.state == "playing":
			self.state = "lost"

	def _draw_moth(self):
		if self.invulnerable > 0 and int(self.invulnerable * 12) % 2 == 0:
			return
		x, y = self.player_x, self.player_y
		forward_x, forward_y = self.facing_x, self.facing_y
		side_x, side_y = -forward_y, forward_x
		self.canvas.create_oval(x - 25, y - 25, x + 25, y + 25, fill="#463967", outline="", tags="frame")
		for direction in (-1, 1):
			points = (
				x - forward_x * 4 + side_x * direction * 4,
				y - forward_y * 4 + side_y * direction * 4,
				x - forward_x * 9 + side_x * direction * 24,
				y - forward_y * 9 + side_y * direction * 24,
				x + forward_x * 8 + side_x * direction * 18,
				y + forward_y * 8 + side_y * direction * 18,
				x + forward_x * 5,
				y + forward_y * 5,
			)
			self.canvas.create_polygon(
				*points, fill="#d5b8f2", outline="#f1d9ff", width=2, tags="frame",
			)
		self.canvas.create_oval(x - 6, y - 7, x + 6, y + 7, fill="#fff2c2", outline="", tags="frame")
		self.canvas.create_line(x, y - 5, x - 5, y - 13, fill="#fff2c2", width=1, tags="frame")
		self.canvas.create_line(x, y - 5, x + 5, y - 13, fill="#fff2c2", width=1, tags="frame")

	def _draw_hud(self):
		canvas = self.canvas
		canvas.create_rectangle(0, 0, WIDTH, 88, fill="#090e20", outline="", tags="frame")
		canvas.create_line(0, 87, WIDTH, 87, fill="#3a4261", width=1, tags="frame")
		canvas.create_text(28, 26, text="LUMEN RUN", anchor="w", fill="#f3e5ff", font=("TkDefaultFont", 15, "bold"), tags="frame")
		canvas.create_text(29, 55, text="NIGHT FLIGHT", anchor="w", fill="#8893b8", font=("TkDefaultFont", 8, "bold"), tags="frame")

		canvas.create_text(338, 23, text="LIGHTS", fill="#a4afce", font=("TkDefaultFont", 8, "bold"), tags="frame")
		score_text = f"{self.score:02d} / {GOAL}" if self.mode == "timed" else f"{self.score:02d}"
		canvas.create_text(338, 51, text=score_text, fill="#ffe6aa", font=("TkDefaultFont", 17, "bold"), tags="frame")
		if self.mode == "timed":
			canvas.create_rectangle(405, 20, 565, 29, fill="#232b48", outline="", tags="frame")
			canvas.create_rectangle(405, 20, 405 + 160 * min(1, self.score / GOAL), 29, fill="#f0c879", outline="", tags="frame")

		canvas.create_text(590, 23, text=DIFFICULTIES[self.difficulty_index]["name"].upper(), fill="#a4afce", font=("TkDefaultFont", 8, "bold"), tags="frame")
		canvas.create_text(590, 51, text=self.mode.upper(), fill="#a4afce", font=("TkDefaultFont", 8, "bold"), tags="frame")
		canvas.create_text(680, 23, text="TIME", fill="#a4afce", font=("TkDefaultFont", 8, "bold"), tags="frame")
		timer_color = "#ff8b9b" if self.seconds_left < 10 else "#f3e5ff"
		timer_text = f"{max(0, math.ceil(self.seconds_left)):02d}s" if self.mode == "timed" else "∞"
		canvas.create_text(680, 51, text=timer_text, fill=timer_color, font=("TkDefaultFont", 17, "bold"), tags="frame")
		canvas.create_text(815, 23, text="WINGS", fill="#a4afce", font=("TkDefaultFont", 8, "bold"), tags="frame")
		canvas.create_text(815, 51, text="♥ " * self.lives, fill="#ff91a3", font=("TkDefaultFont", 16, "bold"), tags="frame")
		canvas.create_text(932, 50, text="P  PAUSE", anchor="e", fill="#8893b8", font=("TkDefaultFont", 8), tags="frame")

	def _draw_world(self):
		canvas = self.canvas
		canvas.delete("frame")
		for storm in self.storms:
			x, y, radius = storm["x"], storm["y"], storm["radius"]
			canvas.create_oval(x - radius - 8, y - radius - 8, x + radius + 8, y + radius + 8, fill="#312747", outline="", tags="frame")
			canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#857095", outline="#c6a9c8", width=2, tags="frame")
			offset = math.sin(storm["phase"]) * 4
			canvas.create_oval(x - 7 + offset, y - 7, x + 7 + offset, y + 7, fill="#f0b4b1", outline="", tags="frame")
			canvas.create_oval(x - radius - 5, y - 2, x - radius + 3, y + 3, fill="#c49dc3", outline="", tags="frame")
			canvas.create_oval(x + radius - 3, y - 5, x + radius + 5, y + 2, fill="#c49dc3", outline="", tags="frame")

		for warning in self.storm_warnings:
			x, y = warning["x"], warning["y"]
			radius = 14 + (math.sin(warning["phase"]) + 1) * 3
			canvas.create_oval(
				x - radius, y - radius, x + radius, y + radius,
				outline="#ff9b9b", width=2, tags="frame",
			)
			canvas.create_line(x - 6, y, x + 6, y, fill="#ffe1b3", width=2, tags="frame")
			canvas.create_line(x, y - 6, x, y + 6, fill="#ffe1b3", width=2, tags="frame")

		for mote in self.motes:
			x, y = mote["x"], mote["y"] + math.sin(mote["phase"]) * 5
			radius = 8 + math.sin(mote["phase"] * 1.5) * 1.5
			canvas.create_oval(x - 18, y - 18, x + 18, y + 18, fill="#473b3c", outline="", tags="frame")
			canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="#ffe5a0", outline="#fff5d5", width=2, tags="frame")
			canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#fffdf0", outline="", tags="frame")

		for x, y, _, _, life, initial, color in self.particles:
			radius = max(1, 4 * life / initial)
			canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline="", tags="frame")

		self._draw_moth()
		self._draw_hud()

		if self.wallet:
			canvas.create_text(WIDTH - 28, HEIGHT - 24, text=f"BANK  {self.wallet}", anchor="e", fill="#ffe6aa", font=("TkDefaultFont", 9, "bold"), tags="frame")

		if self.dash_cooldown > 0:
			canvas.create_text(28, HEIGHT - 24, text=f"DASH  {'READY' if self.dash_cooldown <= 0 else f'{self.dash_cooldown:.1f}s'}", anchor="w", fill="#c7b7df", font=("TkDefaultFont", 9, "bold"), tags="frame")
		if self.state == "countdown":
			canvas.create_text(WIDTH / 2, HEIGHT - 24, text=f"SAFE START  {math.ceil(self.spawn_delay)}s", fill="#9de9ed", font=("TkDefaultFont", 9, "bold"), tags="frame")

	def _draw_market_stall(self):
		canvas = self.canvas
		x = self.player_x
		base_y = self.player_y - 58
		canvas.create_rectangle(x - 70, base_y - 34, x + 70, base_y + 12, fill="#493650", outline="#d2a9c5", width=2, tags="frame")
		canvas.create_rectangle(x - 82, base_y - 48, x + 82, base_y - 30, fill="#d78691", outline="#f5c2c2", width=2, tags="frame")
		for stripe_x in (x - 55, x - 5, x + 45):
			canvas.create_rectangle(stripe_x, base_y - 48, stripe_x + 24, base_y - 30, fill="#f2d9a8", outline="", tags="frame")
		canvas.create_text(x, base_y - 39, text="MOON MARKET", fill="#21182b", font=("TkDefaultFont", 8, "bold"), tags="frame")
		canvas.create_oval(x - 48, base_y - 19, x - 28, base_y + 1, fill="#ffe5a0", outline="#fff5d5", tags="frame")
		canvas.create_oval(x - 10, base_y - 19, x + 10, base_y + 1, fill="#a5e5e9", outline="#e0ffff", tags="frame")
		canvas.create_oval(x + 28, base_y - 19, x + 48, base_y + 1, fill="#d5b8f2", outline="#f1d9ff", tags="frame")

	def _draw_market(self):
		canvas = self.canvas
		self._draw_market_stall()
		canvas.create_rectangle(125, 100, 835, 426, fill="#0b1021", outline="#626b8a", width=2, tags="frame")
		canvas.create_text(WIDTH / 2, 132, text="MOON MARKET", fill="#ffe6aa", font=("TkDefaultFont", 23, "bold"), tags="frame")
		canvas.create_text(WIDTH / 2, 160, text=f"Your light purse: {self.wallet}", fill="#a7b0ce", font=("TkDefaultFont", 11), tags="frame")

		items = (
			("1", "EXTRA WING", "Start with one more life.", 8, "wing"),
			("2", "SWIFT DASH", "Recharge your dash faster.", 6, "dash"),
			("3", "TIME CHARM", "+10 seconds in timed mode.", 6, "time"),
		)
		for center_x, (key, title, description, price, upgrade) in zip((260, 480, 700), items):
			left, right = center_x - 98, center_x + 98
			canvas.create_rectangle(left, 186, right, 332, fill="#151c32", outline="#47516f", width=1, tags="frame")
			canvas.create_text(center_x, 207, text=title, fill="#e6d8f3", font=("TkDefaultFont", 10, "bold"), tags="frame")
			canvas.create_text(center_x, 244, text=description, fill="#a7b0ce", font=("TkDefaultFont", 9), tags="frame")
			if upgrade == "time" and self.mode == "endless":
				status = "TIMED ONLY"
			elif self.pending_upgrades[upgrade] >= (2 if upgrade == "wing" else 1):
				status = "PURCHASED"
			else:
				status = f"{price} LIGHTS  |  PRESS {key}"
			canvas.create_text(center_x, 285, text=status, fill="#ffe6aa", font=("TkDefaultFont", 9, "bold"), tags="frame")
			if self.pending_upgrades[upgrade]:
				canvas.create_text(center_x, 311, text=f"This run: {self.pending_upgrades[upgrade]}", fill="#9de9ed", font=("TkDefaultFont", 8), tags="frame")

		canvas.create_text(WIDTH / 2, 356, text=self.market_message, fill="#9de9ed", font=("TkDefaultFont", 9), tags="frame")
		canvas.create_text(WIDTH / 2, 385, text="1 / 2 / 3  BUY       ENTER  START RUN       ESC  TITLE", fill="#d1d6e8", font=("TkDefaultFont", 9, "bold"), tags="frame")
		canvas.create_text(WIDTH / 2, 405, text="After starting, move freely for 4 seconds before the storms arrive.", fill="#8994b6", font=("TkDefaultFont", 8), tags="frame")

	def _draw_overlay(self, title, subtitle, lines, accent):
		canvas = self.canvas
		canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#080b18", stipple="gray50", outline="", tags="frame")
		canvas.create_text(WIDTH / 2, 220, text=title, fill=accent, font=("TkDefaultFont", 36, "bold"), tags="frame")
		canvas.create_text(WIDTH / 2, 270, text=subtitle, fill="#e3d9ee", font=("TkDefaultFont", 15), tags="frame")
		for index, line in enumerate(lines):
			canvas.create_text(WIDTH / 2, 340 + index * 30, text=line, fill="#a7b0ce", font=("TkDefaultFont", 11), tags="frame")

	def _draw(self):
		self._draw_world()
		if self.state == "title":
			mode_hint = "20 lights before time runs out" if self.mode == "timed" else "survive as long as you can"
			self._draw_overlay(
				"LUMEN RUN",
				f"A little light goes a long way.  {mode_hint}.",
				(
					f"DIFFICULTY  < {DIFFICULTIES[self.difficulty_index]['name'].upper()} >  (LEFT / RIGHT)",
					f"MODE  {self.mode.upper()}  (M TO SWITCH)",
					"Collect lights. Dodge storm wisps. Three hits end your flight.",
					"WASD / ARROWS  MOVE       SPACE  DASH       P  PAUSE",
					"PRESS ENTER TO VISIT THE MARKET",
				),
				"#ffe6aa",
			)
		elif self.state == "market":
			self._draw_market()
		elif self.state == "paused":
			self._draw_overlay("PAUSED", "The night can wait.", ("Press P to return to your flight.", "ESC returns to the title screen."), "#e4d3ff")
		elif self.state == "won":
			self._draw_overlay("NIGHT LIT", f"You gathered {self.score} lights.", ("The garden is glowing because of you.", "PRESS ENTER FOR THE MARKET     ESC  TITLE"), "#ffe6aa")
		elif self.state == "lost":
			reason = "The storm caught your wings." if self.lives <= 0 else "The night slipped away."
			score_line = f"Endless score: {self.score}" if self.mode == "endless" else f"Lights gathered: {self.score} / {GOAL}"
			self._draw_overlay("FLIGHT OVER", reason, (score_line, "PRESS ENTER FOR THE MARKET     ESC  TITLE"), "#ff9aaa")

	def _tick(self):
		now = time.monotonic()
		delta = min(0.05, now - self.last_tick)
		self.last_tick = now
		if self.state == "playing":
			self._update(delta)
		elif self.state == "countdown":
			self._update_countdown(delta)
		self._draw()
		self.root.after(16, self._tick)


def main():
	root = tk.Tk()
	LumenRun(root)
	root.mainloop()


if __name__ == "__main__":
	main()
