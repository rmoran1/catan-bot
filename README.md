# catan-bot
CataNDroid

A semi-intelligent bot that plays Settlers of Catan.

## Dependencies (Game)

- catanlog
- hexgrid
- undoredo

## Dependencies (Bot)

- catan
- catanlog
- hexgrid
- undoredo

## Installing Dependencies

Simply run "make install" (or "make build") in the catan-bot directory. This will install catanlog, hexgrid, and undoredo. "catan" does not need to be installed, as we are using a local copy of it that we have edited. "catan" keeps track of the game, and "catan-spectator" oversees the interactions with it and the running of the bot.

## How to Run

Running "make test" will initiate catan-spectator, which creates a game instance and a board instance from "catan" and displays the interactive window that contains them. In our implementation, there is one human player (the green player named "yurick", they will always go first), and three bot players (blue, red, and orange). The way the game differentiates between human and bot players is their name - specifically, whether it begins with "droid". If it comes to a time where any droid player needs to make a decision, in the future, it will do so automatically.
In order to see it in action, after running make test, the user must hit the "Start Game" button. They then can place a settlement at any of the nodes outlined in green. After choosing one, they then must place a road (the rules dictate that the road must adjoin the placed settlement - our game does not force this yet, although the bot does obey this rule). Once this has been done, the bot will choose its initial settlement and road. This is done by picking the node with the highest number of "dots", or the highest potential to be rolled and therefore gain resources; the droid will then always build its road to the right.
This process is then repeated five times, as the other two bots place their first settlements and roads, and then all three bots place their second in reverse order. Then, it is the player's turn to place their final settlement and road. After doing so, the game begins.

## Control Mechanism

Our control mechanism of choice is a Finite State Machine. In the future the control mechanism will automatically run and cause the bot to make choices during its turn, but for now we have it activate upon clicking any port during a bot's turn in order to more clearly see each bot's decision making. Our control mechanism is relatively simple at the moment as we continue to more fully implement each feature in the game. Right now the FSM operates in two main areas: pre-game and in-game. When in the pre-game state, the bot will place a settlement and road at an optimum spot found during milestone one. When in the in-game state, the bot will make a decision on what building to purchase based upon the result of the high level strategy. In the future we will implement the functionality of states such as trading and playing development cards.

## High Level Strategy

Our high level strategy is currently used to inform the bot on which building it should purchase during its turn, as that is the main choice a player has during any turn. In the future we will implement other functionality available to the player during the game, such as playing dev cards or trading. Currently though, our high level strategy calculates what piece is most efficient to purchase based on a players current resources. The basic thought process is that if a bot has access to a large number of brick and wood compared to other resources, it should build roads for example. Right now we calculate the proportion of the cost of any piece to our currently available resources, and attempt to build whichever piece scores the best. In the future we will add more features that will impact the potential "score" of building each possible piece (e.g. if one road away from longest road, prioritize buying a road).

## Implemented Functionality

We have had to implement many of the game-running functionalities on our own, such as keeping track of cards in a player's hand, rolling the dice to assign resources, and creating the development card deck. After the basics such as those were taken care of, we moved on toward creating a strategy for the bot. As we said, clicking on any port when it is a bot's turn will print out the scores that we have determined for the bot;s next action. Later, this will be translated into an action proceeding from it.

## Expert Knowledge
Our bot does not utilize any true expert knowledge. Instead of following a set build order, it analyzes the board
every turn and considers a multitude of factors to determine what it should build.

### Milestone 05 04/20/20

## Going forward
Going forward, one can easily build upon the systems we have in place to make improvements to our existing factor system to make bots smarter. The main struggles
we faced in this project all seemed to stem from fleshing out features of an incomplete version of the game and hooking up the infrastructure of our bot. Now that
these tasks are complete, it should be easy enough to make any tweaks one desires when it comes to designing a Catan bot. Should you want to make a bot that focuses
more heavily on building the longest road, one can simply use our existing factor system to do that.

## Magic Variables
The main magic variables one can manipulate involve the factor system we have implemented which nudges the bot into building certain pieces over others.
If you wanted to change the factors that affect the decision making process of the bot, edit user_materials[player]["factors"]["city"], or any other piece,
to have the bot focus more on building those types of pieces.
