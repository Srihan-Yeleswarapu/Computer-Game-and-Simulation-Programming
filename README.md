# Career Worlds (Computer-Game-and-Simulation-Programming)

An arcade-style set of mini-worlds that let players sample different careers. Each world has its own scenario, visuals, and skill-based challenge, all built with the Python standard library (tkinter).

## How to run
1) Ensure Python 3.12+ is installed (tkinter comes with standard Windows installs).
2) From this folder, start the game:
   python main.py

## Controls
- Move: Arrow keys or WASD
- Select a world: Press `1`, `2`, `3`, `4`, `5`, or `6`  on the hub, or click a portal card
- After finishing a world: Press `Space` to return to the hub

## Worlds
- Firefighter Rescue: Grab five survivors while weaving through roaming flames that drain your timer.
- Chef Rush: Complete the recipe in the exact station order; spills slow you down and melt the clock.
- Software Engineer: Patch code nodes in order while dodging "glitches" that reset your position and waste time.
- Marine Biologist: Dive, scan fish, and collect samples before O2 runs out.
- Architect: Design a stable Eco-Library that withstands the wind test.
- Doctor: Diagnose and provide solutions for sick patients. 

Each mini-world has a countdown clock, reactive hazards, and tailored tasks to keep the difficulty engaging.

# Technical Report

## Language Choice: Why Python?
We chose **Python** for this project due to its:
1.  **Standard Library Simplicity**: Python's `tkinter` allows for rapid GUI development without external dependencies, making the game easy to run on any machine with Python installed.
2.  **Cross-Platform capabilities**: The code runs seamlessly on Windows, macOS, and Linux.
    - Note: Windows is the only OS with audio functionality
3.  **Readability**: Python's clean syntax is ideal for defining complex game logic (like physics simulations) in a way that is easy to debug and extend.

## Attributions
1.  **Background Music**: ElevenLabs is used for background music

## Graphics Development & Appropriateness

### Tooling: Procedural Vector Art
All game graphics were developed using **native `tkinter.Canvas` primitives** (rectangles, ovals, polygons, arcs). We chose this approach to:
1.  **Eliminate Dependencies**: The game requires zero external image files or libraries like `PIL`, ensuring 100% portability.
2.  **Performance**: Vector-based drawing is highly efficient for the 60 FPS animation loop.

### Concept-Appropriate Asset Design
Graphics were procedurally drawn to match the professional concepts of each world:
-   **Software Engineer**: Uses a high-contrast dark-mode palette, mimicking a code IDE with floating glitch nodes and scanline CRT effects.
-   **Medical Simulation**: Employs a clean, clinical blue-and-white theme with active EKG heart-beat monitor animations.
-   **Marine Biology**: Features deep-sea gradients, simulated water-bubbles, and species-specific fish shapes with anatomical tail-pivot simulations.
-   **Architecture**: Uses an engineering grid blueprint style with background crane silhouettes to establish the "construction site" setting.
-   **Fire Rescue**: Utilizes a smoky, high-stakes aesthetic with flickering flame arcs and heat-shimmer effects.

## Architecture: Modular `BaseWorld` System
The core of the game is built on a scalable **inheritance-based architecture**:
-   **`BaseWorld`**: An abstract base class defining the contract for every mini-game (`reset`, `update`, `draw`, `cleanup`). It handles shared logic like the countdown timer and success/fail states.
-   **Polymorphism**: The `GameEngine` holds a collection of `BaseWorld` objects. It doesn't need to know the details of "Firefighter" vs "Chef"; it simply calls `active_world.update()`.
-   **Extensibility**: Adding a 7th career is as simple as creating a new class that inherits from `BaseWorld` and adding it to the engine's dictionary.

## Complexity Highlights

### 1. Physics Logic (`worlds/architect.py`)
The "Architect" world implements a custom physics engine:
-   **Breadth-First Search (BFS) for Gravity**: We verify structural integrity by running a BFS spread from the foundation nodes. Any block not reachable from the ground is identified as floating and subject to gravity.
-   **Wind Stress Simulation**: During the test phase, we calculate "wind drag" based on height (wind is stronger higher up). We compute a stress ratio (`Drag / MaterialStrength`) and use a probabilistic model to simulate material fracture and collapse.

### 2. Security Logic (`save_system.py`)
To prevent save scumming or tampering:
-   **HMAC-SHA256**: The save data is signed with a secret key.
-   **Integrity Check**: On load, we re-hash the payload. If the calculated signature doesn't match the stored signature, the save file is rejected (reset to empty). This ensures users cannot simply edit the JSON to unlock all careers.

## UX Rationale: The Hub System
The "Career Hub" (Main Menu) is designed for a **seamless user journey**:
-   **Instant Access**: Keyboards shortcuts (1-6) allow players to jump instantly into action without navigating nested menus.
-   **Visual Feedback**: Portals light up with a green outline when a job is mastered, giving immediate progress feedback.
-   **Non-Blocking Flow**: Users can hit `Escape` at any time to abort a mission and return to the Hub instantly.

## Accessibility Features
We have implemented several features to ensure the game is inclusive:

### 1. High Contrast Mode (New)
-   **Toggle**: Press `H` in the Main Menu.
-   **Implementation**: This mode swaps the colorful gradient background for a pure **Black** background and uses **Yellow/White** text. This maximizes readability for users with varying vision needs.

### 2. Universal HUD Visibility
-   **Dynamic Backgrounds**: We implemented a semi-transparent dark bar behind all transparent text (like the HUD). This prevents contrast issues where white text might be unreadable against light backgrounds (e.g., the bright sky in the Architect world).

### 3. Full Keyboard Playability
-   **No Mouse Required**: The entire game—from menu navigation to gameplay mechanics—is fully playable using only the keyboard (`WASD`, `Arrows`, `Space`, `Enter`, `1-6`).
-   **Motor Accessibility**: This supports players who may have difficulty using a mouse or precise pointing devices.

## Future Improvements

### 1. Save System
-   **Cloud Save**: We plan to implement cloud save functionality to allow players to save their progress across devices.
-   **Multiplayer**: We plan to implement a multiplayer mode where players can compete against each other in the same world.

### 2. Game World
-   **New Worlds**: We plan to add new worlds to the game, including a new world for each career.
-   **New Challenges**: We plan to add new challenges to the game, including new hazards and tasks.

### 3. Game Mechanics
-   **New Game Mechanics**: We plan to add new game mechanics to the game, including new physics and game mechanics.
-   **New Game Modes**: We plan to add new game modes to the game, including new game modes and game modes.


# Game Rules Documentation
## For Judges & Players

This document provides a comprehensive explanation of all game rules, mechanics, and simulation logic for the Career Worlds game.

---

## 🎮 Universal Game Rules (All Worlds)

### Core Mechanics
1. **Movement**: Use WASD or Arrow Keys to navigate your character
2. **Time Limit**: Each world has a countdown timer displayed in the top-right corner
3. **Win Condition**: Complete the world-specific objective before time runs out
4. **Fail Condition**: Timer reaches 0:00.0 OR world-specific failure condition is met
5. **Abort Mission**: Press ESC at any time to return to the Career Hub
6. **Return to Hub**: After completing a world, press SPACE to return

### Progression System
- **6 Career Worlds**: Each represents a different profession
- **Completion Tracking**: Completed worlds are marked with a green outline in the hub
- **No Penalties**: Failed attempts don't lock you out; you can retry unlimited times
- **Save System**: Progress is automatically saved with HMAC-SHA256 integrity verification

---

## 🔥 World 1: Firefighter Rescue

### Objective
**Save 5 survivors from a burning building before time runs out (48 seconds)**

### Rules
1. **Rescue Mechanic**:
   - Approach trapped survivors (yellow circles with "TRAPPED" label)
   - Stay near them to free them (progress bar fills automatically)
   - Once freed (green circles with "FREE" label), touch them to pick them up
   - Carry them to the red "Crew Door" on the left side of the screen

2. **Hazards**:
   - **Flames (orange/red circles)**: 
     - Roam around the building randomly
     - Contact drains your timer 3x faster
     - Spread to new locations over time (max 12 flames)
     - Build up "heat exposure" meter (shown at bottom-left)
   - **Heat Exposure**: 
     - Accumulates when touching flames
     - At 40+ heat, you're reset to the starting position
     - Heat meter resets after respawn

3. **Smoke (gray puffs)**: 
   - Visual obstruction only, no damage
   - Rises upward with sinusoidal drift pattern

4. **Win Condition**: Successfully evacuate all 5 survivors to the crew door
5. **Fail Condition**: Timer reaches 0 before saving all 5 survivors

### In-Game Instructions
- Bottom-left: "Tip: free trapped survivors by staying near, then carry them to the red door. Flames drain your clock and spread."
- HUD: "Firefighter Rescue | Navigate smoke, dodge flames, and carry survivors out"
- Survivor counter: "Survivors: X/5"

---

## 👨‍🍳 World 2: Chef Rush

### Objective
**Complete a randomized recipe by visiting stations in the correct order (30 seconds)**

### Rules
1. **Recipe System**:
   - One of 3 random recipes is assigned at start:
     - Recipe A: Knife Skills → Sear Protein → Deglaze → Plate
     - Recipe B: Chop Veggies → Simmer Sauce → Season → Plating
     - Recipe C: Prep Dough → Bake → Glaze → Garnish
   - Recipe sequence is displayed at the bottom of the screen
   - Current step is highlighted in brackets: `[Knife Skills]`

2. **Station Mechanic**:
   - 12 stations are scattered around the kitchen (colored circles)
   - Move to the highlighted station and stay on it
   - Progress bar fills while you're on the correct station
   - Progress drains if you leave before completing (slower drain rate)
   - Completing a step adds +3 seconds to your timer

3. **Hazards**:
   - **Spills (blue circles)**: 
     - Move randomly around the kitchen
     - Contact slows your movement speed to 180 (from 240)
     - Drains timer 4x faster while touching
   - **Wrong Stations**: 
     - Touching non-active stations drains timer 1x faster
     - "Wrong Station!" warning appears on screen

4. **Expedite Tickets**:
   - Appear in the "Pass/Expedite" window (top-right blue box)
   - Spawn every 7-11 seconds
   - Each ticket has a 7.5-second countdown
   - Walk to the Pass window to clear tickets (+4 seconds)
   - If a ticket expires, lose 6 seconds

5. **Win Condition**: Complete all recipe steps in order
6. **Fail Condition**: Timer reaches 0 before finishing the recipe

### In-Game Instructions
- Top banner: "Michelin-night prep. Keep the line moving!"
- Bottom: "Hold on the highlighted station to finish prep; clear expedite tickets at the pass; wrong stations and spills drain your clock."
- Recipe tracker shows full sequence with current step highlighted

---

## 💻 World 3: Software Engineer

### Objective
**Patch 5 code nodes in sequence, then deploy to production (50 seconds)**

### Rules
1. **Node Patching**:
   - 5 nodes must be patched in this order: Telemetry → Physics → AI → UI → Netcode
   - Nodes are connected by dashed lines showing the sequence
   - Active node glows brightly and has a white outline
   - Stand on the active node to patch it (progress bar fills)
   - Completing a node adds +2.8 seconds to timer

2. **Hazards**:
   - **Glitches (red squares)**: 
     - Move randomly around the code space
     - Contact resets your position to start (140, 140)
     - Drains timer 6x faster on contact
   - **Memory Leak (expanding blue circle)**: 
     - Located at center of screen
     - Grows from radius 40 to 130 over time
     - Entering the leak slows movement to 180 (from 260)
     - Drains timer 3x faster while inside
   - **Wrong Nodes**: 
     - Touching non-active nodes drains timer 0.5x faster
     - "Wrong Node!" warning appears

3. **Deployment Phase**:
   - After all 5 nodes are patched, a "DEPLOY" console appears at bottom-center
   - Move to the console and hold position to deploy (progress bar fills)
   - Deployment takes ~0.67 seconds of continuous contact

4. **Win Condition**: Successfully deploy the build to production
5. **Fail Condition**: Timer reaches 0 before deployment completes

### In-Game Instructions
- Top: "Late-night sprint. Fix nodes in order before QA wakes up."
- Bottom: "Hold on glowing nodes to patch them in order, dodge glitches, avoid the memory leak pool, then deploy at the console."
- Next bug tracker: "Next bug: [NodeName]"

---

## 🐠 World 4: Marine Biologist

### Objective
**Scan 3 fish species AND collect 3 seabed samples before oxygen runs out (60 seconds)**

### Rules
1. **Oxygen System**:
   - Start with 100% oxygen
   - Drains at 1.5% per second continuously
   - Displayed as blue bar at bottom-left
   - Game over if oxygen reaches 0%

2. **Swimming Physics**:
   - Natural buoyancy: Player floats upward slowly unless pressing Down/S
   - Water resistance: Velocity capped at ±180 units/sec
   - Inertia-based movement (not instant stop)

3. **Fish Scanning**:
   - 8 fish swim around the ocean (5 species: Clownfish, Blue Tang, Sea Turtle, Jellyfish, Manta Ray)
   - Get within 80 units of a fish to target it (white dashed outline appears)
   - Hold SPACE for 1.5 seconds to complete scan
   - Progress bar shows scan progress above player
   - Scanned fish are labeled "SCANNED" in green
   - Must scan at least 3 different fish

4. **Sample Collection**:
   - 3 purple samples rest on the seabed (bottom of screen)
   - Touch a sample to collect it automatically
   - Samples are labeled "SAMPLE" in white

5. **Win Condition**: Collect 3 samples AND scan 3 fish before oxygen depletes
6. **Fail Condition**: Oxygen reaches 0% OR timer reaches 0

### In-Game Instructions
- HUD displays:
  - "OXYGEN: X%" with visual bar
  - "Samples: X/3"
  - "Scans: X/3"
- When near fish: "Hold SPACE to Scan" with progress bar

---

## 🏗️ World 5: Architect

### Objective
**Design a stable Eco-Library building that survives a 10-second wind stress test (90 seconds)**

### Rules - Build Phase

1. **Grid System**:
   - 12×8 grid for building placement
   - Foundation row is pre-placed at the bottom (cannot be removed)
   - Yellow cursor highlights the grid cell under your player

2. **Room Types & Costs**:
   - Press 1: **Lobby** - $10 (Strength: 45, Color: Light Gray)
   - Press 2: **Books** - $15 (Strength: 80, Color: Brown) - Heavy/Strong
   - Press 3: **Eco-Roof** - $20 (Strength: 20, Color: Green) - Fragile but REQUIRED
   - Press 4: **Elevator** - $25 (Strength: 120, Color: Gray) - Strongest

3. **Building Mechanic**:
   - Starting budget: $1,000
   - Select room type (1-4 keys)
   - Move to desired grid cell
   - Press SPACE to place block (if affordable and cell is empty)
   - Cannot overlap blocks

4. **Starting Wind Test**:
   - Press ENTER when ready to test (or automatically starts if budget < $50)
   - Cannot build during test phase

### Rules - Wind Test Phase

1. **Physics Simulation** (10-second test):
   
   **A. Gravity Check (BFS Algorithm)**:
   - All blocks must be connected to the foundation (directly or through other blocks)
   - Breadth-First Search verifies connectivity in 4 directions (up/down/left/right)
   - Floating blocks (not connected to foundation) fall and are removed

   **B. Wind Stress Calculation**:
   - Wind force: Starts at 0, increases over time, with random gusts (0-200 mph)
   - Wind drag formula: `Drag = WindForce × (0.5 + HeightFactor × 1.5)`
   - HeightFactor: Higher blocks experience more wind (0.0 at bottom, 1.0 at top)
   
   **C. Material Strength**:
   - Each block has base strength (Lobby: 45, Books: 80, Eco-Roof: 20, Elevator: 120)
   - Neighbor support bonus: +15 strength per adjacent block (4 directions)
   
   **D. Failure Mechanics**:
   - Stress Ratio = Drag / (Strength + Neighbor Bonus)
   - If ratio > 1.2: Block breaks immediately
   - If ratio > 0.8: 50% chance per second to break
   - If ratio ≤ 0.8: Block survives
   - Each broken block reduces stability by 5%

2. **Win Condition**: 
   - Stability > 0% after 10-second test
   - At least 10 blocks remain standing
   - Building includes at least one Eco-Roof block

3. **Fail Condition**: 
   - Stability ≤ 0% (too many blocks collapsed)
   - Fewer than 10 blocks remain
   - No Eco-Roof in final structure

### In-Game Instructions
- Build phase: "1: Lobby($10)  2: Books($15)  3: Eco-Roof($20)  4: Elevator($25)"
- Build phase: "Selected: [RoomType] - Press SPACE to Build, ENTER to Test"
- Test phase: "WIND TEST: X mph"
- Budget display: "Budget: $X"

---

## 🏥 World 6: Doctor

### Objective
**Correctly diagnose and treat 3 patients without dropping hospital rating to 0% (60 seconds)**

### Rules
1. **Patient System**:
   - 3 random patients are generated at start
   - Each patient has symptoms from this database:
     - "High Fever, Cough" → Diagnosis: Flu → Treatment: Antivirals
     - "Broken Bone, Pain" → Diagnosis: Fracture → Treatment: Cast
     - "Deep Cut, Bleeding" → Diagnosis: Laceration → Treatment: Stitches
     - "Chest Pain, Nausea" → Diagnosis: Heart Attack → Treatment: CPR/Defib

2. **Treatment Selection**:
   - Patient info card shows: Name and Symptoms
   - Press 1-4 to select treatment:
     - 1: Antivirals (for Flu)
     - 2: Cast (for Fracture)
     - 3: Stitches (for Laceration)
     - 4: CPR/Defib (for Heart Attack)
   - Selected treatment is highlighted in yellow
   - Press SPACE to apply treatment

3. **Scoring**:
   - Start with 100% Hospital Rating
   - **Correct Treatment**: Patient cured, move to next patient, feedback: "Correct treatment applied!"
   - **Wrong Treatment**: 
     - Hospital Rating drops by 20%
     - Timer reduced by 5 seconds
     - Feedback: "Wrong treatment! Patient health dropped."
     - Must try again with correct treatment

4. **Win Condition**: Successfully treat all 3 patients with Hospital Rating > 0%
5. **Fail Condition**: Hospital Rating drops to 0% OR timer reaches 0

### In-Game Instructions
- "Hospital Rating: X%"
- "Select Treatment (Press 1-4, then SPACE):"
- Treatment options listed with keys: "1: Antivirals (Flu)", "2: Cast (Fracture)", etc.
- Feedback messages appear after each treatment attempt

---

## 🔐 Technical Rules (For Judges)

### Save System Security
- **Algorithm**: HMAC-SHA256 cryptographic signing
- **Secret Key**: Hardcoded in save_system.py
- **Integrity Check**: On load, payload is re-hashed and compared to stored signature
- **Tamper Detection**: Mismatched signatures result in save file rejection (reset to empty)
- **Purpose**: Prevents save scumming and JSON editing to unlock all careers

### Physics Engine (Architect World)
- **Gravity Simulation**: BFS traversal from foundation nodes to identify connected vs. floating blocks
- **Wind Simulation**: Height-based drag calculation with probabilistic fracture model
- **Material Properties**: Each block type has unique strength values affecting collapse probability
- **Structural Support**: Adjacent blocks provide cumulative strength bonuses

### Collision Detection
- **Method**: Euclidean distance calculation (`math.hypot`)
- **Hitboxes**: Circular for most entities (player, hazards, collectibles)
- **Rectangular**: Used for zones (doors, stations, deploy console)

### Timer Manipulation
- **Base Drain**: 1 second per real-time second
- **Accelerated Drain**: Hazards multiply drain rate (e.g., flames = 3x, glitches = 6x)
- **Time Bonuses**: Completing objectives adds seconds (e.g., +3s for chef stations, +2.8s for code nodes)
- **Clamping**: Timer cannot exceed original duration + bonus cap


---

## 🎯 Accessibility Features

1. **High Contrast Mode**: Press 'H' in main menu for black background with yellow/white text
2. **Full Keyboard Control**: No mouse required (WASD, Arrow Keys, 1-6, Space, Enter, ESC)
3. **Visual Feedback**: All game states have clear visual indicators (progress bars, labels, colors)
4. **Rotating Hints**: Tips cycle every 4 seconds in the HUD
5. **Semi-Transparent HUD Backgrounds**: Ensures text readability on all backgrounds

---

## 📝 Notes for Judges

This game demonstrates:
- **Polymorphic Architecture**: BaseWorld abstract class with 6 concrete implementations
- **Real-time Physics**: Custom gravity and wind simulation in Architect world
- **State Machines**: Each world manages build/test phases, scanning states, etc.
- **Cryptographic Security**: HMAC-SHA256 for save file integrity
- **Responsive UI**: 60 FPS game loop with delta-time calculations
- **Modular Design**: Easy to add new worlds by inheriting from BaseWorld

All rules are enforced programmatically in the `update()` methods of each world class, ensuring consistent and fair gameplay.
