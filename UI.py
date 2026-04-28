import pygame


pygame.init()

#Set the window size here feel free to change the size. 
window_width, window_height = 1400, 750
window = pygame.display.set_mode((window_width,window_height), 0, 32)
pygame.display.set_caption("UnderCooked UI")

#setting up some small UI features like colors and font
black = (0,0,0)
white = (255,255,255)
gray = (180,180,180)
red = (179,4,46)
blue = (15, 4, 179)
green = (99,179,4)
background_color = (79, 163, 194)
font = pygame.font.Font(None,32)
small_font = pygame.font.Font(None, 24)


#    ----   this will be the text box displaying the server info      ----
server_box = pygame.Rect(400, 300, 600, 350)
messages = [
    "Server: welcome to undercooked",
        "Try typing commands like 'grab tomato' or 'use frying pan'."
        ]

#     ----       this will be where the user inputs text.      ----
input_box = pygame.Rect(350, 690, 700, 50)
input_active = True 
input_text = ""

#      ----      this section will be for the items            ----

frying_pan_box = pygame.Rect(100, 50, 100, 100)
frying_pan_in_use = False
frying_start_time = 0
frying_pan_cook_time = 5000

frying_pan_idle_img = pygame.image.load("images/frying_pan_idle.png")
frying_pan_idle_img = pygame.transform.scale(frying_pan_idle_img, (200, 200))
frying_pan_busy_img = pygame.image.load("images/frying_pan_busy.png")
frying_pan_busy_img = pygame.transform.scale(frying_pan_busy_img, (200, 200))

cutting_board_box = pygame.Rect(400, 50, 100, 100)
cutting_board_in_use = False
cutting_start_time = 0
cutting_use_time = 5000

cutting_board_idle_img = pygame.image.load("images/cutting_board_idle.png")
cutting_board_idle_img = pygame.transform.scale(cutting_board_idle_img, (200, 200))
cutting_board_busy_img = pygame.image.load("images/cutting_board_busy.png")
cutting_board_busy_img = pygame.transform.scale(cutting_board_busy_img, (200, 200))

toaster_oven_box = pygame.Rect(700,50, 100, 100)
toaster_oven_in_use = False
toasting_start_time = 0
toasting_cook_time = 5000

toaster_oven_idle_img = pygame.image.load("images/toaster_oven_idle.png")
toaster_oven_idle_img = pygame.transform.scale(toaster_oven_idle_img, (200, 200))
toaster_oven_busy_img = pygame.image.load("images/toaster_oven_busy.png")
toaster_oven_busy_img = pygame.transform.scale(toaster_oven_busy_img, (200, 200))

#      ----      this section is for the Ingredients           ----

ingredient_box = pygame.Rect(1120, 500, 100, 100)
held_item = None


nothing_img = pygame.image.load("images/nothing.png")
nothing_img = pygame.transform.scale(nothing_img, (200,200))

lettuce_img = pygame.image.load("images/lettuce.png")
lettuce_img = pygame.transform.scale(lettuce_img,(200,200))

tomato_img = pygame.image.load("images/tomato.png")
tomato_img = pygame.transform.scale(tomato_img, (200,200))

bread_img = pygame.image.load("images/bread.png")
bread_img = pygame.transform.scale(bread_img, (200,200))

meat_img = pygame.image.load("images/meat.png")
meat_img = pygame.transform.scale(meat_img, (200,200))

cut_lettuce_img = pygame.image.load("images/cut_lettuce.png")
cut_lettuce_img = pygame.transform.scale(cut_lettuce_img, (200,200))

cut_tomato_img = pygame.image.load("images/cut_tomato.png")
cut_tomato_img = pygame.transform.scale(cut_tomato_img, (200,200))

toasted_bread_img = pygame.image.load("images/toasted_bread.png")
toasted_bread_img = pygame.transform.scale(toasted_bread_img,(200,200))

cooked_meat_img = pygame.image.load("images/cooked_meat.png")
cooked_meat_img = pygame.transform.scale(cooked_meat_img, (200,200))


#we need this for frame rate.
clock = pygame.time.Clock()
FPS = 30

running = True
while running:
    window.fill(background_color)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            input_active = input_box.collidepoint(event.pos)

        elif event.type == pygame.KEYDOWN and input_active:
            if event.key == pygame.K_RETURN:#user hits enter

                #below is placeholder for server functions.  just for testing            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                #this really should be implemented in the server, we should only send info, 
                if input_text.strip().upper() == "USE FRYING PAN" :
                    if frying_pan_in_use == False and held_item == "Meat":
                        frying_pan_in_use = True
                        frying_start_time = pygame.time.get_ticks()
                        messages.append("Server: Cooking Meat for 5 seconds...")
                        input_text = ""
                    elif frying_pan_in_use:
                        messages.append("Server: Frying Pan is in use...")
                        input_text = ""
                    else:
                        messages.append("Server: You need meat to use the frying pan...")
                        input_text = ""

                elif input_text.strip().upper() == "USE CUTTING BOARD":
                    if cutting_board_in_use == False and held_item == "Lettuce":
                        cutting_board_in_use = True
                        cutting_start_time = pygame.time.get_ticks()
                        messages.append("Server: Cutting Lettuce for 5 seconds...")
                        input_text = ""
                    elif cutting_board_in_use == False and held_item == "Tomato":
                        cutting_board_in_use = True
                        cutting_start_time = pygame.time.get_ticks()
                        messages.append("Server: Cutting Tomato for 5 seconds...")
                        input_text = ""
                    elif cutting_board_in_use:
                        messages.append("Server: Cutting Board is in use...")
                        input_text = ""
                    else:
                        messages.append("Server: You need a veggie to use the Cutting Board...")
                        input_text = ""
                
                elif input_text.strip().upper() == "USE TOASTER OVEN" :
                    if toaster_oven_in_use == False and held_item == "Bread":
                        toaster_oven_in_use = True
                        toasting_start_time = pygame.time.get_ticks()
                        messages.append("Server: Toasting Bread for 5 seconds...")
                        input_text = ""
                    elif toaster_oven_in_use:
                        messages.append("Server: Toaster oven is in use...")
                        input_text = ""
                    else:
                        messages.append("Server: You need bread to use the Toaster Oven...")
                        input_text = ""
                    
                elif input_text.strip().upper() == "GRAB LETTUCE":
                    held_item = "Lettuce"
                    messages.append("Server: You grabbed Lettuce...")
                    input_text = ""
                
                elif input_text.strip().upper() == "GRAB TOMATO":
                    held_item = "Tomato"
                    messages.append("Server: You grabbed Tomato...")
                    input_text = ""
                
                elif input_text.strip().upper() == "GRAB BREAD":
                    held_item = "Bread"
                    messages.append("Server: You grabbed Bread...")
                    input_text = ""

                elif input_text.strip().upper() == "GRAB MEAT":
                    held_item = "Meat"
                    messages.append("Server: You grabbed Meat...")
                    input_text = ""
                elif input_text.strip().upper() == "DUMP":
                    held_item = None
                    input_text = ""
                #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                elif input_text.strip() !="":
                    messages.append(f"You: {input_text}")
                    messages.append(f"Server: I don't know '{input_text}' try 'Grab Tomato' or 'Use Frying Pan'")
                    input_text = ""

            elif event.key == pygame.K_BACKSPACE:#user hits backspace
                input_text = input_text[:-1]
            
        

            else: #any other key will be aded to the user input
                input_text += event.unicode


    #       -----       server chat box          -----
    title = font.render("Kitchen Server", True, white)
    window.blit(title, (400,270))
    
    pygame.draw.rect(window, gray, server_box)
    pygame.draw.rect(window, white, server_box, 3)
    messages_amount = 12 #this is how many messages will show in the box
    server_messages = messages[-messages_amount:]

    y = server_box.y + 25
    for message in server_messages: #for each message the user is allowed to see, render it one above the other as they come in. 
        message_surface = small_font.render(message, True, black)
        window.blit(message_surface, (server_box.x +10, y))
        y+=25

    #        -----        input chat box             -----
    input_title = font.render("Your message", True, white)
    window.blit(input_title, (350,660))

    box_color = green if input_active else gray
    pygame.draw.rect(window, white, input_box)
    pygame.draw.rect(window, box_color, input_box, 4)

    input_surface = font.render(input_text, True, black)
    window.blit(input_surface, (input_box.x + 10, input_box.y + 8))

    #        -----         Item boxes
    current_time = pygame.time.get_ticks()

    if frying_pan_in_use:
        window.blit(frying_pan_busy_img, frying_pan_box.topleft)
        if current_time - frying_start_time >= frying_pan_cook_time:
            frying_pan_in_use = False

            if held_item == "Meat":
                held_item = "Cooked Meat"
                messages.append("Server: meat is now cooked...")
    else:
        window.blit(frying_pan_idle_img, frying_pan_box.topleft)

    if cutting_board_in_use:
        window.blit(cutting_board_busy_img, cutting_board_box.topleft)
        if current_time - cutting_start_time >= cutting_use_time:
            cutting_board_in_use = False

            if held_item == "Tomato":
                held_item = "Cut Tomato"
                messages.append("Server: Tomato is now cut...")

            if held_item == "Lettuce":
                held_item = "Cut Lettuce"
                messages.append("Server: Lettuce is now cut...")

    else:
       window.blit(cutting_board_idle_img, cutting_board_box.topleft)

    if toaster_oven_in_use:
        window.blit(toaster_oven_busy_img, toaster_oven_box.topleft)
        if current_time - toasting_start_time >= toasting_cook_time:
            toaster_oven_in_use = False

            if held_item == "Bread":
                held_item = "Toasted Bread"
                messages.append("Server: Bread is now toasted...")
    else:
        window.blit(toaster_oven_idle_img, toaster_oven_box.topleft)
    


    #.    ------                ingredient boxes

    # i will change this to look less cluttered by using hashmap
    if held_item == "Lettuce":
        window.blit(lettuce_img, ingredient_box.topleft)
    elif held_item == "Tomato":
        window.blit(tomato_img, ingredient_box.topleft)
    elif held_item == "Bread":
        window.blit(bread_img, ingredient_box.topleft)
    elif held_item == "Meat":
        window.blit(meat_img, ingredient_box.topleft)
    elif held_item == "Cooked Meat":
        window.blit(cooked_meat_img, ingredient_box.topleft)
    elif held_item == "Cut Lettuce":
        window.blit(cut_lettuce_img, ingredient_box.topleft)
    elif held_item == "Cut Tomato":
        window.blit(cut_tomato_img, ingredient_box.topleft)
    elif held_item == "Toasted Bread":
        window.blit(toasted_bread_img, ingredient_box.topleft)

    else:
        window.blit(nothing_img, ingredient_box.topleft)

    

    ingredient_box_title = font.render("Holding", True, white)
    window.blit(ingredient_box_title, (ingredient_box.x, ingredient_box.y - 30))
    
    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()
        