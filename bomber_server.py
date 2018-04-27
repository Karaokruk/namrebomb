#!/usr/bin/env python3
# -*- coding: Utf-8 -*
# Author: aurelien.esnard@u-bordeaux.fr

from model import *
from view import *
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
if (len(sys.argv) == 2):
    port = int(sys.argv[1])
    map_file = DEFAULT_MAP
elif (len(sys.argv) == 3):
    port = int(sys.argv[1])
    map_file = sys.argv[2]
else:
    print("Usage: {} port [map_file]".format(sys.argv[0]))
    sys.exit()

# initialization
pygame.display.init()
pygame.font.init()
clock = pygame.time.Clock()

model = Model()
model.load_map(map_file)
#for _ in range(10): model.add_fruit()
server = NetworkServerController(model, port)
#view = GraphicView(model, "server")
commands = threading.Thread(None, fun_commands, None, (server,))
commands.daemon = True
commands.start()

# main loop
while True:
    # make sure game doesn't run at more than FPS frames per second
    dt = clock.tick(FPS)
    server.tick(dt, map_file)
    model.tick(dt)
    #view.tick(dt)
    if (not commands.is_alive()):
        break

# quit
print_server_console_msg("Thanks for playing!")
pygame.quit()
