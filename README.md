# catan-bot
CataNDroid
A semi-intelligent bot that plays Settlers of Catan.

We have built a bot that, at a very basic level, can play the board game Settlers of Catan. 

DEPENDENCIES, GAME:
- catanlog
- hexgrid
- undoredo

DEPENDENCIES, BOT:
- catan
- catanlog
- hexgrid
- undoredo

TO INSTALL DEPENDENCIES:
Simply run "make install" in the catan-bot directory. This will install catanlog, hexgrid, and undoredo. "catan" does not need to be installed, as we are using a local copy of it that we have edited. "catan" keeps track of the game, and "catan-spectator" oversees the interactions with it and the running of the bot. 

HOW TO RUN:
Running "make test" will initiate catan-spectator, which creates a game instance and a board instance from "catan" and displays the interactive window that contains them. In our implementation, there is one human player (the green player named "yurick", they will always go first), and three bot players (blue, red, and orange). The way the game differentiates between human and bot players is their name - specifically, whether it begins with "droid". If it comes to a time where any droid player needs to make a decision, it will do so automatically.
In order to see it in action, after running make test, the user must hit the "start game" button. They then can place a settlement at any of the nodes outlined in green. After choosing one, they then must place a road (the rules dictate that the road must adjoin the placed settlement, but our game does not force this yet, although the bot does obey this rule). Once this has been done, the bot will choose its initial settlement and road. This is done by picking the node with the highest number of "dots", or the highest potential to be rolled and therefore gain resources; the droid will then always build its road to the left.
This process is then repeated five times, as the other two bots place their first settlements and roads, and then all three bots place their second in reverse order. Then, it is the player's turn to place their final settlement and road. After doing so, the game begins.


CONTROL MECHANISM:

HIGH-LEVEL STRATEGY:

IMPLEMENTED FUNCTIONALITY:

We have had to implement many of the game-running functionality on our own, such as keeping track of cards in a player's hand and rolling the dice. After the basics such as those were taken care of, we moved on toward creating a strategy for the bot. 






