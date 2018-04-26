#!/usr/bin/env python3
# -*- coding: Utf-8 -*
# Author: aurelien.esnard@u-bordeaux.fr

from model import *
from view import *
from keyboard import *
from network import *
import sys
import pygame

### python version ###
print("python version: {}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]))
print("pygame version: ", pygame.version.ver)

################################################################################
#                                 MAIN                                         #
################################################################################

# parse arguments
if len(sys.argv) != 4:
    print("Usage: {} host port nickname".format(sys.argv[0]))
    sys.exit()
host = sys.argv[1]
port = int(sys.argv[2])
nickname = sys.argv[3]

# initialization
pygame.display.init()
pygame.font.init()
clock = pygame.time.Clock()
model = Model()
client = NetworkClientController(model, host, port, nickname)
view = GraphicView(model, nickname)
kb = KeyboardController(client)
chat = threading.Thread(None, fun_send_msg, None, (client.serv_connexion,nickname))
chat.daemon = True
chat.start()


# main loop
while True:
    # make sure game doesn't run at more than FPS frames per second
    dt = clock.tick(FPS)
    cont = kb.tick(dt)
    if not client.tick(dt, cont): break
    model.tick(dt)
    view.tick(dt)

# quit
print("Game Over!")
pygame.quit()
