import math
import random
import sys
from dataclasses import dataclass

import pygame
from pygame.math import Vector2


# ============================================================
# EIDOLON #014 — BOIDS
# FLOCKING SIMULATION
# ============================================================

WIDTH = 1280
HEIGHT = 800
FPS = 60

BACKGROUND = (3, 5, 11)
GRID_COLOR = (12, 17, 28)

MAX_BOIDS = 600
DEFAULT_BOIDS = 260

MIN_SPEED = 35.0
DEFAULT_MAX_SPEED = 185.0
MAX_SPEED_LIMIT = 500.0

MIN_FORCE = 5.0
DEFAULT_MAX_FORCE = 90.0
MAX_FORCE_LIMIT = 500.0

DEFAULT_PERCEPTION = 75.0
MIN_PERCEPTION = 25.0
MAX_PERCEPTION = 180.0

DEFAULT_SEPARATION_DISTANCE = 25.0

DEFAULT_SEPARATION_WEIGHT = 1.65
DEFAULT_ALIGNMENT_WEIGHT = 1.00
DEFAULT_COHESION_WEIGHT = 1.00

DEFAULT_AVOIDANCE_WEIGHT = 2.50

TRAIL_LENGTH = 28
TRAIL_SAMPLE_INTERVAL = 0.035

BOUNDARY_MARGIN = 100.0
BOUNDARY_FORCE = 65.0

OBSTACLE_COUNT = 5

CAMERA_ZOOM_MIN = 0.45
CAMERA_ZOOM_MAX = 2.5

INTRO_DURATION = 2.8


# ============================================================
# COLORS
# ============================================================

WHITE = (240, 244, 255)
TEXT = (180, 190, 210)
DIM_TEXT = (90, 105, 125)

CYAN = (70, 220, 255)
BLUE = (90, 145, 255)
PURPLE = (175, 100, 255)
PINK = (255, 100, 200)
ORANGE = (255, 165, 70)
YELLOW = (255, 225, 100)
RED = (255, 90, 100)
GREEN = (100, 230, 155)

PALETTES = {
    "EIDOLON": [
        (70, 220, 255),
        (120, 170, 255),
        (175, 110, 255),
        (255, 105, 205),
    ],
    "SOLAR": [
        (255, 235, 160),
        (255, 190, 90),
        (255, 125, 65),
        (235, 80, 80),
    ],
    "ICE": [
        (220, 250, 255),
        (145, 225, 255),
        (90, 170, 255),
        (120, 130, 235),
    ],
    "VOID": [
        (210, 120, 255),
        (150, 90, 230),
        (100, 75, 185),
        (255, 105, 205),
    ],
    "MATRIX": [
        (100, 255, 150),
        (60, 220, 120),
        (30, 175, 100),
        (120, 255, 180),
    ],
}


# ============================================================
# UTILITY
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = clamp(t, 0.0, 1.0)

    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


def palette_color(name):
    palette = PALETTES[name]

    if len(palette) == 1:
        return palette[0]

    index = random.randint(
        0,
        len(palette) - 2,
    )

    return lerp_color(
        palette[index],
        palette[index + 1],
        random.random(),
    )


def limit_vector(vector, maximum):
    length = vector.length()

    if length > maximum and length > 0:
        return vector.normalize() * maximum

    return vector


# ============================================================
# BOID
# ============================================================

@dataclass
class Boid:
    position: Vector2
    velocity: Vector2
    color: tuple

    def __post_init__(self):
        self.acceleration = Vector2(0, 0)
        self.trail = []

        self.size = random.uniform(
            3.0,
            5.0,
        )

    def apply_force(self, force):
        self.acceleration += force

    def update(self, dt, max_speed):
        self.velocity += (
            self.acceleration * dt
        )

        self.velocity = limit_vector(
            self.velocity,
            max_speed,
        )

        speed = self.velocity.length()

        if speed < MIN_SPEED:
            if speed > 0:
                self.velocity.scale_to_length(
                    MIN_SPEED
                )
            else:
                angle = random.uniform(
                    0,
                    math.tau,
                )

                self.velocity = Vector2(
                    math.cos(angle),
                    math.sin(angle),
                ) * MIN_SPEED

        self.position += (
            self.velocity * dt
        )

        self.acceleration.update(
            0,
            0,
        )


# ============================================================
# AUDIO
# ============================================================

class AudioManager:
    def __init__(self):
        self.enabled = True
        self.initialized = False

        try:
            pygame.mixer.pre_init(
                frequency=44100,
                size=-16,
                channels=1,
                buffer=512,
            )

            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.initialized = True

        except pygame.error:
            self.initialized = False

        self.near_miss_sounds = []

        if self.initialized:
            for frequency in (
                180,
                220,
                260,
                310,
            ):
                sound = self.create_tone(
                    frequency,
                    0.075,
                    0.10,
                    True,
                )

                if sound is not None:
                    self.near_miss_sounds.append(
                        sound
                    )

            self.start = self.create_tone(
                420,
                0.16,
                0.20,
                True,
            )

            self.tick = self.create_tone(
                620,
                0.06,
                0.12,
                True,
            )

            self.go = self.create_tone(
                880,
                0.22,
                0.25,
                True,
            )

            self.predator = self.create_tone(
                100,
                0.22,
                0.18,
                True,
            )

    def create_tone(
        self,
        frequency,
        duration,
        volume,
        decay=True,
    ):
        if not self.initialized:
            return None

        sample_rate = 44100

        count = int(
            sample_rate * duration
        )

        buffer = bytearray()

        for i in range(count):
            t = i / sample_rate

            envelope = 1.0

            if decay:
                envelope = max(
                    0.0,
                    1.0 - t / duration,
                )

            wave = math.sin(
                2.0
                * math.pi
                * frequency
                * t
            )

            wave += (
                0.18
                * math.sin(
                    2.0
                    * math.pi
                    * frequency
                    * 2.0
                    * t
                )
            )

            value = (
                wave
                * envelope
                * volume
            )

            sample = int(
                clamp(
                    value,
                    -1.0,
                    1.0,
                )
                * 32767
            )

            buffer += int(
                sample
            ).to_bytes(
                2,
                byteorder="little",
                signed=True,
            )

        try:
            return pygame.mixer.Sound(
                buffer=bytes(buffer)
            )

        except pygame.error:
            return None

    def play(self, sound):
        if (
            not self.initialized
            or not self.enabled
            or sound is None
        ):
            return

        sound.play()

    def near_miss(self):
        if not self.near_miss_sounds:
            return

        self.play(
            random.choice(
                self.near_miss_sounds
            )
        )

    def start_sound(self):
        self.play(self.start)

    def countdown_tick(self):
        self.play(self.tick)

    def go_sound(self):
        self.play(self.go)

    def predator_sound(self):
        self.play(self.predator)

    def toggle(self):
        self.enabled = not self.enabled


# ============================================================
# OBSTACLE
# ============================================================

@dataclass
class Obstacle:
    position: Vector2
    radius: float


# ============================================================
# BOIDS SIMULATION
# ============================================================

class BoidSimulation:
    def __init__(self):
        self.boids = []

        self.running = False
        self.paused = False

        self.simulation_speed = 1.0

        self.max_speed = DEFAULT_MAX_SPEED
        self.max_force = DEFAULT_MAX_FORCE

        self.perception_radius = (
            DEFAULT_PERCEPTION
        )

        self.separation_distance = (
            DEFAULT_SEPARATION_DISTANCE
        )

        self.separation_weight = (
            DEFAULT_SEPARATION_WEIGHT
        )

        self.alignment_weight = (
            DEFAULT_ALIGNMENT_WEIGHT
        )

        self.cohesion_weight = (
            DEFAULT_COHESION_WEIGHT
        )

        self.avoidance_weight = (
            DEFAULT_AVOIDANCE_WEIGHT
        )

        self.obstacles_enabled = True
        self.mouse_enabled = False
        self.mouse_repulsion = False

        self.predator_enabled = False
        self.predator_position = Vector2(
            WIDTH / 2,
            HEIGHT / 2,
        )

        self.trails_enabled = True
        self.trails_visible = True

        self.show_vectors = False
        self.show_perception = False

        self.wrap_edges = False

        self.palette_name = "EIDOLON"

        self.total_near_misses = 0

        self.trail_timer = 0.0
        self.sound_timer = 0.0

        self.obstacles = []

        self.create_obstacles()
        self.create_flock(
            DEFAULT_BOIDS
        )

    # ========================================================
    # CREATE OBSTACLES
    # ========================================================

    def create_obstacles(self):
        self.obstacles.clear()

        positions = [
            (280, 220),
            (640, 170),
            (990, 260),
            (430, 570),
            (850, 610),
        ]

        for x, y in positions:
            self.obstacles.append(
                Obstacle(
                    Vector2(x, y),
                    random.uniform(
                        35,
                        55,
                    ),
                )
            )

    # ========================================================
    # CREATE BOID
    # ========================================================

    def create_boid(
        self,
        position=None,
        velocity=None,
    ):
        if len(self.boids) >= MAX_BOIDS:
            return None

        if position is None:
            position = Vector2(
                random.uniform(
                    100,
                    WIDTH - 100,
                ),
                random.uniform(
                    100,
                    HEIGHT - 100,
                ),
            )

        if velocity is None:
            angle = random.uniform(
                0,
                math.tau,
            )

            velocity = Vector2(
                math.cos(angle),
                math.sin(angle),
            ) * random.uniform(
                60,
                self.max_speed,
            )

        return Boid(
            Vector2(position),
            Vector2(velocity),
            palette_color(
                self.palette_name
            ),
        )

    # ========================================================
    # CREATE FLOCK
    # ========================================================

    def create_flock(
        self,
        count,
    ):
        self.boids.clear()

        count = int(
            clamp(
                count,
                1,
                MAX_BOIDS,
            )
        )

        for _ in range(count):
            boid = self.create_boid()

            if boid is not None:
                self.boids.append(
                    boid
                )

    # ========================================================
    # SET BOID COUNT
    # ========================================================

    def set_boid_count(
        self,
        target,
    ):
        target = int(
            clamp(
                target,
                1,
                MAX_BOIDS,
            )
        )

        current = len(
            self.boids
        )

        if target > current:
            for _ in range(
                target - current
            ):
                boid = self.create_boid()

                if boid is not None:
                    self.boids.append(
                        boid
                    )

        elif target < current:
            del self.boids[target:]

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):
        self.create_flock(
            DEFAULT_BOIDS
        )

        self.running = False
        self.paused = False

        self.simulation_speed = 1.0

        self.max_speed = (
            DEFAULT_MAX_SPEED
        )

        self.max_force = (
            DEFAULT_MAX_FORCE
        )

        self.perception_radius = (
            DEFAULT_PERCEPTION
        )

        self.separation_weight = (
            DEFAULT_SEPARATION_WEIGHT
        )

        self.alignment_weight = (
            DEFAULT_ALIGNMENT_WEIGHT
        )

        self.cohesion_weight = (
            DEFAULT_COHESION_WEIGHT
        )

        self.avoidance_weight = (
            DEFAULT_AVOIDANCE_WEIGHT
        )

        self.mouse_enabled = False
        self.mouse_repulsion = False
        self.predator_enabled = False

        self.total_near_misses = 0

        for boid in self.boids:
            boid.trail.clear()

    # ========================================================
    # STEER
    # ========================================================

    def steer_towards(
        self,
        desired,
    ):
        if desired.length_squared() == 0:
            return Vector2()

        desired = desired.normalize()

        desired *= self.max_speed

        steering = (
            desired
            - desired
        )

        return steering

    # ========================================================
    # SEPARATION
    # ========================================================

    def separation(
        self,
        boid,
    ):
        steering = Vector2()

        count = 0

        desired_distance = (
            self.separation_distance
        )

        for other in self.boids:
            if other is boid:
                continue

            offset = (
                boid.position
                - other.position
            )

            distance = offset.length()

            if (
                distance > 0
                and distance
                < desired_distance
            ):
                direction = (
                    offset.normalize()
                )

                steering += (
                    direction
                    / distance
                )

                count += 1

        if count > 0:
            steering /= count

        if steering.length_squared() > 0:
            steering = (
                steering.normalize()
                * self.max_speed
                - boid.velocity
            )

            steering = limit_vector(
                steering,
                self.max_force,
            )

        return steering

    # ========================================================
    # ALIGNMENT
    # ========================================================

    def alignment(
        self,
        boid,
    ):
        average_velocity = Vector2()

        count = 0

        radius = (
            self.perception_radius
        )

        for other in self.boids:
            if other is boid:
                continue

            distance = (
                boid.position.distance_to(
                    other.position
                )
            )

            if distance < radius:
                average_velocity += (
                    other.velocity
                )

                count += 1

        if count == 0:
            return Vector2()

        average_velocity /= count

        if (
            average_velocity.length_squared()
            == 0
        ):
            return Vector2()

        desired = (
            average_velocity.normalize()
            * self.max_speed
        )

        steering = (
            desired
            - boid.velocity
        )

        return limit_vector(
            steering,
            self.max_force,
        )

    # ========================================================
    # COHESION
    # ========================================================

    def cohesion(
        self,
        boid,
    ):
        center = Vector2()

        count = 0

        radius = (
            self.perception_radius
        )

        for other in self.boids:
            if other is boid:
                continue

            distance = (
                boid.position.distance_to(
                    other.position
                )
            )

            if distance < radius:
                center += (
                    other.position
                )

                count += 1

        if count == 0:
            return Vector2()

        center /= count

        desired = (
            center
            - boid.position
        )

        if desired.length_squared() == 0:
            return Vector2()

        desired = (
            desired.normalize()
            * self.max_speed
        )

        steering = (
            desired
            - boid.velocity
        )

        return limit_vector(
            steering,
            self.max_force,
        )

    # ========================================================
    # OBSTACLE AVOIDANCE
    # ========================================================

    def obstacle_avoidance(
        self,
        boid,
    ):
        if not self.obstacles_enabled:
            return Vector2()

        steering = Vector2()

        look_ahead = clamp(
            boid.velocity.length()
            * 0.55,
            25,
            90,
        )

        if boid.velocity.length() <= 0:
            return steering

        forward = (
            boid.velocity.normalize()
        )

        future_position = (
            boid.position
            + forward * look_ahead
        )

        for obstacle in self.obstacles:
            offset = (
                future_position
                - obstacle.position
            )

            distance = offset.length()

            safe_distance = (
                obstacle.radius
                + 35
            )

            if (
                distance
                < safe_distance
                and distance > 0
            ):
                strength = (
                    1.0
                    - distance
                    / safe_distance
                )

                steering += (
                    offset.normalize()
                    * self.max_force
                    * strength
                )

        return limit_vector(
            steering,
            self.max_force,
        )

    # ========================================================
    # BOUNDARY
    # ========================================================

    def boundary_force(
        self,
        boid,
    ):
        if self.wrap_edges:
            return Vector2()

        steering = Vector2()

        margin = BOUNDARY_MARGIN

        if boid.position.x < margin:
            strength = (
                1.0
                - boid.position.x
                / margin
            )

            steering.x += (
                BOUNDARY_FORCE
                * strength
            )

        elif (
            boid.position.x
            > WIDTH - margin
        ):
            strength = (
                1.0
                - (
                    WIDTH
                    - boid.position.x
                )
                / margin
            )

            steering.x -= (
                BOUNDARY_FORCE
                * strength
            )

        if boid.position.y < margin:
            strength = (
                1.0
                - boid.position.y
                / margin
            )

            steering.y += (
                BOUNDARY_FORCE
                * strength
            )

        elif (
            boid.position.y
            > HEIGHT - margin
        ):
            strength = (
                1.0
                - (
                    HEIGHT
                    - boid.position.y
                )
                / margin
            )

            steering.y -= (
                BOUNDARY_FORCE
                * strength
            )

        return steering

    # ========================================================
    # MOUSE FORCE
    # ========================================================

    def mouse_force(
        self,
        boid,
        mouse_position,
    ):
        if not self.mouse_enabled:
            return Vector2()

        mouse = Vector2(
            mouse_position
        )

        offset = (
            mouse
            - boid.position
        )

        distance = offset.length()

        influence_radius = 250.0

        if (
            distance <= 1
            or distance > influence_radius
        ):
            return Vector2()

        direction = (
            offset.normalize()
        )

        strength = (
            1.0
            - distance
            / influence_radius
        )

        if self.mouse_repulsion:
            direction *= -1

        desired = (
            direction
            * self.max_speed
            * strength
        )

        steering = (
            desired
            - boid.velocity
        )

        return limit_vector(
            steering,
            self.max_force,
        )

    # ========================================================
    # PREDATOR
    # ========================================================

    def predator_force(
        self,
        boid,
    ):
        if not self.predator_enabled:
            return Vector2()

        offset = (
            boid.position
            - self.predator_position
        )

        distance = offset.length()

        influence = 220.0

        if (
            distance <= 1
            or distance > influence
        ):
            return Vector2()

        strength = (
            1.0
            - distance
            / influence
        )

        desired = (
            offset.normalize()
            * self.max_speed
            * (
                1.0
                + strength * 1.5
            )
        )

        steering = (
            desired
            - boid.velocity
        )

        return limit_vector(
            steering,
            self.max_force
            * 1.5,
        )

    # ========================================================
    # WRAP
    # ========================================================

    def wrap_position(
        self,
        boid,
    ):
        if not self.wrap_edges:
            return

        if boid.position.x < 0:
            boid.position.x = WIDTH

        elif boid.position.x > WIDTH:
            boid.position.x = 0

        if boid.position.y < 0:
            boid.position.y = HEIGHT

        elif boid.position.y > HEIGHT:
            boid.position.y = 0

    # ========================================================
    # UPDATE TRAILS
    # ========================================================

    def update_trails(
        self,
        dt,
    ):
        if not self.trails_enabled:
            return

        self.trail_timer += dt

        if (
            self.trail_timer
            < TRAIL_SAMPLE_INTERVAL
        ):
            return

        self.trail_timer = 0.0

        for boid in self.boids:
            boid.trail.append(
                Vector2(
                    boid.position
                )
            )

            if (
                len(boid.trail)
                > TRAIL_LENGTH
            ):
                boid.trail.pop(0)

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        dt,
        mouse_position,
    ):
        if not self.running:
            return

        if self.paused:
            return

        scaled_dt = (
            dt
            * self.simulation_speed
        )

        # Calculate all forces first.
        for boid in self.boids:
            separation = (
                self.separation(
                    boid
                )
                * self.separation_weight
            )

            alignment = (
                self.alignment(
                    boid
                )
                * self.alignment_weight
            )

            cohesion = (
                self.cohesion(
                    boid
                )
                * self.cohesion_weight
            )

            avoidance = (
                self.obstacle_avoidance(
                    boid
                )
                * self.avoidance_weight
            )

            boundary = (
                self.boundary_force(
                    boid
                )
            )

            mouse = (
                self.mouse_force(
                    boid,
                    mouse_position,
                )
            )

            predator = (
                self.predator_force(
                    boid
                )
            )

            total_force = (
                separation
                + alignment
                + cohesion
                + avoidance
                + boundary
                + mouse
                + predator
            )

            total_force = limit_vector(
                total_force,
                self.max_force
                * 2.0,
            )

            boid.apply_force(
                total_force
            )

        # Update positions.
        for boid in self.boids:
            boid.update(
                scaled_dt,
                self.max_speed,
            )

            self.wrap_position(
                boid
            )

        self.update_trails(dt)

    # ========================================================
    # FLOCK CENTER
    # ========================================================

    def flock_center(self):
        if not self.boids:
            return Vector2(
                WIDTH / 2,
                HEIGHT / 2,
            )

        center = Vector2()

        for boid in self.boids:
            center += boid.position

        return (
            center
            / len(self.boids)
        )

    # ========================================================
    # AVERAGE SPEED
    # ========================================================

    def average_speed(self):
        if not self.boids:
            return 0.0

        total = sum(
            boid.velocity.length()
            for boid in self.boids
        )

        return (
            total
            / len(self.boids)
        )


# ============================================================
# CAMERA
# ============================================================

class Camera:
    def __init__(self):
        self.position = Vector2(
            WIDTH / 2,
            HEIGHT / 2,
        )

        self.zoom = 1.0

    def world_to_screen(
        self,
        position,
    ):
        return (
            position
            - self.position
        ) * self.zoom + Vector2(
            WIDTH / 2,
            HEIGHT / 2,
        )

    def screen_to_world(
        self,
        position,
    ):
        return (
            Vector2(position)
            - Vector2(
                WIDTH / 2,
                HEIGHT / 2,
            )
        ) / self.zoom + self.position

    def zoom_at(
        self,
        factor,
        mouse_position,
    ):
        before = (
            self.screen_to_world(
                mouse_position
            )
        )

        self.zoom *= factor

        self.zoom = clamp(
            self.zoom,
            CAMERA_ZOOM_MIN,
            CAMERA_ZOOM_MAX,
        )

        after = (
            self.screen_to_world(
                mouse_position
            )
        )

        self.position += (
            before - after
        )

    def reset(self):
        self.position = Vector2(
            WIDTH / 2,
            HEIGHT / 2,
        )

        self.zoom = 1.0


# ============================================================
# APPLICATION
# ============================================================

class BoidsApp:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (
                WIDTH,
                HEIGHT,
            )
        )

        pygame.display.set_caption(
            "EIDOLON #014 — BOIDS"
        )

        self.clock = pygame.time.Clock()

        self.font_small = (
            pygame.font.SysFont(
                "consolas",
                14,
            )
        )

        self.font_medium = (
            pygame.font.SysFont(
                "consolas",
                18,
            )
        )

        self.font_large = (
            pygame.font.SysFont(
                "consolas",
                28,
                bold=True,
            )
        )

        self.font_huge = (
            pygame.font.SysFont(
                "consolas",
                64,
                bold=True,
            )
        )

        self.simulation = (
            BoidSimulation()
        )

        self.camera = Camera()

        self.audio = AudioManager()

        self.running = True

        self.started = False

        self.countdown_active = False
        self.countdown_value = 3
        self.countdown_timer = 0.0

        self.intro_active = True
        self.intro_timer = 0.0

        self.show_hud = True

        self.palette_index = 0
        self.palette_names = list(
            PALETTES.keys()
        )

        self.predator_flash = 0.0

        self.fps = 0.0

        self.last_near_miss_check = 0.0

    # ========================================================
    # TEXT
    # ========================================================

    def draw_text(
        self,
        text,
        position,
        font=None,
        color=TEXT,
        anchor="topleft",
    ):
        if font is None:
            font = self.font_small

        surface = font.render(
            str(text),
            True,
            color,
        )

        rect = surface.get_rect()

        if anchor == "center":
            rect.center = position

        elif anchor == "midtop":
            rect.midtop = position

        elif anchor == "midbottom":
            rect.midbottom = position

        elif anchor == "topright":
            rect.topright = position

        elif anchor == "bottomleft":
            rect.bottomleft = position

        elif anchor == "bottomright":
            rect.bottomright = position

        else:
            rect.topleft = position

        self.screen.blit(
            surface,
            rect,
        )

    # ========================================================
    # GRID
    # ========================================================

    def draw_grid(self):
        spacing = (
            80
            * self.camera.zoom
        )

        spacing = clamp(
            spacing,
            30,
            160,
        )

        center = (
            self.camera.world_to_screen(
                self.camera.position
            )
        )

        start_x = (
            center.x % spacing
        )

        start_y = (
            center.y % spacing
        )

        x = start_x

        while x < WIDTH:
            pygame.draw.line(
                self.screen,
                GRID_COLOR,
                (
                    int(x),
                    0,
                ),
                (
                    int(x),
                    HEIGHT,
                ),
            )

            x += spacing

        y = start_y

        while y < HEIGHT:
            pygame.draw.line(
                self.screen,
                GRID_COLOR,
                (
                    0,
                    int(y),
                ),
                (
                    WIDTH,
                    int(y),
                ),
            )

            y += spacing

    # ========================================================
    # TRAILS
    # ========================================================

    def draw_trails(self):
        if not self.simulation.trails_visible:
            return

        for boid in (
            self.simulation.boids
        ):
            if len(
                boid.trail
            ) < 2:
                continue

            points = []

            for position in boid.trail:
                screen_position = (
                    self.camera.world_to_screen(
                        position
                    )
                )

                points.append(
                    (
                        int(
                            screen_position.x
                        ),
                        int(
                            screen_position.y
                        ),
                    )
                )

            for i in range(
                1,
                len(points),
            ):
                progress = (
                    i
                    / len(points)
                )

                color = boid.color

                trail_color = (
                    int(
                        color[0]
                        * progress
                        * 0.45
                    ),
                    int(
                        color[1]
                        * progress
                        * 0.45
                    ),
                    int(
                        color[2]
                        * progress
                        * 0.45
                    ),
                )

                pygame.draw.line(
                    self.screen,
                    trail_color,
                    points[i - 1],
                    points[i],
                    1,
                )

    # ========================================================
    # BOID DRAW
    # ========================================================

    def draw_boid(
        self,
        boid,
    ):
        position = (
            self.camera.world_to_screen(
                boid.position
            )
        )

        velocity = boid.velocity

        if velocity.length_squared() == 0:
            direction = Vector2(
                1,
                0,
            )
        else:
            direction = (
                velocity.normalize()
            )

        side = direction.rotate(140)
        other_side = direction.rotate(
            -140
        )

        size = (
            boid.size
            * self.camera.zoom
        )

        tip = (
            position
            + direction * size * 2.8
        )

        left = (
            position
            + side * size
        )

        right = (
            position
            + other_side * size
        )

        pygame.draw.polygon(
            self.screen,
            boid.color,
            [
                (
                    int(tip.x),
                    int(tip.y),
                ),
                (
                    int(left.x),
                    int(left.y),
                ),
                (
                    int(right.x),
                    int(right.y),
                ),
            ],
        )

        # Small glow.
        if size > 2:
            glow = pygame.Surface(
                (
                    20,
                    20,
                ),
                pygame.SRCALPHA,
            )

            pygame.draw.circle(
                glow,
                (
                    boid.color[0],
                    boid.color[1],
                    boid.color[2],
                    30,
                ),
                (
                    10,
                    10,
                ),
                8,
            )

            self.screen.blit(
                glow,
                (
                    int(
                        position.x
                        - 10
                    ),
                    int(
                        position.y
                        - 10
                    ),
                ),
            )

    # ========================================================
    # BOIDS
    # ========================================================

    def draw_boids(self):
        for boid in (
            self.simulation.boids
        ):
            self.draw_boid(
                boid
            )

    # ========================================================
    # VECTORS
    # ========================================================

    def draw_vectors(self):
        if not self.simulation.show_vectors:
            return

        for boid in (
            self.simulation.boids
        ):
            start = (
                self.camera.world_to_screen(
                    boid.position
                )
            )

            vector = (
                boid.velocity
                * 0.25
                * self.camera.zoom
            )

            end = start + vector

            pygame.draw.line(
                self.screen,
                (
                    70,
                    200,
                    240,
                ),
                start,
                end,
                1,
            )

    # ========================================================
    # PERCEPTION CIRCLES
    # ========================================================

    def draw_perception(self):
        if not self.simulation.show_perception:
            return

        # Drawing all circles becomes expensive at high
        # population, so visualize only a sample.
        step = max(
            1,
            len(
                self.simulation.boids
            )
            // 25,
        )

        radius = int(
            self.simulation.perception_radius
            * self.camera.zoom
        )

        for boid in (
            self.simulation.boids[
                ::step
            ]
        ):
            position = (
                self.camera.world_to_screen(
                    boid.position
                )
            )

            pygame.draw.circle(
                self.screen,
                (
                    50,
                    100,
                    140,
                ),
                (
                    int(position.x),
                    int(position.y),
                ),
                radius,
                1,
            )

    # ========================================================
    # OBSTACLES
    # ========================================================

    def draw_obstacles(self):
        if not self.simulation.obstacles_enabled:
            return

        for obstacle in (
            self.simulation.obstacles
        ):
            position = (
                self.camera.world_to_screen(
                    obstacle.position
                )
            )

            radius = int(
                obstacle.radius
                * self.camera.zoom
            )

            pygame.draw.circle(
                self.screen,
                (
                    25,
                    35,
                    50,
                ),
                (
                    int(position.x),
                    int(position.y),
                ),
                radius,
            )

            pygame.draw.circle(
                self.screen,
                (
                    50,
                    75,
                    100,
                ),
                (
                    int(position.x),
                    int(position.y),
                ),
                radius,
                1,
            )

    # ========================================================
    # PREDATOR
    # ========================================================

    def draw_predator(self):
        if not self.simulation.predator_enabled:
            return

        position = (
            self.camera.world_to_screen(
                self.simulation.predator_position
            )
        )

        radius = int(
            18
            * self.camera.zoom
        )

        pygame.draw.circle(
            self.screen,
            RED,
            (
                int(position.x),
                int(position.y),
            ),
            radius,
            2,
        )

        pygame.draw.circle(
            self.screen,
            (
                255,
                50,
                70,
            ),
            (
                int(position.x),
                int(position.y),
            ),
            5,
        )

    # ========================================================
    # MOUSE
    # ========================================================

    def draw_mouse_field(
        self,
        mouse_position,
    ):
        if not self.simulation.mouse_enabled:
            return

        radius = int(
            250
            * self.camera.zoom
        )

        color = (
            255,
            90,
            100,
        )

        if not self.simulation.mouse_repulsion:
            color = CYAN

        pygame.draw.circle(
            self.screen,
            color,
            mouse_position,
            radius,
            1,
        )

        pygame.draw.circle(
            self.screen,
            color,
            mouse_position,
            5,
        )

    # ========================================================
    # HUD
    # ========================================================

    def draw_hud(self):
        if not self.show_hud:
            return

        panel = pygame.Surface(
            (
                425,
                350,
            ),
            pygame.SRCALPHA,
        )

        panel.fill(
            (
                3,
                6,
                14,
                225,
            )
        )

        self.screen.blit(
            panel,
            (
                16,
                16,
            ),
        )

        self.draw_text(
            "BOIDS / FLOCKING",
            (
                32,
                28,
            ),
            self.font_medium,
            WHITE,
        )

        self.draw_text(
            f"BOIDS        "
            f"{len(self.simulation.boids):03d}"
            f" / {MAX_BOIDS}",
            (
                32,
                58,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"PERCEPTION   "
            f"{self.simulation.perception_radius:5.1f}",
            (
                32,
                80,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"SPEED        "
            f"{self.simulation.max_speed:5.1f}",
            (
                32,
                102,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"FORCE        "
            f"{self.simulation.max_force:5.1f}",
            (
                32,
                124,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"SEPARATION   "
            f"{self.simulation.separation_weight:4.2f}",
            (
                32,
                146,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"ALIGNMENT    "
            f"{self.simulation.alignment_weight:4.2f}",
            (
                32,
                168,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"COHESION     "
            f"{self.simulation.cohesion_weight:4.2f}",
            (
                32,
                190,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"AVERAGE VEL  "
            f"{self.simulation.average_speed():5.1f}",
            (
                32,
                212,
            ),
            self.font_small,
            CYAN,
        )

        self.draw_text(
            f"SIM SPEED    "
            f"{self.simulation.simulation_speed:4.1f}x",
            (
                32,
                234,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"ZOOM         "
            f"{self.camera.zoom:4.2f}x",
            (
                32,
                256,
            ),
            self.font_small,
            TEXT,
        )

        self.draw_text(
            f"FPS          "
            f"{self.fps:5.1f}",
            (
                32,
                278,
            ),
            self.font_small,
            TEXT,
        )

        mode = "COHESIVE"

        if self.simulation.predator_enabled:
            mode = "PREDATOR"

        elif self.simulation.mouse_enabled:
            if self.simulation.mouse_repulsion:
                mode = "MOUSE REPEL"
            else:
                mode = "MOUSE ATTRACT"

        self.draw_text(
            f"MODE         {mode}",
            (
                32,
                300,
            ),
            self.font_small,
            ORANGE,
        )

        state = "RUNNING"

        if self.simulation.paused:
            state = "PAUSED"

        elif not self.started:
            state = "READY"

        self.draw_text(
            state,
            (
                405,
                28,
            ),
            self.font_small,
            CYAN,
            anchor="topright",
        )

        self.draw_text(
            "SPACE START/PAUSE   "
            "Q/A BODIES   "
            "WHEEL/Z/X ZOOM",
            (
                WIDTH - 16,
                HEIGHT - 38,
            ),
            self.font_small,
            DIM_TEXT,
            anchor="bottomright",
        )

        self.draw_text(
            "[/ ] PERCEPTION   "
            "1/2/3 RULES   "
            "ESC QUIT",
            (
                WIDTH - 16,
                HEIGHT - 18,
            ),
            self.font_small,
            DIM_TEXT,
            anchor="bottomright",
        )

    # ========================================================
    # INTRO
    # ========================================================

    def draw_intro(self):
        overlay = pygame.Surface(
            (
                WIDTH,
                HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (
                0,
                0,
                0,
                175,
            )
        )

        self.screen.blit(
            overlay,
            (
                0,
                0,
            ),
        )

        center_x = WIDTH // 2

        self.draw_text(
            "EIDOLON",
            (
                center_x,
                190,
            ),
            self.font_medium,
            CYAN,
            anchor="center",
        )

        self.draw_text(
            "BOIDS",
            (
                center_x,
                255,
            ),
            self.font_huge,
            WHITE,
            anchor="center",
        )

        self.draw_text(
            "FLOCKING SIMULATION",
            (
                center_x,
                325,
            ),
            self.font_large,
            WHITE,
            anchor="center",
        )

        self.draw_text(
            "THREE SIMPLE RULES → EMERGENT BEHAVIOR",
            (
                center_x,
                390,
            ),
            self.font_medium,
            TEXT,
            anchor="center",
        )

        self.draw_text(
            "SEPARATION  •  ALIGNMENT  •  COHESION",
            (
                center_x,
                425,
            ),
            self.font_small,
            DIM_TEXT,
            anchor="center",
        )

        self.draw_text(
            "PRESS SPACE TO START",
            (
                center_x,
                510,
            ),
            self.font_medium,
            CYAN,
            anchor="center",
        )

    # ========================================================
    # COUNTDOWN
    # ========================================================

    def draw_countdown(self):
        overlay = pygame.Surface(
            (
                WIDTH,
                HEIGHT,
            ),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (
                0,
                0,
                0,
                110,
            )
        )

        self.screen.blit(
            overlay,
            (
                0,
                0,
            ),
        )

        center = (
            WIDTH // 2,
            HEIGHT // 2,
        )

        if self.countdown_value > 0:
            self.draw_text(
                str(
                    self.countdown_value
                ),
                center,
                self.font_huge,
                CYAN,
                anchor="center",
            )

            self.draw_text(
                "FLOCK INITIALIZING",
                (
                    center[0],
                    center[1] + 70,
                ),
                self.font_small,
                TEXT,
                anchor="center",
            )

        else:
            self.draw_text(
                "GO",
                center,
                self.font_huge,
                WHITE,
                anchor="center",
            )

    # ========================================================
    # START COUNTDOWN
    # ========================================================

    def start_countdown(self):
        if self.started:
            return

        if self.countdown_active:
            return

        self.countdown_active = True
        self.countdown_value = 3
        self.countdown_timer = 0.0

        self.audio.start_sound()

    def finish_start(self):
        self.countdown_active = False
        self.started = True

        self.simulation.running = True
        self.simulation.paused = False

        self.audio.go_sound()

    # ========================================================
    # PALETTE
    # ========================================================

    def cycle_palette(self):
        self.palette_index += 1

        if (
            self.palette_index
            >= len(
                self.palette_names
            )
        ):
            self.palette_index = 0

        name = self.palette_names[
            self.palette_index
        ]

        self.simulation.palette_name = name

        for boid in (
            self.simulation.boids
        ):
            boid.color = (
                palette_color(name)
            )

    # ========================================================
    # KEYBOARD
    # ========================================================

    def handle_key(
        self,
        event,
    ):
        key = event.key

        # ----------------------------------------------------
        # QUIT
        # ----------------------------------------------------

        if key == pygame.K_ESCAPE:
            self.running = False
            return

        # ----------------------------------------------------
        # START / PAUSE
        # ----------------------------------------------------

        if key == pygame.K_SPACE:
            if not self.started:
                self.start_countdown()
            else:
                self.simulation.paused = (
                    not self.simulation.paused
                )

            return

        # ----------------------------------------------------
        # RESET
        # ----------------------------------------------------

        if key == pygame.K_r:
            self.simulation.reset()

            self.started = False
            self.countdown_active = False
            self.countdown_value = 3
            self.countdown_timer = 0.0

            self.camera.reset()

            return

        # ----------------------------------------------------
        # BOID COUNT
        # ----------------------------------------------------

        if key == pygame.K_q:
            self.simulation.set_boid_count(
                len(
                    self.simulation.boids
                )
                + 10
            )

            return

        if key == pygame.K_a:
            self.simulation.set_boid_count(
                len(
                    self.simulation.boids
                )
                - 10
            )

            return

        # ----------------------------------------------------
        # ZOOM
        # ----------------------------------------------------

        if key == pygame.K_z:
            self.camera.zoom_at(
                1.15,
                (
                    WIDTH // 2,
                    HEIGHT // 2,
                ),
            )

            return

        if key == pygame.K_x:
            self.camera.zoom_at(
                1 / 1.15,
                (
                    WIDTH // 2,
                    HEIGHT // 2,
                ),
            )

            return

        # ----------------------------------------------------
        # SIMULATION SPEED
        # ----------------------------------------------------

        if key in (
            pygame.K_EQUALS,
            pygame.K_PLUS,
            pygame.K_KP_PLUS,
        ):
            self.simulation.simulation_speed = clamp(
                self.simulation.simulation_speed
                + 0.25,
                0.25,
                4.0,
            )

            return

        if key in (
            pygame.K_MINUS,
            pygame.K_KP_MINUS,
        ):
            self.simulation.simulation_speed = clamp(
                self.simulation.simulation_speed
                - 0.25,
                0.25,
                4.0,
            )

            return

        # ----------------------------------------------------
        # PERCEPTION
        # ----------------------------------------------------

        if key == pygame.K_LEFTBRACKET:
            self.simulation.perception_radius = clamp(
                self.simulation.perception_radius
                - 10,
                MIN_PERCEPTION,
                MAX_PERCEPTION,
            )

            return

        if key == pygame.K_RIGHTBRACKET:
            self.simulation.perception_radius = clamp(
                self.simulation.perception_radius
                + 10,
                MIN_PERCEPTION,
                MAX_PERCEPTION,
            )

            return

        # ----------------------------------------------------
        # RULE STRENGTHS
        # ----------------------------------------------------

        if key == pygame.K_1:
            self.simulation.separation_weight = clamp(
                self.simulation.separation_weight
                + 0.15,
                0.0,
                5.0,
            )

            return

        if key == pygame.K_2:
            self.simulation.alignment_weight = clamp(
                self.simulation.alignment_weight
                + 0.15,
                0.0,
                5.0,
            )

            return

        if key == pygame.K_3:
            self.simulation.cohesion_weight = clamp(
                self.simulation.cohesion_weight
                + 0.15,
                0.0,
                5.0,
            )

            return

        # ----------------------------------------------------
        # LOWER RULE STRENGTHS
        # ----------------------------------------------------

        if key == pygame.K_4:
            self.simulation.separation_weight = clamp(
                self.simulation.separation_weight
                - 0.15,
                0.0,
                5.0,
            )

            return

        if key == pygame.K_5:
            self.simulation.alignment_weight = clamp(
                self.simulation.alignment_weight
                - 0.15,
                0.0,
                5.0,
            )

            return

        if key == pygame.K_6:
            self.simulation.cohesion_weight = clamp(
                self.simulation.cohesion_weight
                - 0.15,
                0.0,
                5.0,
            )

            return

        # ----------------------------------------------------
        # SPEED
        # ----------------------------------------------------

        if key == pygame.K_UP:
            self.simulation.max_speed = clamp(
                self.simulation.max_speed
                + 15,
                MIN_SPEED,
                MAX_SPEED_LIMIT,
            )

            return

        if key == pygame.K_DOWN:
            self.simulation.max_speed = clamp(
                self.simulation.max_speed
                - 15,
                MIN_SPEED,
                MAX_SPEED_LIMIT,
            )

            return

        # ----------------------------------------------------
        # OBSTACLES
        # ----------------------------------------------------

        if key == pygame.K_o:
            self.simulation.obstacles_enabled = (
                not self.simulation.obstacles_enabled
            )

            return

        # ----------------------------------------------------
        # MOUSE
        # ----------------------------------------------------

        if key == pygame.K_m:
            self.simulation.mouse_enabled = (
                not self.simulation.mouse_enabled
            )

            self.simulation.predator_enabled = False

            return

        if key == pygame.K_e:
            self.simulation.mouse_repulsion = (
                not self.simulation.mouse_repulsion
            )

            return

        # ----------------------------------------------------
        # PREDATOR
        # ----------------------------------------------------

        if key == pygame.K_p:
            self.simulation.predator_enabled = (
                not self.simulation.predator_enabled
            )

            self.simulation.mouse_enabled = False

            self.audio.predator_sound()

            return

        # ----------------------------------------------------
        # VISUALS
        # ----------------------------------------------------

        if key == pygame.K_t:
            self.simulation.trails_enabled = (
                not self.simulation.trails_enabled
            )

            return

        if key == pygame.K_v:
            self.simulation.trails_visible = (
                not self.simulation.trails_visible
            )

            return

        if key == pygame.K_f:
            self.simulation.show_vectors = (
                not self.simulation.show_vectors
            )

            return

        if key == pygame.K_d:
            self.simulation.show_perception = (
                not self.simulation.show_perception
            )

            return

        if key == pygame.K_h:
            self.show_hud = not self.show_hud
            return

        if key == pygame.K_w:
            self.simulation.wrap_edges = (
                not self.simulation.wrap_edges
            )

            return

        # ----------------------------------------------------
        # PALETTE
        # ----------------------------------------------------

        if key == pygame.K_c:
            self.cycle_palette()
            return

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        if key == pygame.K_m and event.mod & pygame.KMOD_SHIFT:
            self.audio.toggle()
            return

        if key == pygame.K_0:
            self.audio.toggle()
            return

    # ========================================================
    # MOUSE
    # ========================================================

    def handle_mouse_button(
        self,
        event,
    ):
        if event.button == 4:
            self.camera.zoom_at(
                1.15,
                event.pos,
            )

        elif event.button == 5:
            self.camera.zoom_at(
                1 / 1.15,
                event.pos,
            )

        elif event.button == 1:
            if not self.started:
                return

            if (
                len(
                    self.simulation.boids
                )
                >= MAX_BOIDS
            ):
                return

            world_position = (
                self.camera.screen_to_world(
                    event.pos
                )
            )

            boid = (
                self.simulation.create_boid(
                    position=world_position
                )
            )

            if boid is not None:
                self.simulation.boids.append(
                    boid
                )

    # ========================================================
    # PREDATOR MOUSE POSITION
    # ========================================================

    def update_predator_position(
        self,
    ):
        if not self.simulation.predator_enabled:
            return

        mouse_position = (
            pygame.mouse.get_pos()
        )

        self.simulation.predator_position = (
            self.camera.screen_to_world(
                mouse_position
            )
        )

    # ========================================================
    # COUNTDOWN
    # ========================================================

    def update_countdown(
        self,
        dt,
    ):
        if not self.countdown_active:
            return

        self.countdown_timer += dt

        if (
            self.countdown_timer >= 1.0
            and self.countdown_value > 0
        ):
            self.countdown_timer -= 1.0

            self.countdown_value -= 1

            if (
                self.countdown_value
                > 0
            ):
                self.audio.countdown_tick()

            else:
                self.finish_start()

    # ========================================================
    # NEAR-MISS AUDIO
    # ========================================================

    def update_collision_audio(
        self,
        dt,
    ):
        self.last_near_miss_check += dt

        if (
            self.last_near_miss_check
            < 0.18
        ):
            return

        self.last_near_miss_check = 0.0

        if len(
            self.simulation.boids
        ) < 2:
            return

        # Only sample a limited number of pairs
        # to keep audio detection cheap.
        sample_count = min(
            45,
            len(
                self.simulation.boids
            ),
        )

        candidates = random.sample(
            self.simulation.boids,
            sample_count,
        )

        for i in range(
            len(candidates)
        ):
            a = candidates[i]

            for j in range(
                i + 1,
                len(candidates),
            ):
                b = candidates[j]

                distance = (
                    a.position.distance_to(
                        b.position
                    )
                )

                if (
                    distance
                    < 12
                    and distance > 2
                ):
                    self.simulation.total_near_misses += 1

                    self.audio.near_miss()

                    return

    # ========================================================
    # DRAW
    # ========================================================

    def draw(self):
        self.screen.fill(
            BACKGROUND
        )

        self.draw_grid()

        self.draw_obstacles()

        self.draw_trails()

        self.draw_perception()

        self.draw_vectors()

        self.draw_boids()

        self.draw_predator()

        self.draw_mouse_field(
            pygame.mouse.get_pos()
        )

        self.draw_hud()

        if self.intro_active:
            self.draw_intro()

        elif self.countdown_active:
            self.draw_countdown()

        pygame.display.flip()

    # ========================================================
    # MAIN LOOP
    # ========================================================

    def run(self):
        while self.running:
            dt = (
                self.clock.tick(FPS)
                / 1000.0
            )

            dt = min(
                dt,
                0.05,
            )

            self.fps = (
                self.clock.get_fps()
            )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    self.handle_key(
                        event
                    )

                elif (
                    event.type
                    == pygame.MOUSEBUTTONDOWN
                ):
                    self.handle_mouse_button(
                        event
                    )

            if self.intro_active:
                self.intro_timer += dt

                if (
                    self.intro_timer
                    >= INTRO_DURATION
                ):
                    self.intro_active = False

            self.update_predator_position()

            self.update_countdown(dt)

            mouse_position = (
                self.camera.screen_to_world(
                    pygame.mouse.get_pos()
                )
            )

            self.simulation.update(
                dt,
                mouse_position,
            )

            self.update_collision_audio(
                dt
            )

            self.draw()

        pygame.quit()
        sys.exit()


# ============================================================
# SMOKE TEST
# ============================================================

def smoke_test():
    pygame.init()

    simulation = BoidSimulation()

    initial_count = len(
        simulation.boids
    )

    assert initial_count == (
        DEFAULT_BOIDS
    )

    simulation.set_boid_count(300)

    assert len(
        simulation.boids
    ) == 300

    simulation.perception_radius = 100

    assert (
        simulation.perception_radius
        == 100
    )

    simulation.running = True

    for _ in range(120):
        simulation.update(
            1.0 / 60.0,
            (
                WIDTH // 2,
                HEIGHT // 2,
            ),
        )

    assert len(
        simulation.boids
    ) == 300

    simulation.set_boid_count(150)

    assert len(
        simulation.boids
    ) == 150

    print(
        "BOIDS SMOKE TEST PASSED"
    )

    print(
        f"Initial bodies: {initial_count}"
    )

    print(
        f"Final bodies:   {len(simulation.boids)}"
    )

    print(
        "Flocking rules: separation + alignment + cohesion"
    )

    pygame.quit()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        smoke_test()
    else:
        app = BoidsApp()
        app.run()