"""
server.py
=========

UnderCooked kitchen server -- simplified procedural version.

OS concepts demonstrated:
  - Sockets (TCP)        : one listening socket + one socket per client
  - Multithreading       : one thread per client + one thread per utility
  - Mutex (lock)         : one per player, plus a global winner lock
  - FCFS scheduling      : queue.Queue is FIFO. One worker thread per
                           utility processes jobs in arrival order.

Run with:  python server.py
"""

import queue
import socket
import threading
import time

from network import LineReader, send_line, make_server_socket


# =======================================================
#  Game rules
# ========================================================
HOST = "0.0.0.0"
PORT = 8910
COOK_TIME = 5.0    # seconds for any utility to finish a job

INGREDIENTS = {"Tomato", "Lettuce", "Meat", "Bread"}
RECIPE = {"Cooked Meat", "Cut Lettuce", "Cut Tomato", "Toasted Bread"}

# (utility name, raw item) -> prepared item
TRANSFORMS = {
    ("Frying Pan",    "Meat"):    "Cooked Meat",
    ("Cutting Board", "Lettuce"): "Cut Lettuce",
    ("Cutting Board", "Tomato"):  "Cut Tomato",
    ("Toaster Oven",  "Bread"):   "Toasted Bread",
}


# ========================================================
#  Shared state (protected by locks)
# =========================================================
players = {}                       # client_id -> player dict
players_lock = threading.Lock()    # guards players + winner + game_phase
winner = None                      # name of the first winner, or None
game_phase = "lobby"               # "lobby" or "playing"

# --- FCFS queues (commented out — replaced by mutex approach below) ---
# One FCFS queue per utility. queue.Queue is thread-safe FIFO.
# utility_queues = {
#     "Frying Pan":    queue.Queue(),
#     "Cutting Board": queue.Queue(),
#     "Toaster Oven":  queue.Queue(),
# }

# --- Mutex approach: each station has an occupied_by field ---
# Only one player can use a station at a time. Others are rejected.
station_lock = threading.Lock()    # guards station_occupied + waiting_for
station_occupied = {
    "Frying Pan":    None,         # player name or None
    "Cutting Board": None,
    "Toaster Oven":  None,
}
# Track which player is waiting for which station (for deadlock detection)
# player_name -> station_name they want, or None
waiting_for = {}                   # populated when player types WAIT

next_client_id = 0
next_id_lock = threading.Lock()


# =========================================================
#  Lobby helpers
# =========================================================
def broadcast_all(text):
    """Send a message to every connected player."""
    with players_lock:
        for p in players.values():
            p["send"](text)


def broadcast_lobby_status():
    """Tell all players who is connected and who is ready."""
    with players_lock:
        lines = []
        for p in players.values():
            status = "READY" if p.get("ready") else "waiting"
            lines.append(f"  {p['name']} [{status}]")
        count = len(players)
    msg = f"Server: Lobby ({count} player(s)):\n" + "\n".join(lines)
    broadcast_all(msg)


def try_start_game():
    """If all players are ready and there are at least 2, start the game."""
    global game_phase
    with players_lock:
        if game_phase != "lobby":
            return
        if len(players) < 2:
            return
        if not all(p.get("ready") for p in players.values()):
            return
        game_phase = "playing"
    broadcast_all("Server: All players ready! The game has started!")
    broadcast_all(
        "Server: Commands: GRAB <ingredient>, USE <utility>, "
        "PLATE <item>, QUIT."
    )


# =========================================================
#  Utility worker (one thread per utility)
# ========================================================
# --- FCFS utility worker (commented out — replaced by mutex timer below) ---
# def utility_worker(util_name):
#     """
#     Pulls jobs off the FCFS queue and cooks them one at a time.
#     Because there's exactly one worker per utility, only one cook job
#     runs at a time per station -- that's our mutex for the station.
#     """
#     q = utility_queues[util_name]
#     while True:
#         player, raw_item, prepared_item = q.get()    # blocks (FCFS)
#         player["send"](
#             f"Server: {util_name} starting on your {raw_item} "
#             f"for {COOK_TIME:.0f} seconds..."
#         )
#         time.sleep(COOK_TIME)
#
#         # update player's held item under their personal lock
#         with player["lock"]:
#             if player["held"] == raw_item:
#                 player["held"] = prepared_item
#                 player["send"](
#                     f"Server: Your {raw_item} is now {prepared_item}."
#                 )
#             else:
#                 player["send"](
#                     f"Server: {util_name} finished but you no longer "
#                     f"have {raw_item}."
#                 )


# --- Mutex cook timer callback ---
# When cooking finishes, transform the ingredient but KEEP the station occupied.
# Player must type LEAVE or WAIT to proceed (enables hold-and-wait for deadlock).
def cook_done_callback(player, util_name, raw_item, prepared_item):
    """Timer callback: transform ingredient, keep station held."""
    with player["lock"]:
        if player["held"] == raw_item:
            player["held"] = prepared_item
            player["state"] = "cooking_done"
            player["occupied_station"] = util_name
            player["send"](
                f"Server: Your {raw_item} is now {prepared_item}.\n"
                f"Server: You're still on {util_name}. Type LEAVE to take "
                f"your item, or WAIT <station> to hold and wait."
            )
        else:
            player["state"] = "idle"
            player["send"](
                f"Server: {util_name} finished but you no longer have {raw_item}."
            )
            # Release station since cooking failed
            with station_lock:
                station_occupied[util_name] = None


# =========================================================
#  Deadlock detection (wait-for graph cycle check)
# =========================================================
def check_deadlock():
    """Check for circular waits among players. Broadcast alert if found."""
    with station_lock:
        # Build wait-for graph: who waits for whom?
        # Player A waits for Player B if A typed WAIT for a station held by B.
        graph = {}  # player_name -> player_name they wait for
        for waiter_name, target_station in waiting_for.items():
            holder = station_occupied.get(target_station)
            if holder and holder != waiter_name:
                graph[waiter_name] = holder

    # DFS cycle detection
    visited = set()
    for start in graph:
        path = []
        node = start
        seen_in_path = set()
        while node and node not in visited:
            if node in seen_in_path:
                # Found a cycle — extract it
                cycle_start = path.index(node)
                cycle = path[cycle_start:]
                _broadcast_deadlock(cycle)
                return
            seen_in_path.add(node)
            path.append(node)
            node = graph.get(node)
        visited.update(seen_in_path)


def _broadcast_deadlock(cycle):
    """Send deadlock alert to all players."""
    lines = ["Server: *** DEADLOCK DETECTED ***"]
    with station_lock:
        for name in cycle:
            held = None
            for stn, occ in station_occupied.items():
                if occ == name:
                    held = stn
                    break
            wants = waiting_for.get(name, "?")
            lines.append(f"  {name} holds {held}, waiting for {wants}")
    lines.append("Server: Someone must type LEAVE to break the deadlock!")
    broadcast_all("\n".join(lines))


def notify_waiters(freed_station):
    """If anyone was waiting for this station, tell them it's free."""
    with station_lock:
        to_notify = [
            name for name, target in waiting_for.items()
            if target == freed_station
        ]
    for name in to_notify:
        with players_lock:
            for p in players.values():
                if p["name"] == name:
                    p["send"](
                        f"Server: {freed_station} is now free! "
                        f"Type LEAVE to go use it."
                    )


# =========================================================
#  Command dispatch  (called by each client thread per input line)
# =========================================================
def handle_command(player, line):
    global winner
    text = line.strip()
    if not text:
        return

    parts = text.split(maxsplit=1)
    verb = parts[0].upper()
    rest = (
        " ".join(w.capitalize() for w in parts[1].split())
        if len(parts) > 1 else ""
    )

    # ---------------- READY (lobby only) ----------------
    if verb == "READY":
        with players_lock:
            if game_phase != "lobby":
                player["send"]("Server: Game already started.")
                return
            if player.get("ready"):
                player["send"]("Server: You're already ready.")
                return
            player["ready"] = True
        player["send"]("Server: You are ready!")
        broadcast_lobby_status()
        try_start_game()
        return

    # ---------------- Gate: game commands need "playing" phase ----
    if verb in ("GRAB", "USE", "PLATE", "LEAVE", "WAIT", "DUMP"):
        with players_lock:
            if game_phase != "playing":
                player["send"](
                    "Server: Game hasn't started yet. Type READY first."
                )
                return

    # ---------------- Gate: block commands while cooking ----
    if verb in ("GRAB", "USE", "PLATE", "DUMP"):
        with player["lock"]:
            if player["state"] == "cooking":
                player["send"]("Server: You're busy cooking. Please wait.")
                return
            if player["state"] in ("cooking_done", "waiting_for"):
                player["send"](
                    "Server: You're still at a station. Type LEAVE or WAIT first."
                )
                return

    # ---------------- LEAVE (release station after cooking) --------
    if verb == "LEAVE":
        with player["lock"]:
            state = player["state"]
            stn = player["occupied_station"]
        if state not in ("cooking_done", "waiting_for"):
            player["send"]("Server: You're not at a station to leave.")
            return
        # Release station and go idle
        with station_lock:
            station_occupied[stn] = None
            waiting_for.pop(player["name"], None)
        with player["lock"]:
            player["state"] = "idle"
            player["occupied_station"] = None
        player["send"](f"Server: You left {stn}.")
        # Notify anyone waiting for this station
        notify_waiters(stn)
        # Re-check deadlock (leaving may break a cycle)
        check_deadlock()
        return

    # ---------------- WAIT <station> (hold-and-wait) ---------------
    if verb == "WAIT":
        target = rest
        if target not in station_occupied:
            player["send"](f"Server: There's no '{target}' in this kitchen.")
            return
        with player["lock"]:
            if player["state"] != "cooking_done":
                player["send"](
                    "Server: You can only WAIT after cooking is done."
                )
                return
        # Check target is actually occupied by someone else
        with station_lock:
            if station_occupied[target] is None:
                player["send"](
                    f"Server: {target} is free! Type LEAVE to go use it."
                )
                return
            if station_occupied[target] == player["name"]:
                player["send"]("Server: You're already on that station.")
                return
            # Record the wait (hold-and-wait condition)
            waiting_for[player["name"]] = target
        with player["lock"]:
            player["state"] = "waiting_for"
        player["send"](
            f"Server: You're holding {player['occupied_station']} "
            f"and waiting for {target}."
        )
        # Check for deadlock after entering wait state
        check_deadlock()
        return

    # ---------------- GRAB ----------------
    if verb == "GRAB":
        if rest not in INGREDIENTS:
            player["send"](f"Server: '{rest}' isn't something you can grab.")
            return
        with player["lock"]:
            if player["held"] is not None:
                held = player["held"]
                # Suggest PLATE if holding a cooked item, DUMP otherwise
                if held in RECIPE:
                    player["send"](
                        f"Server: You're holding {held}. "
                        f"PLATE {held} to add it to your burger, or DUMP it."
                    )
                else:
                    player["send"](
                        f"Server: You're already holding {held}. "
                        f"DUMP it first to grab something else."
                    )
                return
            player["held"] = rest
        player["send"](f"Server: You grabbed {rest}.")
        return

    # ---------------- DUMP (drop held item) ----------------
    if verb == "DUMP":
        with player["lock"]:
            if player["held"] is None:
                player["send"]("Server: You're not holding anything.")
                return
            dropped = player["held"]
            player["held"] = None
        player["send"](f"Server: You dumped {dropped}.")
        return

    # ---------------- USE (mutex approach) -----------------
    if verb == "USE":
        util = rest
        if util not in station_occupied:
            player["send"](f"Server: There's no '{util}' in this kitchen.")
            return
        with player["lock"]:
            held = player["held"]
            if held is None:
                player["send"](
                    f"Server: You need an ingredient before using {util}."
                )
                return
            key = (util, held)
            if key not in TRANSFORMS:
                player["send"](f"Server: You can't use {util} on {held}.")
                return
            prepared = TRANSFORMS[key]

        # Mutex check: reject if station is occupied
        with station_lock:
            if station_occupied[util] is not None:
                # Suggest PLATE if holding a cooked item
                if held in RECIPE:
                    player["send"](
                        f"Server: {util} is occupied by {station_occupied[util]}. "
                        f"You can PLATE {held} to add it to your burger, "
                        f"or keep trying USE {util} when it frees up."
                    )
                else:
                    player["send"](
                        f"Server: {util} is occupied by {station_occupied[util]}. "
                        f"Keep trying USE {util} to grab it when it frees up, "
                        f"or DUMP your {held} to switch ingredients."
                    )
                return
            station_occupied[util] = player["name"]

        player["send"](
            f"Server: {util} starting on your {held} "
            f"for {COOK_TIME:.0f} seconds..."
        )
        # Set player state to cooking (locked at station)
        with player["lock"]:
            player["state"] = "cooking"
            player["occupied_station"] = util
        # Timer keeps station held when cooking finishes
        t = threading.Timer(
            COOK_TIME, cook_done_callback,
            args=(player, util, held, prepared),
        )
        t.daemon = True
        t.start()
        return

        # --- FCFS USE handler (commented out) ---
        # q = utility_queues[util]
        # position = q.qsize() + 1
        # q.put((player, held, prepared))
        # if position == 1:
        #     player["send"](f"Server: {util} accepted your {held}. Cooking...")
        # else:
        #     player["send"](
        #         f"Server: {util} is busy. You're #{position} in line."
        #     )
        # return

    # ---------------- PLATE ---------------
    if verb == "PLATE":
        item = rest
        with player["lock"]:
            if player["held"] != item:
                player["send"](f"Server: You're not holding {item}.")
                return
            if item not in RECIPE:
                player["send"](f"Server: {item} isn't part of a hamburger.")
                return
            if item in player["plate"]:
                player["send"](f"Server: You already plated {item}.")
                return
            player["plate"].add(item)
            player["held"] = None
            done = player["plate"] >= RECIPE

        # Win check is its own critical section.
        with players_lock:
            if winner is None and done:
                winner = player["name"]
                player["send"](
                    f"Server: You plated {item}. *** YOU WIN! ***"
                )
                # tell the other players the game is over
                for p in players.values():
                    if p is player:
                        continue
                    p["send"](
                        f"Server: Game over! {player['name']} built "
                        f"the burger first."
                    )
                return
        player["send"](
            f"Server: You plated {item} "
            f"({len(player['plate'])}/4 burger pieces)."
        )
        return

    # ---------------- QUIT ----------------
    if verb == "QUIT":
        player["send"]("Server: Goodbye.")
        player["quit"] = True
        return

    # ---------------- unknown -------------
    player["send"](
        f"Server: I don't understand '{text}'. "
        f"Try READY / GRAB / DUMP / USE / PLATE / LEAVE / WAIT / QUIT."
    )


# =======================================================
#  Per-client connection handler  (one thread per UI.py)
# ========================================================
def handle_client(sock, addr):
    global next_client_id
    with next_id_lock:
        next_client_id += 1
        cid = next_client_id

    # A lock so the worker thread and the client thread never write
    # to the same socket at the same time.
    send_lock = threading.Lock()
    def send(text):
        try:
            send_line(sock, text, lock=send_lock)
        except OSError:
            pass

    reader = LineReader(sock)

    send("Server: Welcome to UnderCooked! What's your name?")
    name_line = reader.readline()
    name = (name_line or "").strip() or f"Player{cid}"

    player = {
        "id": cid,
        "name": name,
        "held": None,
        "plate": set(),
        "send": send,
        "lock": threading.Lock(),
        "quit": False,
        "ready": False,
        "state": "idle",              # idle, cooking, cooking_done, waiting_for
        "occupied_station": None,     # station name while cooking/waiting
    }
    with players_lock:
        players[cid] = player

    send(f"Server: Hi {name}! You're in the lobby. Type READY when you're set.")
    print(f"[server] {addr} connected as {name} (id={cid})")
    broadcast_lobby_status()

    # Main read loop: one command per line.
    while not player["quit"]:
        line = reader.readline()
        if line is None:
            break
        handle_command(player, line)

    # Cleanup
    with station_lock:
        # Release any station this player held
        for stn in station_occupied:
            if station_occupied[stn] == name:
                station_occupied[stn] = None
        waiting_for.pop(name, None)
    with players_lock:
        players.pop(cid, None)
        # Reset to lobby if no players remain (allows new game)
        if not players:
            global game_phase, winner
            game_phase = "lobby"
            winner = None
    try:
        sock.close()
    except OSError:
        pass
    print(f"[server] {addr} disconnected ({name})")
    # Let remaining players know someone left
    if game_phase == "lobby":
        broadcast_lobby_status()


# ========================================================
#  Main
# =========================================================
def main(host=HOST, port=PORT):
    # --- FCFS worker threads (commented out — using mutex timers instead) ---
    # for util_name in utility_queues:
    #     threading.Thread(
    #         target=utility_worker,
    #         args=(util_name,),
    #         name=f"{util_name}-worker",
    #         daemon=True,
    #     ).start()

    # Listen for clients.
    listener = make_server_socket(host=host, port=port)
    print(f"[server] UnderCooked listening on {host}:{port}")

    try:
        while True:
            client_sock, addr = listener.accept()
            threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                name=f"client-{addr}",
                daemon=True,
            ).start()
    except KeyboardInterrupt:
        print("\n[server] shutting down")
    finally:
        listener.close()


if __name__ == "__main__":
    main()
