import threading
import pygame

from network import LineReader, send_line

# --------------------------------------------------------
#  Connection settings
# --------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8910

sock = None
reader = None
connected = False
messages = []
messages_lock = threading.Lock()

def connect(host, port, player_name):
    global sock, reader, connected
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    reader = LineReader(sock)

    # server immediately asks for a name
    welcome = reader.readline()
    if welcome:
        with messages_lock:
            messages.append(welcome)
    send_line(sock, player_name)
    connected = True

def receive_loop():
    """Background thread: read server messages and append to the list."""
    while connected:
        line = reader.readline()
        if line is None:
            with messages_lock:
                messages.append("Server: disconnected.")
            break
        with messages_lock:
            messages.append(line)

# --------------------------------------------------------
#  Name prompt screen
# --------------------------------------------------------
pygame.init()

window_width, window_height = 1400, 750
info = pygame.display.Info()
scale = min((info.current_w - 50) / window_width, (info.current_h - 100) / window_height)
actual_w = int(window_width * scale)
actual_h = int(window_height * scale)
window = pygame.display.set_mode((actual_w, actual_h), pygame.SCALED)
pygame.display.set_caption("UnderCooked Client")

black           = (0,   0,   0)
white           = (255, 255, 255)
gray            = (180, 180, 180)
red             = (179, 4,   46)
blue            = (15,  4,   179)
green           = (99,  179, 4)
background_color = (79, 163, 194)

font       = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 24)
clock      = pygame.time.Clock()

# name-entry phase
name_text = ""
name_entered = False
connection_error = ""

while not name_entered:
    window.fill(background_color)

    prompt = font.render("Enter your name and press Enter:", True, white)
    window.blit(prompt, (window_width // 2 - prompt.get_width() // 2, 300))

    name_box = pygame.Rect(window_width // 2 - 200, 350, 400, 40)
    pygame.draw.rect(window, white, name_box)
    pygame.draw.rect(window, green, name_box, 3)
    name_surf = font.render(name_text, True, black)
    window.blit(name_surf, (name_box.x + 10, name_box.y + 8))

    if connection_error:
        err_surf = font.render(connection_error, True, red)
        window.blit(err_surf, (window_width // 2 - err_surf.get_width() // 2, 410))

    pygame.display.flip()
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and name_text.strip():
                try:
                    connect(HOST, PORT, name_text.strip())
                    name_entered = True
                    threading.Thread(target=receive_loop, daemon=True).start()
                except OSError as e:
                    connection_error = f"Could not connect: {e}"
            elif event.key == pygame.K_BACKSPACE:
                name_text = name_text[:-1]
            else:
                name_text += event.unicode

# --------------------------------------------------------
#  Load images
# --------------------------------------------------------
frying_pan_idle_img  = pygame.transform.scale(pygame.image.load("images/frying_pan_idle.png"),  (200, 200))
frying_pan_busy_img  = pygame.transform.scale(pygame.image.load("images/frying_pan_busy.png"),  (200, 200))
cutting_board_idle_img = pygame.transform.scale(pygame.image.load("images/cutting_board_idle.png"), (200, 200))
cutting_board_busy_img = pygame.transform.scale(pygame.image.load("images/cutting_board_busy.png"), (200, 200))
toaster_oven_idle_img  = pygame.transform.scale(pygame.image.load("images/toaster_oven_idle.png"),  (200, 200))
toaster_oven_busy_img  = pygame.transform.scale(pygame.image.load("images/toaster_oven_busy.png"),  (200, 200))

meat_crate_img    = pygame.transform.scale(pygame.image.load("images/meat_crate.png"),    (150, 150))
lettuce_crate_img = pygame.transform.scale(pygame.image.load("images/lettuce_crate.png"), (150, 150))
tomato_crate_img  = pygame.transform.scale(pygame.image.load("images/tomato_crate.png"),  (150, 150))
bread_crate_img   = pygame.transform.scale(pygame.image.load("images/bread_crate.png"),   (150, 150))

nothing_img      = pygame.transform.scale(pygame.image.load("images/nothing.png"),      (200, 200))
lettuce_img      = pygame.transform.scale(pygame.image.load("images/lettuce.png"),      (200, 200))
tomato_img       = pygame.transform.scale(pygame.image.load("images/tomato.png"),       (200, 200))
bread_img        = pygame.transform.scale(pygame.image.load("images/bread.png"),        (200, 200))
meat_img         = pygame.transform.scale(pygame.image.load("images/meat.png"),         (200, 200))
cut_lettuce_img  = pygame.transform.scale(pygame.image.load("images/cut_lettuce.png"),  (200, 200))
cut_tomato_img   = pygame.transform.scale(pygame.image.load("images/cut_tomato.png"),   (200, 200))
toasted_bread_img = pygame.transform.scale(pygame.image.load("images/toasted_bread.png"), (200, 200))
cooked_meat_img  = pygame.transform.scale(pygame.image.load("images/cooked_meat.png"),  (200, 200))

bread_one_img    = pygame.transform.scale(pygame.image.load("images/bread_done_1.png"),   (200, 50))
bread_two_img    = pygame.transform.scale(pygame.image.load("images/bread_done_2.png"),   (200, 50))
lettuce_done_img = pygame.transform.scale(pygame.image.load("images/lettuce_done.png"),   (200, 50))
tomato_done_img  = pygame.transform.scale(pygame.image.load("images/tomato_done.png"),    (200, 50))
meat_done_img    = pygame.transform.scale(pygame.image.load("images/meat_done.png"),      (200, 50))

# --------------------------------------------------------
#  Layout rects
# --------------------------------------------------------
server_box    = pygame.Rect(400, 305, 600, 270)
input_box     = pygame.Rect(350, 605, 700, 40)

frying_pan_box    = pygame.Rect(300, 50, 100, 100)
cutting_board_box = pygame.Rect(600, 50, 100, 100)
toaster_oven_box  = pygame.Rect(900, 50, 100, 100)

meat_crate_box    = pygame.Rect(60, 50,  100, 100)
lettuce_crate_box = pygame.Rect(60, 200, 100, 100)
tomato_crate_box  = pygame.Rect(60, 350, 100, 100)
bread_crate_box   = pygame.Rect(60, 500, 100, 100)

ingredient_box    = pygame.Rect(1120, 550, 100, 100)

bread_done_box    = pygame.Rect(1120, 270, 200, 50)
lettuce_done_box  = pygame.Rect(1120, 320, 200, 50)
tomato_done_box   = pygame.Rect(1120, 370, 200, 50)
meat_done_box     = pygame.Rect(1120, 420, 200, 50)
bread_done_box_2  = pygame.Rect(1120, 470, 200, 50)

# --------------------------------------------------------
#  Client-side display state (derived from server messages)
# --------------------------------------------------------
input_text   = ""
input_active = True

# track what the server tells us we're holding / have plated
held_item   = None
bread_done  = False
lettuce_done = False
tomato_done = False
meat_done   = False

# which stations are busy (shown via busy image while server cooks)
frying_pan_busy    = False
cutting_board_busy = False
toaster_oven_busy  = False

ITEM_IMAGES = {
    "Lettuce":      lettuce_img,
    "Tomato":       tomato_img,
    "Bread":        bread_img,
    "Meat":         meat_img,
    "Cooked Meat":  cooked_meat_img,
    "Cut Lettuce":  cut_lettuce_img,
    "Cut Tomato":   cut_tomato_img,
    "Toasted Bread": toasted_bread_img,
}

def update_state_from_message(msg):
    """Update local display state based on server messages."""
    global held_item, bread_done, lettuce_done, tomato_done, meat_done
    global frying_pan_busy, cutting_board_busy, toaster_oven_busy

    low = msg.lower()

    # held item tracking
    if "you grabbed" in low:
        for item in ("Tomato", "Lettuce", "Meat", "Bread"):
            if item.lower() in low:
                held_item = item
    elif "your meat is now cooked meat" in low or "cooked meat" in low and "now" in low:
        held_item = "Cooked Meat"
    elif "your lettuce is now cut lettuce" in low or "cut lettuce" in low and "now" in low:
        held_item = "Cut Lettuce"
    elif "your tomato is now cut tomato" in low or "cut tomato" in low and "now" in low:
        held_item = "Cut Tomato"
    elif "your bread is now toasted bread" in low or "toasted bread" in low and "now" in low:
        held_item = "Toasted Bread"

    # plating
    if "you plated" in low:
        if "bread" in low:
            bread_done = True
            held_item = None
        if "lettuce" in low:
            lettuce_done = True
            held_item = None
        if "tomato" in low:
            tomato_done = True
            held_item = None
        if "meat" in low:
            meat_done = True
            held_item = None

    # dump / drop
    if "you dumped" in low or "you dropped" in low:
        held_item = None

    # station busy indicators
    # set busy on "starting" messages (contain the station name)
    if "frying pan" in low:
        if "starting" in low or "cooking" in low or "busy" in low or "in line" in low:
            frying_pan_busy = True

    if "cutting board" in low:
        if "starting" in low or "cutting" in low or "busy" in low or "in line" in low:
            cutting_board_busy = True

    if "toaster oven" in low:
        if "starting" in low or "toasting" in low or "busy" in low or "in line" in low:
            toaster_oven_busy = True

    # clear busy when the server sends the "is now" completion message
    # (these messages don't mention the station name, so check the item)
    if "is now cooked meat" in low or ("no longer have" in low and "meat" in low):
        frying_pan_busy = False
    if "is now cut lettuce" in low or "is now cut tomato" in low or ("no longer have" in low and ("lettuce" in low or "tomato" in low)):
        cutting_board_busy = False
    if "is now toasted bread" in low or ("no longer have" in low and "bread" in low):
        toaster_oven_busy = False

# --------------------------------------------------------
#  Main game loop
# --------------------------------------------------------
running = True
while running:
    window.fill(background_color)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            input_active = input_box.collidepoint(event.pos)

        elif event.type == pygame.KEYDOWN and input_active:
            if event.key == pygame.K_RETURN:
                text = input_text.strip()
                if text:
                    try:
                        send_line(sock, text)
                    except OSError:
                        with messages_lock:
                            messages.append("Server: connection lost.")
                input_text = ""

            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]

            else:
                input_text += event.unicode

    # pull any new messages and update display state
    with messages_lock:
        new_msgs = messages[:]
    for msg in new_msgs:
        update_state_from_message(msg)

    # ---- server chat box ----
    title = font.render("Kitchen Server", True, white)
    window.blit(title, (400, 275))

    pygame.draw.rect(window, gray,  server_box)
    pygame.draw.rect(window, white, server_box, 3)

    visible = new_msgs[-12:]
    y = server_box.y + 25
    for msg in visible:
        surf = small_font.render(msg, True, black)
        window.blit(surf, (server_box.x + 10, y))
        y += 25

    # ---- input box ----
    input_title = font.render("Your message", True, white)
    window.blit(input_title, (350, 580))

    box_color = green if input_active else gray
    pygame.draw.rect(window, white, input_box)
    pygame.draw.rect(window, box_color, input_box, 4)
    input_surf = font.render(input_text, True, black)
    window.blit(input_surf, (input_box.x + 10, input_box.y + 8))

    # ---- stations ----
    window.blit(frying_pan_busy_img    if frying_pan_busy    else frying_pan_idle_img,    frying_pan_box.topleft)
    window.blit(cutting_board_busy_img if cutting_board_busy else cutting_board_idle_img, cutting_board_box.topleft)
    window.blit(toaster_oven_busy_img  if toaster_oven_busy  else toaster_oven_idle_img,  toaster_oven_box.topleft)

    # ---- food crates ----
    window.blit(meat_crate_img,    meat_crate_box.topleft)
    window.blit(lettuce_crate_img, lettuce_crate_box.topleft)
    window.blit(tomato_crate_img,  tomato_crate_box.topleft)
    window.blit(bread_crate_img,   bread_crate_box.topleft)

    # ---- held ingredient ----
    window.blit(ITEM_IMAGES.get(held_item, nothing_img), ingredient_box.topleft)
    label = font.render("Holding", True, white)
    window.blit(label, (ingredient_box.x, ingredient_box.y - 30))

    # ---- burger plate ----
    if bread_done:
        window.blit(bread_one_img,  bread_done_box.topleft)
        window.blit(bread_two_img,  bread_done_box_2.topleft)
    if lettuce_done:
        window.blit(lettuce_done_img, lettuce_done_box.topleft)
    if tomato_done:
        window.blit(tomato_done_img,  tomato_done_box.topleft)
    if meat_done:
        window.blit(meat_done_img,    meat_done_box.topleft)

    pygame.display.flip()
    clock.tick(60)

if sock:
    try:
        send_line(sock, "QUIT")
        sock.close()
    except OSError:
        pass

pygame.quit()
