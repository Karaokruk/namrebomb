# -*- coding: Utf-8 -*
# Author: aurelien.esnard@u-bordeaux.fr

from model import *
import socket
import select
import threading
import time


# messages codes
REMOVE_CODE = 0
CHARACTER_CODE = 1
MOVE_CODE = 2
BOMB_CODE = 3
BOMB2_CODE = 4
MSG_CODE = 5
FRUIT_CODE = 6
PM_CODE = 7
HEAL_CODE = 8
DAMAGE_CODE = 9


# server properites
SERVER_SIZE = 4
MESSAGE_SIZE = 8
FRUIT_SPAWN_LIMIT = 15
BOMB_SPAWN_LIMIT = 15


FORBIDDEN_CHARACTERS = ['\n', ' ', ':', '|', ',', '(', ')', '>', '*']


#print functions
def print_server_console_msg(msg):
    print(SERVER_CONSOLE_COLOR + msg + DEFAULT_COLOR)

def print_nb_connected_people(nb_people):
    print(CONNECTED_PEOPLE_COLOR + "{}/{} people connected.".format(nb_people, SERVER_SIZE) + DEFAULT_COLOR)


#content_to_str functions
def character_to_str(character):
    tab = [str(character.kind), character.nickname, str(character.pos), str(character.direction), str(character.health)]
    return "|".join(tab)

def fruit_to_str(fruit):
    tab = [str(fruit.pos), str(fruit.kind)]
    return "|".join(tab)

def bomb_to_str(bomb):
    tab = [str(bomb.pos), str(bomb.countdown), str(bomb.time_to_explode)]
    return "|".join(tab)

def hour_string():
    return "(" + str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ") "


#str_to_content functions
def str_to_character(board, char_str):
    tab = char_str.split("|")
    character = Character(tab[1], int(tab[0]), board, str_to_position(tab[2]))
    character.direction = int(tab[3])
    character.health = int(tab[4])
    return character

def str_to_fruit(board, fruit_str):
    tab = fruit_str.split("|")
    fruit = Fruit(int(tab[1]), board, str_to_position(tab[0]))
    return fruit

def str_to_bomb(board, bomb_str):
    tab = bomb_str.split("|")
    bomb = Bomb(board, str_to_position(tab[0]))
    bomb.countdown = int(tab[1])
    bomb.time_to_explode = int(tab[2])
    return bomb
    
def str_to_position(position_str):
    tab = position_str.split(", ")
    x = tab[0].split("(")
    y = tab[1].split(")")
    return (int(x[1]), int(y[0]))


#thread functions
def fun_send_msg(s, nickname) :
    while True:
        msg = input("")
        if(msg != "" and msg != " "):
            if(msg == "quit" or msg == "exit"):
                break
            if msg[0] == '>':
                tab = msg.split(" ", 1)
                if not len(tab) <= 1:
                    msg = tab[1]
                    receiver = tab[0].split(">")[1]
                    print(PM_COLOR + hour_string() + "to " + NICKNAME_COLOR + receiver + PM_COLOR + " : " + msg + DEFAULT_COLOR)
                    msg = "pm:" + receiver + " " + PM_COLOR + hour_string() + "from " + NICKNAME_COLOR + nickname + PM_COLOR + " : " + msg + DEFAULT_COLOR
                    send_with_size(s, msg)
                else:
                    print_server_console_msg("Please type a message.")
            else:
                msg = CHAT_COLOR + hour_string() + NICKNAME_COLOR + nickname + CHAT_COLOR + " : " + msg + DEFAULT_COLOR
                print(msg)
                msg = "msg:" + msg
                send_with_size(s, msg)

def fun_commands(server):
    while True:
        command = input("")
        if command == "quit" or command == "exit":
            break
        if command == "help":
            print_server_console_msg("Here is a list of all the commands:")
            print(NICKNAME_COLOR +"quit (or exit)\n" + JOIN_COLOR + "help\n" + CONNECTED_PEOPLE_COLOR + "kill\n" + JOIN_COLOR + "fruit\n" + CONNECTED_PEOPLE_COLOR + "bomb\n" + PM_COLOR + "heal\n" + SERVER_CONSOLE_COLOR + "damage"+ DEFAULT_COLOR)
        else:
            command = command.split(" ")
            if command[0] == "kill":
                kill_command(command, server)
            elif command[0] == "fruit":
                command_fruit(command, server)
            elif command[0] == "bomb":
                command_bomb(command, server)
            elif command[0] == "heal":
                command_heal(command,server)
            elif command[0] == "damage":
                command_damage(command,server)
            else:
                print_server_console_msg("Command unknown!")


#console commands functions
def kill_command(command, server):
    
    if(len(command) != 2):
        print_server_console_msg("To kill somebody, type \"kill <this horrible person nickname>\".")
        print_server_console_msg("You can also kill every player by typing \"kill *\", but that's not very nice...")
    elif not server.player_list:
        print_server_console_msg("Nobody to kill!")
    elif (command[1] == "*"):
        print_server_console_msg("You killed everybody! You're a monster!")
        for (c,n) in server.player_list:
            send_quit_character(c,n)
            server.model.kill_character(n)
            c.close()
            server.client_list.remove(c)
        for (c,n) in server.player_list:
            server.player_list.remove((c,n))
    else:
        character = server.model.look(command[1])
        if character:
            for c in server.client_list:
                send_quit_character(c, command[1])
            for (c,n) in server.player_list:
                if (n == command[1]):
                    server.player_list.remove((c,n))
                    c.close()
                    server.client_list.remove(c)
            server.model.kill_character(command[1])
        else:
            print_server_console_msg(command[1] + " wasn't found on the server.")

def command_fruit(command, server):
    nb_to_spawn = 0 
    if(len(command) == 1):
        nb_to_spawn = 1
    elif(len(command) > 2 or not (command[1].isdigit())):
        print_server_console_msg("You can add a fruit on the board with the command \"fruit\" (this one is hard to guess).")
        print_server_console_msg("To add multiple fruits, type \"fruit <number of fruits in digits>\".")
    else:
        nb_to_spawn = int(command[1])
        if(nb_to_spawn > FRUIT_SPAWN_LIMIT):
            nb_to_spawn = FRUIT_SPAWN_LIMIT
            print_server_console_msg("Don't spawn too much fruits please, that's not funny.")
            print_server_console_msg(str(FRUIT_SPAWN_LIMIT) + " is enough.")
    for i in range(nb_to_spawn):
        fruit = Fruit(random.choice(FRUITS), server.model.map,server.model.map.random())
        server.model.fruits.append(fruit)
        for c in server.client_list:
            send_fruit(c,fruit)

def command_bomb(command, server):
    nb_to_spawn = 0
    if(len(command)==1):
        nb_to_spawn = 1
    elif(len(command) > 2 or not (command[1].isdigit())):
        print_server_console_msg("you can drop a bomb on the board with the command \"bomb\" (this one is hard to guess).")
        print_server_console_msg("To add multiple bombs (yay, fireworks!), type \"bomb <number of bombs in digits>\".")
    else:
        nb_to_spawn = int(command[1])
        if(nb_to_spawn > BOMB_SPAWN_LIMIT):
            nb_to_spawn = BOMB_SPAWN_LIMIT
            print_server_console_msg("Don't spawn too much bomb please, that's not funny... ok, it is funny, but still.")
            print_server_console_msg(str(BOMB_SPAWN_LIMIT) + " is enough.")
    for i in range(nb_to_spawn):
        bomb = Bomb(server.model.map,server.model.map.random())
        server.model.bombs.append(bomb)
        for c in server.client_list:
            send_bomb2(c,bomb)

def command_heal(command, server):
    list_to_heal = []
    base_heal = False
    healing = 0
    if(len(command) == 2):
        base_heal = True
        if(command[1] == "*"):
            list_to_heal = server.model.characters
            print_server_console_msg("Everybody has been healed to base health!")
        else:
            char = server.model.look(command[1])
            if not char:
                print_server_console_msg(command[1]+" wasn't found on the server.")
            else:
                if char.health < HEALTH:
                    list_to_heal.append(char)
                else:
                    print_server_console_msg(command[1] + " didn't needed to be heal to base health.")
    elif(len(command) == 3 and command[2].isdigit()):
        if(command[1] == "*"):
            list_to_heal = server.model.characters
            print_server_console_msg("Everybody has been healed " + command[2] + " life points!")
        else:
            char = server.model.look(command[1])
            if not char:
                print_server_console_msg(command[1]+" wasn't found on the server.")
            else:
                list_to_heal.append(char)
                print_server_console_msg(command[1] + " has been healed " + command[2] + " points !")
    else:
        print_server_console_msg("If you want to be a nice person, you can heal people with \"heal <nickname> < number of life points to give>\".")
        print_server_console_msg("If no number is given, player will go back to base health.")
        print_server_console_msg("To heal all players, you can type \"*\" instead of the nickname.")
    for char in list_to_heal:
        if base_heal:
            if char.health < HEALTH:
                healing = HEALTH - char.health
        else:
            healing = int(command[2])
        for c in server.client_list:
            send_healing(c,char.nickname,healing)
            char.health =+ healing
        

def command_damage(command, server):
    if(len(command) == 3 and command[2].isdigit()):
        if(command[1] == "*"):
            print_server_console_msg("Everybody took " + command[2] + " points of damage!")
            for char in server.model.characters:
                damage = int(command[2])
                char.health -= damage
                if char.health <= 0:
                    print_server_console_msg("{} is dead!".format(char.nickname))
                for c in server.client_list:
                    send_damage(c,char.nickname, damage)
                    if char.health <= 0:
                        for c in server.client_list:
                            send_quit_character(c, command[1])
                        for (c,n) in server.player_list:
                            if (n == char.nickname):
                                server.player_list.remove((c,n))
                                c.close()
                                server.client_list.remove(c)
        else:
            char = server.model.look(command[1])
            if not char:
                print_server_console_msg(command[1] + " wasn't found on the server.")
            else:
                damage = int(command[2])
                for c in server.client_list:
                    send_damage(c,char.nickname, damage)
                char.health -= damage
                if char.health <= 0:
                    for c in server.client_list:
                        send_quit_character(c, command[1])
                    for (c,n) in server.player_list:
                        if (n == command[1]):
                            server.player_list.remove((c,n))
                            c.close()
                            server.client_list.remove(c)
                    server.model.kill_character(command[1])
                print_server_console_msg(command[1] + " took " + command[2] + " points of damage !")
                if char.health <= 0:
                    print_server_console_msg("{} is dead!".format(char.nickname))
    else:
        print_server_console_msg("If you want to be a bad person, you can inflict damage to people with \"damage <nickname> < number of damage points to give>\".")
        print_server_console_msg("To inflict damage to all players, you can type \"*\" instead of the nickname.")
        
#parsing function
def parse_message(msg):
    if msg == "remove":
        return REMOVE_CODE
    elif msg == "character":
        return CHARACTER_CODE
    elif msg == "move":
        return MOVE_CODE
    elif msg == "bomb":
        return BOMB_CODE
    elif msg == "bomb2":
        return BOMB2_CODE
    elif msg == "msg":
        return MSG_CODE
    elif msg == "fruit":
        return FRUIT_CODE
    elif msg == "pm":
        return PM_CODE
    elif msg == "heal":
        return HEAL_CODE
    elif msg == "damage":
        return DAMAGE_CODE
    return REMOVE_CODE
    

#sending functions
def send_size(connexion, encoded_msg):
    size_msg = str(len(encoded_msg))
    padding_zero = MESSAGE_SIZE - len(size_msg)
    while (padding_zero > 0):
        size_msg = "0" + size_msg
        padding_zero -= 1
    connexion.send(size_msg.encode())

def send_with_size(connexion,msg):
    msg = msg.encode()
    send_size(connexion, msg)
    connexion.send(msg)

def send_fruit(connexion,fruit):
    fruit_str = "fruit:"
    fruit_str += fruit_to_str(fruit)
    send_with_size(connexion,fruit_str)
    
def send_character(client_list, character):
    character_str = "character:"
    character_str += character_to_str(character)
    for c in client_list:
        send_with_size(c, character_str)

def send_movement(connexion, nickname, direction):
    movement_str = "move:"
    movement_str += nickname + '|' + str(direction)
    send_with_size(connexion, movement_str)

def send_bomb(connexion, nickname):
    bomb_str = "bomb:"
    bomb_str += nickname
    send_with_size(connexion, bomb_str)

def send_bomb2(connexion, bomb):
    bomb_str = "bomb2:"
    bomb_str += bomb_to_str(bomb)
    send_with_size(connexion, bomb_str)

def send_quit_character(connexion, nickname):
    remove_str = "remove:"
    remove_str += nickname
    send_with_size(connexion, remove_str)
    
def send_healing(connexion, nickname, healing):
    healing_str = "heal:" + nickname + ":" + str(healing)
    send_with_size(connexion, healing_str)
    
def send_damage(connexion, nickname, damage):
    damage_str = "damage:" + nickname + ":" + str(damage)
    send_with_size(connexion,damage_str)


#server functions to initialize network client controller
def check_nickname(model, nickname):
    if not nickname:
        return False
    for char in model.characters:
        if nickname == char.nickname:
            return False
    for char in nickname:
        if char in FORBIDDEN_CHARACTERS:
            return False
    return True

def send_base_model(co, model, map_file):
    map_str = map_file
    
    characters_tab = []
    for c in model.characters:
        characters_tab.append(character_to_str(c))
    characters_str = "  ".join(characters_tab)
    
    fruits_tab = []
    for c in model.fruits:
        fruits_tab.append(fruit_to_str(c))
    fruits_str = "  ".join(fruits_tab)
    
    bombs_tab = []
    for c in model.bombs:
        bombs_tab.append(bomb_to_str(c))
    bombs_str = "  ".join(bombs_tab)
    
    model_tab = [map_str, characters_str, fruits_str, bombs_str]
    model_str = "\n".join(model_tab)
    
    send_with_size(co, model_str)

################################################################################
#                          NETWORK SERVER CONTROLLER                           #
################################################################################

class NetworkServerController:

    def __init__(self, model, port):
        
        self.model = model
        self.port = port
        self.host = ''
        self.client_list = []
        self.player_list = []
        
        self.main_connexion = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.main_connexion.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.main_connexion.bind((self.host, self.port))
        self.main_connexion.listen(1)
        print(JOIN_COLOR + "Welcome, master of the server!" + DEFAULT_COLOR)
        print(PM_COLOR + "You have a lot more power than you think here..." + DEFAULT_COLOR)
        print(PM_COLOR + "That's right... You can use... COMMANDS!" + DEFAULT_COLOR)
        print(PM_COLOR + "You can type \"help\" to see a list of the commands you cans use." + DEFAULT_COLOR)
        print_server_console_msg("Have fun <3")
        print_nb_connected_people(0)


    # time event

    def tick(self, dt, map_file):
        fruit_pop = random.randint(0,500)
        if fruit_pop == 1:
            command_fruit(["fruit"],self)
        bomb_pop = random.randint(0,200)
        if bomb_pop == 1:
            command_bomb(["bomb"],self)
        
        request_list, _, _ = select.select(self.client_list+[self.main_connexion], [], [], 0)
        
        for request in request_list:
            
            if request == self.main_connexion:
                client, _ = self.main_connexion.accept()

                if (len(self.model.characters) >= SERVER_SIZE):
                    server_full_msg = b""
                    client.send(server_full_msg)
                else:
                    server_full_msg = b"1"
                    client.send(server_full_msg)
                    msg_size = client.recv(MESSAGE_SIZE)
                    if not msg_size:
                        nickname_taken_msg = b""
                        client.send(nickname_taken_msg)
                    else:
                        nickname = client.recv(int(msg_size.decode()))
                        nickname = nickname.decode()
                        is_nickname_ok = check_nickname(self.model, nickname)
                        
                        if not is_nickname_ok:
                            nickname_taken_msg = b""
                            client.send(nickname_taken_msg)
                        else:
                            new_character = self.model.add_character(nickname)
                            nickname_taken_msg = b"1"
                            client.send(nickname_taken_msg)
                            send_base_model(client, self.model, map_file)
                            send_character(self.client_list, new_character)
                    
                            self.client_list.append(client)
                            self.player_list.append((client, nickname))
                            print(JOIN_COLOR + "{} joins the server.".format(new_character.nickname) + DEFAULT_COLOR)
                            print_nb_connected_people(len(self.model.characters))
                
            else:
                encoded_msg_size = request.recv(MESSAGE_SIZE)
                msg_size = encoded_msg_size.decode()
                if not msg_size:
                    request.close()
                    self.client_list.remove(request)
                    for (c, n) in self.player_list:
                        if request == c:
                            char = self.model.look(n)
                            if char:
                                self.model.quit(n)
                                self.player_list.remove((c, n))
                                for client in self.client_list:
                                    send_quit_character(client, n) 
                    print_nb_connected_people(len(self.model.characters))
                    return True

                encoded_msg = request.recv(int(msg_size))
                msg = encoded_msg.decode()
                
                tab = msg.split(":")
                msg_type = parse_message(tab[0])
                if msg_type == REMOVE_CODE:
                    self.model.quit(tab[1])
                    self.player_list.remove((request, tab[1]))
                    request.close()
                    self.client_list.remove(request)
                    print_nb_connected_people(len(self.model.characters))
                if msg_type == MOVE_CODE:
                    move_tab = tab[1].split("|")
                    self.model.move_character(move_tab[0], int(move_tab[1]))
                if msg_type == BOMB_CODE:
                    self.model.drop_bomb(tab[1])
                if msg_type == MSG_CODE:
                    tab.remove(tab[0])
                    print(":".join(tab))
                if msg_type == PM_CODE:
                    tab.remove(tab[0])
                    msg = ":".join(tab)
                    split_msg = msg.split(" ", 1)
                    for (c, n) in self.player_list:
                        if split_msg[0] == n:
                            msg_to_send = "pm:" + split_msg[1]
                            send_with_size(c, msg_to_send)
                else:
                    for c in self.client_list:
                        if c != request:
                            c.send(encoded_msg_size)
                            c.send(encoded_msg)
        return True

################################################################################
#                          NETWORK CLIENT CONTROLLER                           #
################################################################################




class NetworkClientController:

    def __init__(self, model, host, port, nickname):
        self.model = model
        self.host = host
        self.port = port
        self.nickname = nickname

        # Hello
        self.serv_connexion = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.serv_connexion.connect((self.host, self.port))

        # Can i connect to server ?
        can_connect = self.serv_connexion.recv(1)
        if ( can_connect.decode == ""):
            print_server_console_msg("Server is full.")
            sys.exit(1)

        # Here is my nickname
        send_with_size(self.serv_connexion, nickname)

        #Is my nickname available?
        nickname_ok = self.serv_connexion.recv(1)
        if ( nickname_ok.decode() == ""):
            print_server_console_msg("nickname \"{}\" already used (or lame)!".format(nickname))
            sys.exit(1)

        # Thanks you for the model
        print(JOIN_COLOR + "Welcome to the server, " + nickname + "." + DEFAULT_COLOR)
        print(PM_COLOR + "Move with the directional arrows and drop bombs with space" + DEFAULT_COLOR)
        print(PM_COLOR + "You have access to a chat. Just type a message and you will send it to everybody (yes, that's what chats do). " + DEFAULT_COLOR)
        print(PM_COLOR + "To send a private message to somebody, type \">\" followed by his nickname, a space, plus your message" + DEFAULT_COLOR)
        print(PM_COLOR + "You can quit the game anytime by entering \"exit\" or \"quit\"." + DEFAULT_COLOR)
        print_server_console_msg("Have lots of fun!")
        msg_size = self.serv_connexion.recv(MESSAGE_SIZE)
        if not msg_size :
            sys.exit(1)
        model_str = self.serv_connexion.recv(int(msg_size.decode()))
        
        self.decode_base_model(model_str.decode(), nickname)
        print_nb_connected_people(len(self.model.characters))


    def decode_base_model(self, model_str, nickname):
        model_tab = model_str.split("\n")
        self.model.load_map(model_tab[0])
        characters_tab = model_tab[1].split("  ")
        for c in characters_tab:
            if (c != ""):
                self.model.characters.append(str_to_character(self.model.map, c))
        for i in self.model.characters:
            if i.nickname == nickname:
                self.model.player = i
        fruits_tab = model_tab[2].split("  ")
        for f in fruits_tab:
            if (f != ""):
                self.model.fruits.append(str_to_fruit(self.model.map, f))
        bombs_tab = model_tab[3].split("  ")
        for b in bombs_tab:
            if (b != ""):
                self.model.bombs.append(str_to_bomb(self.model.map, b))
            

    # keyboard events

    def keyboard_quit(self):
        #print("=> event \"quit\"")
        return False

    def keyboard_move_character(self, direction):
        #print("=> event \"keyboard move direction\" {}".format(DIRECTIONS_STR[direction]))
        if not self.model.player: return True
        nickname = self.model.player.nickname
        if direction in DIRECTIONS:
            self.model.move_character(nickname, direction)
            send_movement(self.serv_connexion, nickname, direction)
        return True

    def keyboard_drop_bomb(self):
        #print("=> event \"keyboard drop bomb\"")
        if not self.model.player: return True
        nickname = self.model.player.nickname
        self.model.drop_bomb(nickname)
        send_bomb(self.serv_connexion, nickname)
        return True

    # time event

    def tick(self, dt, cont):
        if not self.model.player:
            return False
        if not cont:
            send_quit_character(self.serv_connexion, self.model.player.nickname)
            return False
        request_list, _, _ = select.select([self.serv_connexion], [], [], 0)
        for request in request_list:
            msg_size = self.serv_connexion.recv(MESSAGE_SIZE)
            if not msg_size:
                print_server_console_msg("May the server rest in peace.")
                return False
            msg = self.serv_connexion.recv(int(msg_size.decode()))
            
            msg = msg.decode()
            tab = msg.split(":")
            msg_type = parse_message(tab[0])
            if msg_type == REMOVE_CODE:
                char = self.model.look(tab[1])
                if char:
                    self.model.quit(tab[1])
                print_nb_connected_people(len(self.model.characters))
            elif msg_type == CHARACTER_CODE:
                character = str_to_character(self.model.map, tab[1])
                self.model.characters.append(character)
                print(JOIN_COLOR + "{} joins the server.".format(character.nickname) + DEFAULT_COLOR)
                print_nb_connected_people(len(self.model.characters))
            elif msg_type == MOVE_CODE:
                move_tab = tab[1].split("|")
                self.model.move_character(move_tab[0], int(move_tab[1]))
            elif msg_type == BOMB_CODE:
                self.model.drop_bomb(tab[1])
            elif msg_type == BOMB2_CODE:
                bomb= str_to_bomb(self.model.map,tab[1])
                self.model.bombs.append(bomb)
            elif msg_type == FRUIT_CODE:
                fruit= str_to_fruit(self.model.map,tab[1])
                self.model.fruits.append(fruit)
            elif msg_type == MSG_CODE or msg_type == PM_CODE:
                tab.remove(tab[0])
                print(":".join(tab))
            elif msg_type == HEAL_CODE:
                char = self.model.look(tab[1])
                char.health += int(tab[2])
                print_server_console_msg(char.nickname + " has been healed, his health is now " + str(char.health) + "!")
            elif msg_type == DAMAGE_CODE:
                char = self.model.look(tab[1])
                char.health -= int(tab[2])
                print_server_console_msg(char.nickname + " took damage, his health is now " + str(char.health) + "!")
        return True
