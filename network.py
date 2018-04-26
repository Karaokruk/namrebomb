# -*- coding: Utf-8 -*
# Author: aurelien.esnard@u-bordeaux.fr

from model import *
import socket
import select
import threading


REMOVE_CODE = 0
CHARACTER_CODE = 1
MOVE_CODE = 2
BOMB_CODE = 3

SERVER_SIZE = 4

MESSAGE_SIZE = 8

FORBIDDEN_CHARACTERS = ['\n', ' ', ':', '|', ',', '(', ')']

def character_to_str(character):
    tab = [str(character.kind), character.nickname, str(character.pos), str(character.direction), str(character.health)]
    return "|".join(tab)

def fruit_to_str(fruit):
    tab = [str(fruit.pos), str(fruit.kind)]
    return "|".join(tab)

def bomb_to_str(bomb):
    tab = [str(bomb.pos), str(bomb.countdown), str(bomb.time_to_explode)]
    return "|".join(tab)

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


def parse_message(msg):
    tab = msg.split(":")
    if tab[0] == "remove":
        return REMOVE_CODE
    elif tab[0] == "character":
        return CHARACTER_CODE
    elif tab[0] == "move":
        return MOVE_CODE
    elif tab[0] == "bomb":
        return BOMB_CODE
    return REMOVE_CODE
    

def send_character(client_list, character):
    character_str = "character:"
    character_str += character_to_str(character)
    for c in client_list:
        send_size(c, character_str.encode())
        c.send(character_str.encode())

def send_size(connexion, encoded_msg):
    size_msg = str(len(encoded_msg))
    padding_zero = MESSAGE_SIZE - len(size_msg)
    while (padding_zero > 0):
        size_msg = "0" + size_msg
        padding_zero -= 1
    connexion.send(size_msg.encode())

def send_movement(connexion, nickname, direction):
    movement_str = "move:"
    movement_str += nickname + '|' + str(direction)
    movement_str = movement_str.encode()
    send_size(connexion, movement_str)
    connexion.send(movement_str)

def send_bomb(connexion, nickname):
    bomb_str = "bomb:"
    bomb_str += nickname
    bomb_str = bomb_str.encode()
    send_size(connexion, bomb_str)
    connexion.send(bomb_str)

def send_quit_character(connexion, nickname):
    remove_str = "remove:"
    remove_str += nickname
    remove_str = remove_str.encode()
    send_size(connexion, remove_str)
    connexion.send(remove_str)


def print_nb_connected_people(nb_people):
    print("{}/{} people connected.".format(nb_people, SERVER_SIZE))

################################################################################
#                          NETWORK SERVER CONTROLLER                           #
################################################################################


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
    
    model_msg = model_str.encode()
    send_size(co, model_msg)
    co.send(model_msg)


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
        print("Have fun <3")
        print_nb_connected_people(0)


    # time event

    def tick(self, dt, map_file):
        
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
                            print("{} joins the server.".format(new_character.nickname))
                            print_nb_connected_people(len(self.model.characters))
                
            else:
                msg_size = request.recv(MESSAGE_SIZE)
                if not msg_size.decode():
                    request.close()
                    self.client_list.remove(request)
                    for (c, n) in self.player_list :
                        if request == c:
                            char = self.model.look(n)
                            if char:
                                self.model.kill_character(n)
                            
                                self.player_list.remove((c, n))
                                for client in self.client_list:
                                    send_quit_character(client, n) 
                    print_nb_connected_people(len(self.model.characters))
                    return True
                msg = request.recv(int(msg_size.decode()))
                for c in self.client_list:
                    if c != request:
                        c.send(msg_size)
                        c.send(msg)
                msg = msg.decode()
                
                
                tab = msg.split(":")
                msg_type = parse_message(tab[0])
                if msg_type == REMOVE_CODE:
                    self.model.kill_character(tab[1])
                    self.player_list.remove((request, tab[1]))
                    request.close()
                    self.client_list.remove(request)
                if msg_type == MOVE_CODE:
                    move_tab = tab[1].split("|")
                    self.model.move_character(move_tab[0], int(move_tab[1]))
                if msg_type == BOMB_CODE:
                    self.model.drop_bomb(tab[1])

        # ...
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
            print("Server is full.")
            sys.exit(1)

        # Here is my nickname
        send_size(self.serv_connexion, nickname.encode())
        self.serv_connexion.send(nickname.encode())

        #Is my nickname available?
        nickname_ok = self.serv_connexion.recv(1)
        if ( nickname_ok.decode() == ""):
            print("nickname \"{}\" already used (or lame)!".format(nickname))
            sys.exit(1)

        # Thanks you for the model
        print("Welcome to the server.")
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
            self.model.characters.append(str_to_character(self.model.map, c))
        for i in self.model.characters:
            if i.nickname == nickname:
                self.model.player = i
        fruits_tab = model_tab[2].split("  ")
        for f in fruits_tab:
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
                print("May the server rest in peace.")
                return False
            msg = self.serv_connexion.recv(int(msg_size.decode()))
            
            msg = msg.decode()
            tab = msg.split(":")
            msg_type = parse_message(tab[0])
            if msg_type == REMOVE_CODE:
                char = self.model.look(tab[1])
                if char:
                    self.model.kill_character(tab[1])
            if msg_type == CHARACTER_CODE:
                character = str_to_character(self.model.map, tab[1])
                self.model.characters.append(character)
                print("{} joins the server.".format(character.nickname))
                print_nb_connected_people(len(self.model.characters))
            if msg_type == MOVE_CODE:
                move_tab = tab[1].split("|")
                self.model.move_character(move_tab[0], int(move_tab[1]))
            if msg_type == BOMB_CODE:
                self.model.drop_bomb(tab[1])
        return True
