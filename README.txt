Bienvenue sur le jeu Bomber !

Pour pouvoir jouer vous devez d'abord lancer un serveur avec l'éxecutable bomber_server.py, avec le port que vous voulez, ainsi que le chemin vers une map(ce dernier paramètre est facultatif, si aucune map n'est rentrée, la map par défault sera choisie).
Pour rejoindre ce serveur, vous devez lancer l'exécutable bomber_client.py.

Que ce soit pour le serveur ou le client, des instructions sont affichées au lancement de l'exécutable.

Depuis le terminal où vous avez lancé bomber_server.py, vous pouvez utliser des commandes telles que:
	-exit:
		-"exit" ou "quit" ferme le serveur, l'exécutable, et déconnecte tous les clients présent.
	-help:
		-"help" affiche la liste de commandes disponibles.
	-kill:
		-"kill <pseudo>" tue le personnage avec le pseudo correspondant.
	-fruit:
		-"fruit" fait apparaître un fruit aléatoire à une position aléatoire sur le terrain.
		-"fruit <nombre>" fait apparaître le nombre choisi de fruits, chacun de genre aléatoire, à une position aléatoire.
	-bomb:
		-"bomb" fait apparaître une bombe à une position aléatoire sur le terrain.
		-"bomb <nombre>" fait apparaître le nombre choisi de bombes,chacune à une position aléatoire.
	-heal:
		-"heal <pseudo> <nombre>" donne le nombre indiqué de points de vie au joueur indiqué.
		-"heal <pseudo>" remonte le nombre de points de vie du joueur indiqué jusqu'au nombre initial (si le nombre de points de vie du joueur est supérieur ou égaux à celui donné en début de partie, ils restent inchangés).
	-damage:
		--"damage <pseudo> <nombre>" retire le nombre indiqué de points de vie au joueur indiqué. Si son nombre de points de vie descends à zéro ou en dessous, le personnage meurt.

Pour toutes les commandes nécessitant un pseudo, on peut cibler tout les joueurs en entrant "*" à la place du pseudo (exemple: "heal *").
Pour toutes les commandes nécéssitant un nombre, ce nombre doit être écrit en chiffre. Certains sont limités.

Depuis le terminal où vous avez lancé bomber_client.py, vous avez accès à un chat, avec tous les autres joueurs.
Tapez un message puis appuyez sur entrée, il sera envoyé au serveur et à tous les clients.
Si avant votre message, vous tapez ">" suivi du pseudo d'un joueur, ce message ne sera envoyé qu'à ce joueur.

Sur la fenêtre de jeu, vous pouvez vous déplacer avec les flèches directionelles et poser des bombes avec espaces.
Vous partez avec un nombre de 50 points de vie.
Les fruits rendent 10 points de vie.
Si vous êtes touchés lors de l'explosion d'une bombe, vous perdrez 10 points de vie, et vous aurez une courte période d'immunité.
Lorsque vous posez une bombe, vous devez attendre 2 secondes avant de pouvoir en poser une autre.
Des bombes et des fruits apparaîssent aléatoirement sur la grille.

Vous pouvez quitter la partie à tout moment en entrant "exit" ou "quit" sur le terminal.

Amusez-vous bien!
