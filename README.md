# Career Worlds: Career Quest (2025-2026)

**Career Worlds** is a comprehensive arcade-style career simulation built for the **FBLA 2025-2026 Computer Game & Simulation Programming** event. Following the **"Career Quest"** topic, players explore a "hub" of 17 distinct mini-worlds, each simulating the skill-based challenges of a specific profession.

---

## 🚀 How to Run
1.  **Requirement**: Python 3.12+ (includes `tkinter` on standard Windows installs).
2.  **Music Support**: Ensure `pygame` is installed if you want background music.
3.  **Command**: From this folder, run:
    ```bash
    python main.py
    ```

---

## 🎮 The Hub (Main Menu)
-   **Navigate**: Use **Arrow Keys** or hover your mouse over career cards.
-   **Launch**: Press **Enter** or **Space** to enter a profession's briefing.
-   **Shortcuts**: Keys **1-0** and **Q-U** instantly launch worlds.
-   **Progress**: Your best grade (S, A, B, C) is saved per career.
-   **Victory**: Clear every profession with a **B-Rank** or higher to reach the final tour completion screen.

---

## 🏛️ Comprehensive Career Manifest (17 Worlds)

| Key | Career | Skill-Based Challenge |
|---|---|---|
| **1** | **Fire Rescue** | Saving survivors while managing heat exposure and spreading flames. |
| **2** | **Chef Rush** | Multi-tasking a complex recipe sequence while clearing service tickets. |
| **3** | **QA Engineer** | Identifying and squashing priority bugs in a failing build. |
| **4** | **Marine Biologist**| Scientific data collection (scanning/sampling) under oxygen constraints. |
| **5** | **Architect** | Structural engineering using custom BFS gravity and wind-stress physics. |
| **6** | **Doctor** | Clinical diagnostics and triage based on patient symptoms. |
| **7** | **ATC (Air Traffic)**| Approach coordination and standard separation avoidance (collision logic). |
| **8** | **Pilot** | Flight navigation and waypoint tracking. |
| **9** | **Fullstack Dev** | Managing the full ALM lifecycle (Triage -> Code -> Review -> Deploy). |
| **0** | **Psychologist** | De-escalating unit-wide distress using targeted therapeutic interventions. |
| **Q** | **Startup Founder**| Economic simulation (balancing equity, runway, and growth deals). |
| **W** | **Electrician** | Circuit maintenance and power grid stabilization. |
| **E** | **Game Developer** | High-pressure release management with abilities (Dash, Coffee, Patch). |
| **R** | **Data Scientist** | Trend analysis and anomaly detection in data streams. |
| **T** | **AI Engineer** | Training neural nodes and managing iterative drift. |
| **Y** | **Sec Analyst** | Defending infrastructure against simulated port-scan attacks. |
| **U** | **Robotics Eng** | Precision control of robotic actuators to assemble components. |

---

## 📄 Technical Report & Rationale (For Judges)

### 1. Topic Adherence: "Career Quest"
We strictly followed the FBLA 2025-2026 topic developed with Code.org. Players "jump into mini-worlds" that include a **Scenario Briefing** (job description) and **Skill-Based Tasks** unique to that profession. By the end of the 17-career tour, players understand the core competencies and pressures of each role.

### 2. Architecture: Polymorphic Scalability
To handle 17 different games in one engine, we implemented a **Modular BaseWorld System**:
-   **`BaseWorld` Abstract Class**: Defines handles for `reset`, `update`, `draw`, and `tick`. This allows the `GameEngine` to treat a complex physics architect simulation exactly the same as a simple navigation task.
-   **Inheritance**: Adding a new career requires zero changes to the core game loop; new worlds simply inherit and override specific logic.

### 3. Graphics: Procedural Vector Art
To maximize portability and performance, we used **Native `tkinter.Canvas` Primitives** (arcs, polygons, ovals):
-   **Rationale**: Eliminates external dependencies (no PIL/Image files needed).
-   **Visual Excellence**: Includes heat-shimmer effects in Fire Rescue, sinusoidal bubble drift in Marine Biology, and dynamic EKG animations in Doctor.
-   **60 FPS Performance**: Vector primitives are lightweight, ensuring a consistent framerate even on low-end school computers.

### 4. Technical Complexity Highlights
-   **Structural Physics (Architect)**: Uses a custom **Breadth-First Search (BFS)** algorithm to detect "floating" blocks. If a block is disconnected from the foundation, gravity is applied.
-   **Collision Logic (ATC)**: Implements Euclidean distance calculations for circular hitboxes and OBB-style checks for runway landing zones.
-   **System Integrity (Save System)**: Progress is signed using **HMAC-SHA256**. If a user manually edits the JSON save file, the signature mismatch is detected, and the file is reset to prevent cheating.

---

## ♿ Accessibility & UX Design

### 1. User Journey
-   **Zero-Friction Re-entry**: Players can hit `Esc` to abort and `Space` to return. The "Hub" remains active in memory for instant transitions between careers.
-   **Clear Instructions**: Every world begins with a **Briefing Panel** explaining the *Scenario*, *Rules*, and *Keys*.

### 2. High Contrast Mode
Press **'H'** in the Hub to toggle **WCAG-compliant High Contrast**. This swaps gradients for absolute black backgrounds and applies high-visibility yellow/white text and thick outlines.

### 3. Comprehensive Visibility
We implemented **Semi-Transparent HUD Backdrops** behind all game text. This ensures HUD elements (timer, score) remain 100% readable regardless of background colors (e.g., white clouds or bright ocean floor).

### 4. About/Rationale Screen
Press **'A'** in the Hub to access the **In-Game Technical Report**, explicitly highlighting design rationale and accessibility features for easier judging.

---

## 📜 Game Rules Documentation (Key Worlds)

### 🔥 World 1: Firefighter Rescue
-   **Objective**: Rescue 5 survivors (free them by staying near, then carry to the red door).
-   **Hazard**: Flames drain the timer 3x faster and spread randomly. High heat resets your position.

### 👨‍🍳 World 2: Chef Rush
-   **Objective**: Complete a 4-step recipe at highlighted stations.
-   **Mechanic**: Progress bars fill while on-station; clearing "Expedite Tickets" at the pass window adds time.

### 🏗️ World 5: Architect
-   **Objective**: Build an Eco-Library on a budget ($1,000) that survives a 10s wind test.
-   **Rules**: Must include an Eco-Roof. Wind drag increases with height. BFS validates structural connection to ground.

### 🧠 World 0: Psychologist
-   **Objective**: Stabilize 4 patients using Grounding (1), Breathing (2), Reflection (3), or Reframing (4).
-   **Logic**: Match the intervention to the patient's "Cue words". Mismatched interventions spike distress and fail the session.

---

## 📝 Notes for Judges
-   **110/110 Goal**: This project intentionally targets every point on the Rating Sheet.
-   **Implementation**: No external libraries/engines were used (Pure Python Standard Library).
-   **Originality**: Every mechanic, from the wind-drag simulation to the ALM ticket flow, was custom built for this event.

*Developed by Srihan Yeleswarapu | 2025-2026 Competitive Event Entry*
