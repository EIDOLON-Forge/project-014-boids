# EIDOLON #014 — BOIDS

> Three simple rules. One emergent flock.

BOIDS is a real-time flocking simulation built from scratch with Python and Pygame.

The simulation creates autonomous agents that follow three basic behavioral rules:

1. Separation
2. Alignment
3. Cohesion

No central controller tells the flock how to move.

Complex group behavior emerges from local interactions between neighboring agents.

---

## Features

- Real-time flocking simulation
- Separation behavior
- Alignment behavior
- Cohesion behavior
- Obstacle avoidance
- Boundary steering
- Mouse attraction
- Mouse repulsion
- Predator mode
- Adjustable perception radius
- Adjustable rule strengths
- Adjustable boid count
- Adjustable maximum speed
- Adjustable simulation speed
- Camera zoom
- Motion trails
- Velocity vectors
- Perception visualization
- Multiple color palettes
- Obstacle field
- Procedural audio
- Near-miss audio
- Start countdown
- Interactive HUD
- FPS display
- Smoke test

---

## Requirements

Python 3.12+ is recommended.

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

---

## Run

```bash
python main.py
```

---

## Smoke Test

Run:

```bash
python main.py --smoke-test
```

Expected output:

```text
BOIDS SMOKE TEST PASSED
Initial bodies: 260
Final bodies:   150
Flocking rules: separation + alignment + cohesion
```

---

# Controls

| Key | Action |
| --- | --- |
| `SPACE` | Start / Pause |
| `R` | Reset |
| `Q` | Add 10 boids |
| `A` | Remove 10 boids |
| `Mouse Wheel Up` | Zoom in |
| `Mouse Wheel Down` | Zoom out |
| `Z` | Zoom in |
| `X` | Zoom out |
| `+` | Increase simulation speed |
| `-` | Decrease simulation speed |
| `UP` | Increase maximum boid speed |
| `DOWN` | Decrease maximum boid speed |
| `[` | Decrease perception radius |
| `]` | Increase perception radius |
| `1` | Increase separation |
| `2` | Increase alignment |
| `3` | Increase cohesion |
| `4` | Decrease separation |
| `5` | Decrease alignment |
| `6` | Decrease cohesion |
| `O` | Toggle obstacles |
| `M` | Toggle mouse interaction |
| `E` | Toggle mouse attraction / repulsion |
| `P` | Toggle predator |
| `T` | Toggle trail recording |
| `V` | Toggle trails |
| `F` | Toggle velocity vectors |
| `D` | Toggle perception circles |
| `W` | Toggle edge wrapping |
| `C` | Change color palette |
| `H` | Toggle HUD |
| `0` | Toggle audio |
| `Left Mouse` | Spawn a boid |
| `ESC` | Quit |

---

# The Three Rules

## 1. Separation

Boids try to avoid getting too close to nearby boids.

This prevents the flock from collapsing into a single point.

Conceptually:

```text
If another boid is too close:
    move away from it.
```

---

## 2. Alignment

Boids try to match the direction of nearby boids.

Conceptually:

```text
Look at nearby velocities.
Calculate their average direction.
Steer toward it.
```

This causes groups of boids to begin moving together.

---

## 3. Cohesion

Boids try to move toward the center of nearby boids.

Conceptually:

```text
Find the center of nearby neighbors.
Steer toward that center.
```

This prevents the flock from spreading infinitely apart.

---

# Emergent Behavior

The interesting part of the simulation is that no rule explicitly says:

```text
"Create a flock."
```

Instead:

```text
Separation
     +
Alignment
     +
Cohesion
     +
Obstacle Avoidance
     ↓
Emergent Group Behavior
```

A large-scale flock emerges from many small local decisions.

---

# Steering

Each boid receives multiple steering forces:

```text
Total Force =
    Separation
  + Alignment
  + Cohesion
  + Obstacle Avoidance
  + Boundary Steering
  + Mouse Force
  + Predator Force
```

The resulting force changes the boid's acceleration.

Then:

```text
Acceleration
      ↓
Velocity
      ↓
Position
```

---

# Perception Radius

A boid does not need to know about every other boid.

It only considers nearby neighbors.

The perception radius determines how far a boid can "see."

### Small Radius

```text
Small local groups
More chaotic movement
```

### Large Radius

```text
More synchronized flock
Larger coordinated structures
```

---

# Predator Mode

Predator mode introduces an additional force.

Boids attempt to move away from the predator position.

The predator follows the mouse.

This creates a simple example of:

```text
Environment
     ↓
Threat
     ↓
Local reaction
     ↓
Collective movement
```

---

# Mouse Interaction

Mouse interaction can either attract or repel the flock.

This makes it possible to interact with the simulation in real time.

Move the mouse around the flock and observe how the local force propagates through the group.

---

# Complexity

The basic implementation compares each boid against every other boid.

For `N` boids:

```text
O(N²)
```

For example:

```text
100 boids   → ~10,000 comparisons
300 boids   → ~90,000 comparisons
600 boids   → ~360,000 comparisons
```

This is intentionally useful for the EIDOLON progression.

The next optimization step could introduce:

- Spatial grids
- Uniform grids
- Quadtrees
- Spatial hashing
- Barnes-Hut
- GPU computation

---

# Future Expansion

Potential future versions could include:

- Spatial partitioning
- Thousands of boids
- GPU flocking
- 3D flocking
- Predator / prey ecosystems
- Multiple species
- Obstacle mazes
- Swarm intelligence
- Reinforcement learning
- Neural flocking
- Autonomous drone simulation
- Robotics simulation

---

# Project Progression

EIDOLON #014 follows the physics and emergent-behavior progression:

```text
#005 Gravity Lab
        ↓
Basic physical interaction

#012 Double Pendulum
        ↓
Chaotic deterministic system

#013 N-Body Gravity
        ↓
Many-body physical interaction

#014 Boids
        ↓
Many-agent local interaction

Future
        ↓
Swarm intelligence
AI agents
Robotics
GPU simulations
```

---

# EIDOLON

EIDOLON is a 500+ project coding journey exploring:

- Programming
- Mathematics
- Physics
- Algorithms
- Graphics
- Simulations
- Games
- AI
- Cybersecurity
- Systems
- Engineering

One project at a time.

> **Build. Experiment. Break. Repeat.**
