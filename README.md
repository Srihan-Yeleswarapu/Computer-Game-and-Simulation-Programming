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
