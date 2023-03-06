import pygame,sys,math,random,textwrap,pickle
from pygame.locals import *

#colors
BLACK=pygame.color.THECOLORS["black"]
WHITE=pygame.color.THECOLORS["white"]
RED=pygame.color.THECOLORS["red"]
GREEN=pygame.color.THECOLORS["green"]
BLUE=pygame.color.THECOLORS["blue"]
YELLOW=pygame.color.THECOLORS["yellow"]
ORANGE=pygame.color.THECOLORS["orange"]
VIOLET=pygame.color.THECOLORS["violet"]
LIGHT_CYAN=pygame.color.THECOLORS["lightcyan"]
LIGHT_GREEN=pygame.color.THECOLORS["lightgreen"]
LIGHT_BLUE=pygame.color.THECOLORS["lightblue"]
LIGHT_YELLOW=pygame.color.THECOLORS["lightyellow"]

#actual size of the window
SCREEN_WIDTH=640
SCREEN_HEIGHT=480

#tile size
TILE_WIDTH = 32
TILE_HEIGHT = 32

#size of the map in pixels
MAP_WIDTH = 640 * 2
MAP_HEIGHT = 480 * 2

#size of the map in tiles
TILE_MAP_WIDTH = int(MAP_WIDTH/TILE_WIDTH)
TILE_MAP_HEIGHT = int(MAP_HEIGHT/TILE_HEIGHT)

#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 4
MAX_ROOMS = 30

#spell values
HEAL_AMOUNT = 4
LIGHTNING_DAMAGE = 20
LIGHTNING_RANGE = 5 * TILE_WIDTH
CONFUSE_RANGE = 8 * TILE_WIDTH
CONFUSE_NUM_TURNS = 10
FIREBALL_RADIUS = 3 * TILE_WIDTH
FIREBALL_DAMAGE = 12

#experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

TORCH_RADIUS = 10

#sizes and coordinates relevant for the GUI
MSG_X = 5
MSG_WIDTH = int(SCREEN_WIDTH / 15)
MSG_HEIGHT = 3


def make_map():
    global level_map, objects, stairs
    
    #the list of objects with just the player
    objects = [player]
    
    #fill map with "unblocked" tiles
    level_map = [[ Tile(True, x, y)
              for y in range(0, MAP_HEIGHT, TILE_HEIGHT) ]
                  for x in range(0, MAP_WIDTH, TILE_WIDTH) ]

    rooms = []
    num_rooms = 0
 
    for r in range(MAX_ROOMS):
        #random width and height
        w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = random.randint(0, TILE_MAP_WIDTH - w - 1)
        y = random.randint(0, TILE_MAP_HEIGHT - h - 1)
        #"Rectangle" class makes rectangles easier to work with
        new_room = Rectangle(x, y, w, h)
 
        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
 
        if not failed:
            #this means there are no intersections, so this room is valid
            
            #"paint" it to the map's tiles
            create_room(new_room)
 
            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()
 
            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x * TILE_WIDTH
                player.y = new_y * TILE_HEIGHT
                level_map[new_x][new_y].entity = player
                player.tile = level_map[new_x][new_y]
                check_tile(new_x, new_y)
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel
 
                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                #draw a coin (random number that is either 0 or 1)
                if random.randint(0, 1) == 1:
                    #first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
                    
            #add some contents to this room, such as monsters
            place_objects(new_room)
            
            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1
            
    #create stairs at the center of the last room
    stairs = Object(new_x * TILE_WIDTH, new_y * TILE_HEIGHT, images[9], 'stairs')
    level_map[new_x][new_y].item = stairs
    objects.append(stairs)
    stairs.send_to_back()  #so it's drawn below the monsters

    
def random_choice_index(chances):  #choose one option from list of chances, returning its index
    #the dice will land on some number between 1 and the sum of the chances
    dice = random.randint(1, sum(chances))
 
    #go through all chances, keeping the sum so far
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w
 
        #see if the dice landed in the part that corresponds to this choice
        if dice <= running_sum:
            return choice
        choice += 1


def random_choice(chances_dict):
    #choose one option from dictionary of chances, returning its key
    chances = chances_dict.values()
    strings = list(chances_dict.keys())
    return strings[random_choice_index(chances)]


def from_dungeon_level(table):
    #returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0

    
def next_level():
    #advance to the next level
    global dungeon_level
    message('You take a moment to rest, and recover your strength.', VIOLET)
    player.fighter.heal(int(player.fighter.max_hp / 2))  #heal the player by 50%
 
    dungeon_level += 1
    message('After a rare moment of peace, you descend deeper into the heart of the dungeon...', RED)
    make_map()  #create a fresh new level!
    camera.update()
    update_gui()    
    
def render_all():
    global active_entities
    active_entities = []
    screen.fill(BLACK)
    #go through only visible tiles, and draw them
    for y in range(camera.tile_map_y, camera.y_range):
        for x in range(camera.tile_map_x, camera.x_range):
            tile = level_map[x][y]
            if tile.visible:
               if tile.block_sight:
                   screen.blit(images[0], (tile.x-camera.x, tile.y-camera.y))
               else:
                   screen.blit(images[1], (tile.x-camera.x, tile.y-camera.y))
                   if tile.item:
                      tile.item.draw(screen)
                   if tile.entity:
                      tile.entity.draw(screen)
                      active_entities.append(tile.entity)
    if impact:
       screen.blit(impact_image, impact_image_pos)
    #render the GUI                  
    screen.blit(gui, (10,456))                  
    #print the game messages, one line at a time
    if message_log:
       y = 10
       for msg in game_msgs:
           screen.blit(msg, (5,y))
           y += 24
    pygame.display.flip()


def create_room(room):
    global level_map
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            tile = level_map[x][y]
            tile.blocked = False
            tile.block_sight = False
            tile.room = room

            
def create_h_tunnel(x1, x2, y):
    global level_map
    #horizontal tunnel. min() and max() are used in case x1>x2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        level_map[x][y].blocked = False
        level_map[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
    global level_map
    #vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        level_map[x][y].blocked = False
        level_map[x][y].block_sight = False


def check_tile(x, y):
    tile = level_map[x][y]
    if not tile.explored:
       tile.explored = True 
       old_x = x
       old_y = y
       for x in range(old_x - 1, old_x + 2):
           for y in range(old_y - 1, old_y + 2):
               level_map[x][y].visible = True
       if tile.room and not  tile.room.explored:
          room = tile.room
          room.explored = True
          for x in range(room.x1 , room.x2 + 1):
              for y in range(room.y1 , room.y2 + 1):
                  level_map[x][y].visible = True       


def is_blocked(x, y):
    #first test the map tile
    if level_map[x][y].blocked:
        return True
    #now check for any blocking monster
    if level_map[x][y].entity:
        return True
    return False


def place_objects(room):
    #this is where we decide the chance of each monster or item appearing.
 
    #maximum number of monsters per room
    max_monsters = from_dungeon_level([[2, 1], [3, 4], [5, 6]])
 
    #chance of each monster
    monster_chances = {}
    monster_chances['orc'] = 80  #orc always shows up, even if all other monsters have 0 chance
    monster_chances['troll'] = from_dungeon_level([[15, 3], [30, 5], [60, 7]])
 
    #maximum number of items per room
    max_items = from_dungeon_level([[1, 1], [2, 4]])
 
    #chance of each item (by default they have a chance of 0 at level 1, which then goes up)
    item_chances = {}
    item_chances['heal'] = 35  #healing potion always shows up, even if all other items have 0 chance
    item_chances['lightning'] = from_dungeon_level([[25, 4]])
    item_chances['fireball'] =  from_dungeon_level([[25, 6]])
    item_chances['confuse'] =   from_dungeon_level([[10, 2]])
    item_chances['sword'] =     from_dungeon_level([[5, 4]])
    item_chances['shield'] =    from_dungeon_level([[15, 8]])
    
    #choose random number of monsters
    num_monsters = random.randint(0, max_monsters)
 
    for i in range(num_monsters):
        #choose random spot for this monster
        x = random.randint(room.x1+1, room.x2-1)
        y = random.randint(room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not is_blocked(x, y):
            choice = random_choice(monster_chances)
            if choice == 'orc':
                #create an orc
                fighter_component = Fighter(hp=20, defense=0, power=4, exp=35, death_function=monster_death)
                ai_component = BasicMonster()               
                monster = Object(x*TILE_WIDTH, y*TILE_HEIGHT, images[3], 'orc', blocks=True,
                    fighter=fighter_component, ai=ai_component)
            elif choice == 'troll':
                #create a troll
                fighter_component = Fighter(hp=30, defense=2, power=8, exp=100, death_function=monster_death)
                ai_component = BasicMonster()               
                monster = Object(x*TILE_WIDTH, y*TILE_HEIGHT, images[4], 'troll', blocks=True,
                    fighter=fighter_component, ai=ai_component)
                
            objects.append(monster)
            level_map[x][y].entity = monster
            monster.tile = level_map[x][y]
            
    #choose random number of items
    num_items = random.randint(0, max_items)
 
    for i in range(num_items):
        #choose random spot for this item
        x = random.randint(room.x1+1, room.x2-1)
        y = random.randint(room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not is_blocked(x, y):
            choice = random_choice(item_chances)
            if choice == 'heal':
               #create a healing potion
               item_component = Item(use_function=cast_heal)
 
               item = Object(x*TILE_WIDTH, y*TILE_HEIGHT, images[6],
                             'healing potion', item=item_component)
            elif choice == 'lightning':
               #create a lightning bolt scroll
               item_component = Item(use_function=cast_lightning)
 
               item = Object(x*TILE_WIDTH, y*TILE_HEIGHT, images[5],
                             'scroll of lightning bolt', item=item_component)
            elif choice == 'fireball':
               #create a fireball scroll
               item_component = Item(use_function=cast_fireball)
 
               item = Object(x*TILE_WIDTH, y*TILE_HEIGHT, images[5],
                             'scroll of fireball', item=item_component)
            elif choice == 'confuse':
               #create a confuse scroll
               item_component = Item(use_function=cast_confuse)
 
               item = Object(x*TILE_WIDTH, y*TILE_HEIGHT, images[5],
                             'scroll of confusion', item=item_component)
            elif choice == 'sword':
                #create a sword
                equipment_component = Equipment(slot='right hand', power_bonus=3)
                item = Object(x*TILE_WIDTH, y*TILE_HEIGHT, images[7],
                              'sword', equipment=equipment_component)
            elif choice == 'shield':
                #create a shield
                equipment_component = Equipment(slot='left hand', defense_bonus=1)
                item = Object(x*TILE_WIDTH, y*TILE_HEIGHT, images[8],
                              'shield', equipment=equipment_component)
                
            objects.append(item)
            level_map[x][y].item = item
            item.send_to_back()  #items appear below other objects
               

def player_move_or_attack(dx, dy):
    global player_action
    target = None
    #move by the given amount, if the destination is not blocked
    x = int((player.x + dx)/TILE_WIDTH)
    y = int((player.y + dy)/TILE_HEIGHT)
    if not is_blocked(x, y):
       player.x += dx
       player.y += dy
       player.tile.entity = None
       level_map[x][y].entity = player
       player.tile = level_map[x][y]
       check_tile(x, y)
       camera.update()
    elif level_map[x][y].entity:
       target = level_map[x][y].entity
       #attack if target found
       #if target.fighter:
       player.fighter.attack(target)
    player_action = 'taked-turn'

    
def player_death(player):
    #the game ended!
    global game_state
    message('You died!', RED)
    game_state = 'dead'
    #for added effect, transform the player into a corpse!
    player.image = images[10]
    player.image_index = 10
    player.tile.entity = None
    player.tile.item = player

 
def monster_death(monster):
    #transform it into a nasty corpse! it doesn't block, can't be
    #attacked and doesn't move
    message('The ' + monster.name + ' is dead! You gain ' + str(monster.fighter.exp) + ' experience points.', ORANGE)
    monster.image = images[10]
    monster.image_index = 10
    monster.tile.entity = None
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()
    monster.item = Item()
    monster.item.owner = monster
    if not monster.tile.item:
       monster.tile.item = monster

    
def closest_monster(max_range):
    #find closest enemy, up to a maximum range, and in the player's FOV
    closest_enemy = None
    closest_dist = max_range + 1  #start with (slightly more than) maximum range
 
    for obj in active_entities:
        if obj.fighter and obj != player and obj.tile.visible:
            #calculate distance between this object and the player
            dist = player.distance_to(obj)
            if dist < closest_dist:  #it's closer, so remember it
                closest_enemy = obj
                closest_dist
    return closest_enemy
   
                
def target_tile(max_range=None):
    global message_log
    #return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
    while True:         
        pygame.time.Clock().tick(30)
        for event in pygame.event.get():    #wait for events
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
               if event.key == K_ESCAPE:
                  message_log = False 
                  return (None, None)  #cancel if the player pressed Escape
            if event.type == MOUSEBUTTONDOWN:
               if event.button==3:
                  message_log = False 
                  return (None, None)  #cancel if the player right-clicked
               #accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
               if event.button==1:
                  mouse_x, mouse_y = event.pos
                  mouse_x += camera.x
                  mouse_y += camera.y
                  x = int(mouse_x /TILE_WIDTH)
                  y = int(mouse_y /TILE_HEIGHT)
                  if (level_map[x][y].visible and
                      (max_range is None or player.distance(mouse_x, mouse_y) <= max_range)):
                     return (mouse_x, mouse_y)
        #render the screen          
        render_all()

        
def target_monster(max_range=None):
    #returns a clicked monster inside FOV up to a range, or None if right-clicked
    while True:
        (x, y) = target_tile(max_range)
        if x is None:  #player cancelled
            return None
 
        #return the first clicked monster, otherwise continue looping
        x = int(x / TILE_WIDTH)
        y = int(y / TILE_HEIGHT)
        tile = level_map[x][y]
        for obj in active_entities:
            if obj.x == tile.x and obj.y == tile.y and obj.fighter and obj != player:
                return obj
               
    
def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health.', RED)
        return 'cancelled'
      
    message('Your wounds start to feel better!', VIOLET)
    player.fighter.heal(HEAL_AMOUNT)


def cast_lightning():
    #find closest enemy (inside a maximum range) and damage it
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:  #no enemy found within maximum range
        message('No enemy is close enough to strike.', RED)
        return 'cancelled'
 
    #zap it!
    message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
        + str(LIGHTNING_DAMAGE) + ' hit points.', LIGHT_BLUE)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)

    
def cast_fireball():
    #ask the player for a target tile to throw a fireball at
    message('Left-click a target tile for the fireball, or right-click to cancel.', LIGHT_CYAN)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    message('The fireball explodes, burning everything within ' + str(int(FIREBALL_RADIUS/TILE_WIDTH)) + ' tiles!', ORANGE)
 
    for obj in active_entities:  #damage every fighter in range, including the player
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', ORANGE)
            obj.fighter.take_damage(FIREBALL_DAMAGE)


def cast_confuse():
    #ask the player for a target to confuse
    message('Left-click an enemy to confuse it, or right-click to cancel.', LIGHT_CYAN)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None: return 'cancelled'
 
    #replace the monster's AI with a "confused" one; after some turns it will restore the old AI
    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster  #tell the new component who owns it
    message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', LIGHT_GREEN)
            
    
def message(new_msg, color = WHITE):
    global game_msgs, message_log, game_msgs_data
    if not message_log:
       game_msgs = []
       game_msgs_data = []
    message_log = True
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
            del game_msgs_data[0]
 
        #add the new message
        msg = font.render(line, True, color)    
        game_msgs.append(msg)
        game_msgs_data.append((line,color))

    render_all()
    wait_time = 0
    while wait_time < 10:
        pygame.time.Clock().tick(30)
        wait_time += 1


def entity_falsh(entity):
    global impact
    impact = True
    impact_image_pos[0] = entity.x-camera.x
    impact_image_pos[1] = entity.y-camera.y
    render_all()
    impact = False
    wait_time = 0
    while wait_time < 5:
        pygame.time.Clock().tick(30)
        wait_time += 1    
    flash = 3
    flash_time = 2
    if entity.fighter.hp <=0:
       flash_time = 4
    entity_old_image = entity.image
    while flash_time > 1:
        pygame.time.Clock().tick(30)
        if flash:
           entity.image = blank_surface
        render_all()
        if not flash:
           flash = 6
        flash -= 1
        if flash < 1:
           flash = False
           flash_time -= 1
           entity.image = entity_old_image 
           if flash_time < 1:
              flash_time = 0
              flash = False
              entity.image = entity_old_image


def get_impact_image():
    color = (230,230,230)
    impact_image = pygame.Surface((TILE_WIDTH, TILE_WIDTH)).convert()
    impact_image.set_colorkey(impact_image.get_at((0,0)))
    image = pygame.Surface((int(TILE_WIDTH/2), int(TILE_HEIGHT/3))).convert()
    top = 0
    left = 0
    bottom = image.get_width()-1
    right = image.get_height()-1
    center_x = int(image.get_width()/2)-1
    center_y = int(image.get_height()/2)-1
    pygame.draw.line(image, color, (top,left), (bottom,right), 2)
    #pygame.draw.line(image, color, (bottom,left), (top,right), 2)
    #pygame.draw.line(image, color, (center_x,top), (center_x,bottom), 2)
    #pygame.draw.line(image, color, (left,center_y),(right,center_y), 2)
    x = int((impact_image.get_width()-image.get_width())/2)
    y = int((impact_image.get_height()-image.get_height())/2)
    impact_image.blit(image, (x,y))
    return impact_image


def menu(header, options):
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
    screen.fill(BLACK)
    header = font.render(header, True, YELLOW)
    screen.blit(header,(0,0))
    #print all the options
    y = header.get_height()+5
    letter_index = ord('a')
    for option_text in options:
        text = font.render('(' + chr(letter_index) + ') ' + option_text, True, WHITE)
        screen.blit(text,(0,y))
        y += text.get_height()
        letter_index += 1
    pygame.display.flip()
    while True:
        pygame.time.Clock().tick(30)
        for event in pygame.event.get():    #wait for events
            if event.type == QUIT:
                save_game()
                pygame.quit()
                sys.exit()
                
            if event.type == KEYDOWN:
               if event.key == K_ESCAPE:
                  save_game() 
                  pygame.quit()
                  sys.exit()
               else:
                  #wait for a key-press 
                  #convert the ASCII code to an index;
                  #if it corresponds to an option, return it
                  if event.unicode != '':
                     index = ord(event.unicode) - ord('a')
                     if index >= 0 and index < len(options): 
                        return index
                     else:
                        return None

                    
def inventory_menu(header):
    #show a menu with each item of the inventory as an option
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        for item in inventory:
            text = item.name
            #show additional information, in case it's equipped
            if item.equipment and item.equipment.is_equipped:
                text = text + ' (on ' + item.equipment.slot + ')'
            options.append(text)
 
    index = menu(header, options)
 
    #if an item was chosen, return it
    if index is None or len(inventory) == 0:
       return None
    return inventory[index].item

    
def update_gui():
    global gui
    gui = font.render('HP: ' + str(player.fighter.hp) + '/' + str(player.fighter.max_hp) +  ' '*60 + ' Dungeon level ' + str(dungeon_level), True, YELLOW)
    #gui= font.render('Dungeon level ' + str(dungeon_level) +  ' '*5 + 'HP: ' + str(player.fighter.hp) + '/' + str(player.fighter.max_hp), True, YELLOW)

    
def get_names_under_mouse(mouse_x, mouse_y):
    #return a string with the names of all objects under the mouse
    x = int((mouse_x + camera.x)/TILE_WIDTH)
    y = int((mouse_y + camera.y)/TILE_HEIGHT)    
    #create a list with the names of all objects at the mouse's coordinates and in FOV
    tile = level_map[x][y]
    if tile.visible:
       if not(tile.item or tile.entity):
          message("There is nothing there")
       else:
          names = []
          if tile.item:
             names.append(tile.item.name)
          if tile.entity:
             names.append(tile.entity.name)
          if tile.item and tile.entity:
             names = ' and '.join(names)  #join the names, separated by commas
             message("There is "+names+" there")
          else:
             message("There is "+names[0]+" there")
    else:
       message("You can't see that spot")

       
def check_level_up():
    #see if the player's experience is enough to level-up
    level_up_exp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    if player.fighter.exp >= level_up_exp:
        #it is! level up and ask to raise some stats
        player.level += 1
        player.fighter.exp -= level_up_exp
        message('Your battle skills grow stronger! You reached level ' + str(player.level) + '!', YELLOW)
 
        choice = None
        while choice == None:  #keep asking until a choice is made
            choice = menu('Level up! Choose a stat to raise:',
                ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
                'Strength (+1 attack, from ' + str(player.fighter.power) + ')',
                'Agility (+1 defense, from ' + str(player.fighter.defense) + ')'])
 
        if choice == 0:
            player.fighter.max_hp += 20
            player.fighter.hp += 20
        elif choice == 1:
            player.fighter.power += 1
        elif choice == 2:
            player.fighter.defense += 1
        update_gui()

        
def get_equipped_in_slot(slot):  #returns the equipment in a slot, or None if it's empty
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None


def get_all_equipped(obj):  #returns a list of equipped items
    if obj == player:
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return []  #other objects have no equipment


def save_game():
    #open a new empty shelve (possibly overwriting an old one) to write the game data
    for obj in objects:
        obj.image = None
    game_data = {}
    game_data['map'] = level_map
    game_data['objects'] = objects
    game_data['player'] = player
    game_data['stairs'] = stairs
    game_data['inventory'] = inventory
    game_data['game_msgs_data'] = game_msgs_data
    game_data['game_state'] = game_state
    game_data['player_action'] = player_action
    game_data['message_log'] = message_log
    game_data['dungeon_level'] = dungeon_level
    with open('LIttle_Rogue.dat', 'wb') as file:
         file_saver=pickle.Pickler(file)
         file_saver.dump(game_data)

    
def load_game():
    #open the previously saved shelve and load the game data
    global level_map, objects, player, stairs, camera, inventory, dungeon_level
    global game_msgs, game_msgs_data, game_state, player_action, message_log
    
    with open('LIttle_Rogue.dat', 'rb') as file:
         file_loader=pickle.Unpickler(file)
         game_data=file_loader.load()
    
    level_map = game_data['map']
    objects = game_data['objects']
    player = game_data['player']
    stairs = game_data['stairs']
    inventory = game_data['inventory']
    game_msgs_data = game_data['game_msgs_data']     
    game_state = game_data['game_state']
    player_action = game_data['player_action']
    message_log = game_data['message_log']
    dungeon_level = game_data['dungeon_level']
    
    camera = Camera(player)
    update_gui()
    for obj in objects:
        obj.image = images[obj.image_index]
    game_msgs = []       
    for line,color in game_msgs_data:
        msg = font.render(line, True, color)
        game_msgs.append(msg)
        
       
def new_game():
    global player, camera, game_state, player_action, active_entities
    global gui, game_msgs, game_msgs_data, message_log, inventory,  dungeon_level 

    #create object representing the player
    fighter_component = Fighter(hp=30, defense=2, power=5, exp=0, death_function=player_death)        
    player = Object(TILE_WIDTH*10, TILE_HEIGHT*7, images[2], "player",
                    blocks=True, fighter=fighter_component)
    
    player.level = 1

    #generate map (at this point it's not drawn to the screen)
    dungeon_level = 1
    make_map()
    camera = Camera(player)
    
    game_state = 'playing'
    player_action = 'didnt-take-turn' 
    inventory = []
    active_entities = []
    
    update_gui()
    #create the list of game messages and their colors, starts empty
    game_msgs = []
    game_msgs_data = []
    message_log = True
    #a warm welcoming message!
    message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', RED)
    
    #initial equipment: a dagger
    equipment_component = Equipment(slot='right hand', power_bonus=2)
    obj = Object(0, 0, images[10], 'dagger', equipment=equipment_component)
    inventory.append(obj)
    equipment_component.equip()


def msgbox(text):
    menu(text, [])  #use menu() as a sort of "message box"

    
def play_game():
    global player_action, message_log
    
    clock = pygame.time.Clock()
    player_move = False
    pygame.key.set_repeat(400, 30)

    while True:
        #loop speed limitation
        #30 frames per second is enought
        clock.tick(30)
        
        for event in pygame.event.get():    #wait for events
            if event.type == QUIT:
                save_game()
                pygame.quit()
                sys.exit()
   
            if game_state == 'playing':    
               if event.type == KEYDOWN:
                  if event.key == K_ESCAPE:
                     save_game()
                     return
                  message_log = False
                  #movement keys
                  if event.key == K_UP:
                     player_move_or_attack(0, -TILE_HEIGHT)
                  elif event.key == K_DOWN:
                     player_move_or_attack(0, TILE_HEIGHT)
                  if event.key == K_LEFT:
                     player_move_or_attack(-TILE_WIDTH, 0)
                  elif event.key == K_RIGHT:
                     player_move_or_attack(TILE_WIDTH, 0)
                  if event.key == K_g:
                     #pick up an item
                     if player.tile.item and player.tile.item.item: 
                        player.tile.item.item.pick_up()
                        player.tile.item = None
                  if event.key == K_i:
                     #show the inventory; if an item is selected, use it
                     chosen_item = inventory_menu("Press the key next to an item to use it, or any other to cancel.")
                     if chosen_item is not None:
                        chosen_item.use()
                        update_gui()
                  if event.key == K_d:
                     if player.tile.item:
                        message("There's already something here")
                     else:
                        #show the inventory; if an item is selected, drop it
                        chosen_item = inventory_menu('Press the key next to an item to drop iy, or any other to cancel.')
                        if chosen_item is not None:
                           chosen_item.drop()
                  if event.key == K_c:
                    #show character information
                    level_up_exp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
                    menu('Character Information', ['Level: ' + str(player.level), 'Experience: ' + str(player.fighter.exp),
                        'Experience to level up: ' + str(level_up_exp), 'Maximum HP: ' + str(player.fighter.max_hp),
                        'Attack: ' + str(player.fighter.power), 'Defense: ' + str(player.fighter.defense)])
                  if event.key in (K_LESS, K_PERIOD) or event.unicode == '>':
                     #go down stairs, if the player is on them
                     if stairs.x == player.x and stairs.y == player.y:
                        next_level()                           
               if event.type == MOUSEBUTTONDOWN:
                  if event.button==1:
                     player_move = True
                     message_log = False
                  elif event.button==3:
                     mouse_x, mouse_y = event.pos
                     get_names_under_mouse(mouse_x, mouse_y)
               if event.type == MOUSEBUTTONUP:
                  if event.button==1:
                     player_move = False

        if player_move and game_state == 'playing':
           pos = pygame.mouse.get_pos()
           x = int((pos[0] + camera.x)/TILE_WIDTH)
           y = int((pos[1] + camera.y)/TILE_HEIGHT)
           tile = level_map[x][y]
           if tile != player.tile:
              #vector from player to the target, and distance
              dx = tile.x - player.x
              dy = tile.y - player.y
              distance = math.sqrt(dx ** 2 + dy ** 2)
              #normalize it to length 1 (preserving direction), then round it and
              #convert to integer so the movement is restricted to the map grid
              dx = int(round(dx / distance)) * TILE_WIDTH
              dy = int(round(dy / distance)) * TILE_HEIGHT
              player_move_or_attack(dx, dy)
        
           
        #let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
           for entity in active_entities:
               if entity.ai:
                  entity.ai.take_turn()
           player_action = 'didnt-take-turn'
        

        #draw everything
        render_all()


def main_menu():
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont('Arial', 45, bold=True)
    game_title = title_font.render("Little Rogue", True, GREEN)
    game_title_pos = (int((SCREEN_WIDTH - game_title.get_width())/2), 150)
    cursor_img = pygame.Surface((16, 16)).convert()
    cursor_img.set_colorkey(cursor_img.get_at((0,0)))
    pygame.draw.polygon(cursor_img, RED, [(0, 0), (16, 8), (0, 16)], 0)
    cursor_img_pos = [195, 254]
    menu_choices = ['Play a new game', 'Continue last game', 'Quit']   
    for i in range(len(menu_choices)):
        menu_choices[i] = font.render(menu_choices[i], True, WHITE)
    choice = 0
    choices_length = len(menu_choices)-1
    while True:        
        #loop speed limitation
        #30 frames per second is enought
        clock.tick(30)
        
        for event in pygame.event.get():    #wait for events
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
   
            if event.type == KEYDOWN:
               if event.key == K_ESCAPE:
                  pygame.quit()
                  sys.exit()

               if event.key == K_UP:
                  cursor_img_pos[1] -= 24
                  choice -= 1
                  if choice < 0:
                     choice = choices_length
                     cursor_img_pos[1] = 302
               elif event.key == K_DOWN:
                  cursor_img_pos[1] += 24
                  choice += 1
                  if choice > choices_length:
                     choice = 0
                     cursor_img_pos[1] = 254
               if event.key == K_RETURN:
                  if choice == 0:  #new game
                     new_game()
                     play_game()
                  if choice == 1:  #load last game
                     #try:
                     load_game()
                     #except:
                        #msgbox(' No saved game to load.')
                        #continue
                     play_game()
                  elif choice == 2:  #quit
                     return

        #draw everything
        screen.fill(BLACK)
        y = 250
        for menu_choice in menu_choices:
            screen.blit(menu_choice,(230,y))
            y += 24
        #show the background image
        #screen.blit(bg_img, (0, 0))
        #show the game's title, and some credits!
        screen.blit(game_title, game_title_pos)
        screen.blit(cursor_img, cursor_img_pos)                
        pygame.display.flip()
        
    
class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    def __init__(self, x, y, image, name, blocks=False, fighter=None, ai=None, item=None, equipment=None):
        self.x = x
        self.y = y
        self.image = image
        self.image_index = images.index(image)
        self.name = name
        self.blocks = blocks
        self.tile = None
        self.fighter = fighter
        if self.fighter:  #let the fighter component know who owns it
            self.fighter.owner = self
        self.ai = ai
        if self.ai:  #let the AI component know who owns it
            self.ai.owner = self
        self.item = item
        if self.item:  #let the Item component know who owns it
            self.item.owner = self
        self.equipment = equipment
        if self.equipment:  #let the Equipment component know who owns it
            self.equipment.owner = self
            #there must be an Item component for the Equipment component to work properly
            self.item = Item()
            self.item.owner = self
            
            
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        x = int((self.x + dx)/TILE_WIDTH)
        y = int((self.y + dy)/TILE_HEIGHT)
        if not is_blocked(x, y):
           self.x += dx
           self.y += dy
           self.tile.entity = None
           level_map[x][y].entity = self
           self.tile = level_map[x][y]

    def move_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance)) * TILE_WIDTH
        dy = int(round(dy / distance)) * TILE_HEIGHT
        self.move(dx, dy)
 
    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
      
    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)      
      
    def send_to_back(self):
        #make this object be drawn first, so all others appear above it if they're in the same tile.
        global objects
        objects.remove(self)
        objects.insert(0, self)
       
    def draw(self, surface):
        #draw object at its position
        surface.blit(self.image, (self.x-camera.x, self.y-camera.y))
          
        
class Fighter:
    #combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, defense, power, exp, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.exp = exp
        self.death_function = death_function
 
    def attack(self, target):
        #a simple formula for attack damage
        damage = self.power - target.fighter.defense
 
        if damage > 0:
            #make the target take some damage
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')
 
    def take_damage(self, damage):
        #apply damage if possible
        if damage > 0:
            self.hp -= damage
            entity_falsh(self.owner)
            if self.owner == player:
               update_gui()
            #check for death. if there's a death function, call it
            if self.hp <= 0:
                self.hp = 0
                update_gui()
                function = self.death_function
                if function is not None:
                    function(self.owner)
                if self.owner != player:  #yield experience to the player
                    player.fighter.exp += self.exp
                    #level up if needed
                    check_level_up()
                    
    def heal(self, amount):
        #heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

                    
class Item:
    #an item that can be picked up and used.
    def __init__(self, use_function=None):
        self.use_function = use_function
 
    def pick_up(self):
        #add to the player's inventory and remove from the map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up ' + self.owner.name + '.', RED)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', GREEN)
            
            #special case: automatically equip, if the corresponding equipment slot is unused
            equipment = self.owner.equipment
            if equipment and get_equipped_in_slot(equipment.slot) is None:
               equipment.equip()

    def drop(self):
        #special case: if the object has the Equipment component, dequip it before dropping
        if self.owner.equipment:
           self.owner.equipment.dequip()
        
        #add to the map and remove from the player's inventory. also, place it at the player's coordinates
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        player.tile.item = self.owner
        message('You dropped a ' + self.owner.name + '.', YELLOW)   
 
    def use(self):
        #special case: if the object has the Equipment component, the "use" action is to equip/dequip
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return
        
        #just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner)  #destroy after use, unless it was cancelled for some reason


class Equipment:
    #an object that can be equipped, yielding bonuses. automatically adds the Item component.
    def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0):
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
 
        self.slot = slot
        self.is_equipped = False
 
    def toggle_equip(self):  #toggle equip/dequip status
        if self.is_equipped:
            self.dequip()
        else:
            self.equip()
 
    def equip(self):
        #if the slot is already being used, dequip whatever is there first
        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.dequip()

        #equip object and show a message about it
        self.is_equipped = True
        player.fighter.power +=  self.power_bonus
        player.fighter.defense +=  self.defense_bonus
        player.fighter.max_hp +=  self.max_hp_bonus
        message('Equipped ' + self.owner.name + ' on ' + self.slot + '.', LIGHT_GREEN)
 
    def dequip(self):
        #dequip object and show a message about it
        if not self.is_equipped: return
        self.is_equipped = False
        player.fighter.power -=  self.power_bonus
        player.fighter.defense -=  self.defense_bonus
        player.fighter.max_hp -=  self.max_hp_bonus
        if player.fighter.hp > player.fighter.max_hp:
           player.fighter.hp = player.fighter.max_hp 
        message('Dequipped ' + self.owner.name + ' from ' + self.slot + '.', LIGHT_YELLOW)

       
class BasicMonster:
    #AI for a basic monster.
    def take_turn(self):
        #a basic monster takes its turn. if you can see it, it can see you
        monster = self.owner
        if monster.tile.visible:
            distance = monster.distance_to(player)
            if distance < 128:
               #move towards player if far away
               if distance >= 64:
                  monster.move_towards(player.x, player.y)
               #close enough, attack! (if the player is still alive.)
               elif player.fighter.hp > 0:
                  monster.fighter.attack(player)


class ConfusedMonster:
    #AI for a temporarily confused monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns
 
    def take_turn(self):
        if self.num_turns > 0:  #still confused...
            #move in a random direction, and decrease the number of turns confused
            dx = random.randint(-1, 1) * TILE_WIDTH
            dy = random.randint(-1, 1) * TILE_HEIGHT
            self.owner.move(dx, dy)
            self.num_turns -= 1
 
        else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name + ' is no longer confused!', RED)

            
class Tile:
    #a tile of the map and its properties
    def __init__(self, blocked, x, y, block_sight = None):
        self.blocked = blocked
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight
        self.x = x
        self.y = y
        self.visible = False
        self.explored = False
        self.room = None
        self.entity = None
        self.item = None

        
class Rectangle :
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.explored = False
 
    def center(self):
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return (center_x, center_y)
 
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)        

class Camera :
    #a camera class to follow the player
    def __init__(self, target):
        self.target = target
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT + TILE_HEIGHT
        self.x = self.target.x - int(self.width / 2)
        self.y = self.target.y - int(self.height / 2)
        self.center_x = self.x + int(self.width / 2)
        self.center_y = self.y + int(self.height / 2)
        self.right = self.x + self.width
        self.bottom = self.y + self.height
        self.tile_map_x = int(self.x / TILE_WIDTH)
        self.tile_map_y = int(self.y / TILE_HEIGHT)
        self.tile_map_width = int(self.width / TILE_WIDTH)
        self.tile_map_height = int(self.height / TILE_HEIGHT)
        self.x_range = self.tile_map_x + self.tile_map_width
        self.y_range = self.tile_map_y + self.tile_map_height
        self.fix_position()
        
    def update(self):
        #if self.x > 0 and  self.target.x < self.center_x \
        #or self.right < MAP_WIDTH and  self.target.x > self.center_x:
        if self.target.x != self.center_x:
           x_move = self.target.x - self.center_x
           self.x += x_move
           self.center_x += x_move
           self.right += x_move
           self.tile_map_x = int(self.x / TILE_WIDTH)
           self.x_range = self.tile_map_x + self.tile_map_width
        #if self.y > 0 and  self.target.y < self.center_y \
        #or self.bottom < MAP_HEIGHT and  self.target.y > self.center_y:
        if self.target.y != self.center_y:   
           y_move = self.target.y - self.center_y
           self.y += y_move
           self.center_y += y_move
           self.bottom += y_move
           self.tile_map_y = int(self.y / TILE_HEIGHT)
           self.y_range = self.tile_map_y + self.tile_map_height
        self.fix_position()
           
    def fix_position(self):
        if self.x < 0:
           self.x = 0
           self.center_x = self.x + int(self.width / 2)
           self.right = self.x + self.width
           self.tile_map_x = int(self.x / TILE_WIDTH)
           self.x_range = self.tile_map_x + self.tile_map_width
        elif self.right > MAP_WIDTH:
           self.right = MAP_WIDTH
           self.x = self.right - self.width
           self.center_x = self.x + int(self.width / 2)
           self.tile_map_x = int(self.x / TILE_WIDTH)
           self.x_range = self.tile_map_x + self.tile_map_width
        if self.y < 0:
           self.y = 0
           self.center_y = self.y + int(self.height / 2)
           self.bottom = self.y + self.height
           self.tile_map_y = int(self.y / TILE_HEIGHT)
           self.y_range = self.tile_map_y + self.tile_map_height
        elif self.bottom > MAP_HEIGHT:
           self.bottom = MAP_HEIGHT
           self.y = self.bottom - self.height
           self.center_y = self.y + int(self.height / 2)
           self.tile_map_y = int(self.y / TILE_HEIGHT)
           self.y_range = self.tile_map_y + self.tile_map_height
           

def main():
    
    pygame.init()
    
    global screen, font, images, gui, blank_surface, impact_image, impact_image_pos, impact
    #Open Pygame window
    screen = pygame.display.set_mode((640, 480),) #add RESIZABLE or FULLSCREEN
    #Title
    pygame.display.set_caption("Little Rogue")
    #font
    font = pygame.font.SysFont('Arial', 20, bold=True)

    rogue_tiles=pygame.image.load('rogue_tiles.png').convert()
    tile_width = int(rogue_tiles.get_width()/11)
    tile_height = rogue_tiles.get_height()
    blank_surface = pygame.Surface((TILE_WIDTH, TILE_HEIGHT)).convert()
    blank_surface.set_colorkey(blank_surface.get_at((0,0)))
    impact_image = get_impact_image()
    impact_image_pos = [0,0]
    impact = False
    images = []
    for i in range(11):
        image = rogue_tiles.subsurface(tile_width*i, 0, tile_width, tile_height).convert()
        if i not in (0, 1, 9):
           image.set_colorkey(image.get_at((0,0)))
        images.append(image)
        
    main_menu()


if __name__ == "__main__":
    main()
