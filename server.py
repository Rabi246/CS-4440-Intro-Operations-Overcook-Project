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
players_lock = threading.Lock()    # guards players + winner
winner = None                      # name of the first winner, or None

# One FCFS queue per utility. queue.Queue is thread-safe FIFO.
utility_queues = {
    "Frying Pan":    queue.Queue(),
    "Cutting Board": queue.Queue(),
    "Toaster Oven":  queue.Queue(),
}

next_client_id = 0
next_id_lock = threading.Lock()


# =========================================================
#  Utility worker (one thread per utility)
# ========================================================
def utility_worker(util_name):
    """
    Pulls jobs off the FCFS queue and cooks them one at a time.
    Because there's exactly one worker per utility, only one cook job
    runs at a time per station -- that's our mutex for the station.
    """
    q = utility_queues[util_name]
    while True:
        player, raw_item, prepared_item = q.get()    # blocks (FCFS)
        player["send"](
            f"Server: {util_name} starting on your {raw_item} "
            f"for {COOK_TIME:.0f} seconds..."
        )
        time.sleep(COOK_TIME)

        # update player's held item under their personal lock
        with player["lock"]:
            if player["held"] == raw_item:
                player["held"] = prepared_item
                player["send"](
                    f"Server: Your {raw_item} is now {prepared_item}."
                )
            else:
                player["send"](
                    f"Server: {util_name} finished but you no longer "
                    f"have {raw_item}."
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

    # ---------------- GRAB ----------------
    if verb == "GRAB":
        if rest not in INGREDIENTS:
            player["send"](f"Server: '{rest}' isn't something you can grab.")
            return
        with player["lock"]:
            if player["held"] is not None:
                player["send"](
                    f"Server: You're already holding {player['held']}."
                )
                return
            player["held"] = rest
        player["send"](f"Server: You grabbed {rest}.")
        return

    # ---------------- USE -----------------
    if verb == "USE":
        util = rest
        if util not in utility_queues:
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

        # Enqueue the job. queue.Queue is FIFO -> FCFS comes for free.
        q = utility_queues[util]
        position = q.qsize() + 1
        q.put((player, held, prepared))
        if position == 1:
            player["send"](f"Server: {util} accepted your {held}. Cooking...")
        else:
            player["send"](
                f"Server: {util} is busy. You're #{position} in line."
            )
        return

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
        f"Server: I don't understand '{text}'. Try GRAB / USE / PLATE."
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
    }
    with players_lock:
        players[cid] = player

    send(f"Server: Hi {name}! Commands: GRAB <ingredient>, "
         f"USE <utility>, PLATE <item>.")
    print(f"[server] {addr} connected as {name} (id={cid})")

    # Main read loop: one command per line.
    while not player["quit"]:
        line = reader.readline()
        if line is None:
            break
        handle_command(player, line)

    # Cleanup
    with players_lock:
        players.pop(cid, None)
    try:
        sock.close()
    except OSError:
        pass
    print(f"[server] {addr} disconnected ({name})")


# ========================================================
#  Main
# =========================================================
def main(host=HOST, port=PORT):
    # Start one worker thread for each utility.
    for util_name in utility_queues:
        threading.Thread(
            target=utility_worker,
            args=(util_name,),
            name=f"{util_name}-worker",
            daemon=True,
        ).start()

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
