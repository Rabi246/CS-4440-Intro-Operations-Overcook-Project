# UnderCooked

**A multiplayer cooking game that demonstrates core operating systems concepts.** Players connect to a shared kitchen server, grab ingredients, and race to build a hamburger, competing for the same cooking stations. Every station is a shared resource, so players run into real concurrency problems: mutual exclusion, hold-and-wait, and deadlock.

Built as a team project for **CS 4440 (Introduction to Operating Systems)** at Cal State LA, Spring 2026.

This is my copy of the team repository. The original is at [dylanleon35/CS-4440-Intro-Operations-Overcook-Project](https://github.com/dylanleon35/CS-4440-Intro-Operations-Overcook-Project).

<!-- Add a screenshot or GIF of the game here -->

---

## How to Play

1. Every player joins the lobby and types `READY`. The game starts when everyone is ready.
2. Grab raw ingredients from the crates: **Meat, Lettuce, Tomato, Bread**
3. Take each one to the right station to prepare it:

| Station | Input | Output |
|---|---|---|
| Frying Pan | Meat | Cooked Meat |
| Cutting Board | Lettuce / Tomato | Cut Lettuce / Cut Tomato |
| Toaster Oven | Bread | Toasted Bread |

4. Plate all four prepared items. The first player to complete a burger wins!

### Commands

| Command | What it does |
|---|---|
| `READY` | Mark yourself ready in the lobby |
| `GRAB <item>` | Pick up a raw ingredient |
| `USE <station>` | Lock a station and start cooking (5 seconds) |
| `LEAVE` | Release the station you're holding |
| `WAIT <station>` | Keep your station and wait for another one (hold-and-wait) |
| `PLATE <item>` | Add a prepared item to your burger |
| `DUMP` | Throw away what you're holding |
| `QUIT` | Leave the game |

## Operating Systems Concepts

| Concept | How it shows up in the game |
|---|---|
| **TCP sockets** | A central server with one socket per connected player |
| **Multithreading** | The server runs one thread per client; clients use a background thread to receive messages while the UI keeps running |
| **Mutual exclusion** | Each cooking station is protected by a lock, so only one player can use it at a time |
| **Hold-and-wait** | After cooking, a player can keep their station while waiting for another one |
| **Deadlock detection** | The server builds a wait-for graph and checks for cycles. When players are stuck waiting on each other, it broadcasts a deadlock alert until someone releases a station |
| **FCFS scheduling** | An earlier version queued cooking jobs first-come, first-served (still in the code, commented out, for comparison) |

## Tech Stack

- **Python 3**
- **pygame** for the client UI
- **socket** and **threading** from the Python standard library

## Project Structure

```
├── server.py         # Game server: lobby, game rules, station locks, deadlock detection
├── client_UI.py      # Networked pygame client (the game window players use)
├── network.py        # Shared helpers for sending and reading lines over sockets
├── UI.py             # Original standalone UI prototype
├── images/           # Sprites for stations, crates, and ingredients
└── program examples/ # Simple socket client/server examples
```

## Running Locally

**Requirements:** Python 3.10+ and pygame

1. Clone the repo and install pygame
   ```bash
   git clone https://github.com/Rabi246/CS-4440-Intro-Operations-Overcook-Project.git
   cd CS-4440-Intro-Operations-Overcook-Project
   python -m pip install pygame
   ```
2. Start the server
   ```bash
   python server.py
   ```
3. In a new terminal for each player, start a client
   ```bash
   python client_UI.py
   ```
4. Enter a name, type `READY`, and start cooking!

The server listens on port `8910`. Clients connect to `127.0.0.1` by default, so to play across computers, change `HOST` in `client_UI.py` to the server's IP address.

## Team

- [@dylanleon35](https://github.com/dylanleon35)
- [@DanielMS-AI](https://github.com/DanielMS-AI)
- [@Rabi246](https://github.com/Rabi246) (Samantha Vazquez): built the networked game client (`client_UI.py`), the socket client/server examples, station release, plating, and the game-over screen
- Nguyen
