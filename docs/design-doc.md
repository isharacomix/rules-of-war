Open Tactics - Design Document
==============================

Overview
--------
Open Tactics is a Free and Open Source engine for *Deterministic Perfect
Information Turn-Based Tactical Wargames*. A game fits this description
if the following two criteria hold:

 * Any game can be replayed using nothing but the initial configuration
   of the game board and a list of the actions that the players took.
   (Deterministic, non-random).
 * A player should be able to make a turn without having to interact with
   their opponent during the turn. In other words, the game should be
   "playable-by-post".
   (Perfect Information, decentralized)

Chess is an example of such a game. You can recreate a board perfectly by
starting from the common configuration and then replaying the moves of the
two players. You can do this even if you don't have the final configuration
of the board. Furthermore, a player can "play-by-post" by sending their moves
to their opponent by internet protocol or carrier pigeon. Each player can make
the other player's moves for them on their local board without "cheating".

The purpose of the open tactics project is to create an engine to create
these kinds of games with minimal technical overhead. The rules should be
well-defined enough to support many different games.


Philosophy
----------
**A player's strength in a game powered by the open tactics engine should
ultimately be a factor of how well they grasp the system of rules.**

This is not to say that games that involve randomness or imperfect information
are not fun, challenging, or good. Randomness encourages players to practice
risk assessment, which is a positive mental state. Imperfect information gives
players an opportunity to attempt to build a complete picture from the bits
of information revealed by their opponents, also a positive state. This engine
is designed to make it possible to explore a space of possible games, and
certain limitations have to be made in order to reduce the engineering burden.
The engine could be extended to support such games, and may be done in the
near future, but for now, the limited scope helps focus the creative energy
of the project.


Systems of Rules
----------------
This project is motivated by the theory of *games as systems of rules*.
The idea behind this theory is that a player who learns rules by trial and
error will eventually achieve mastery of the game as they learn the optimal
reactions to their opponent's actions.


Project Goals
-------------
 * A fun, challenging wargame
 * Flexibility to add and rebalance units
 * Rapid prototyping and playtesting for new units
 * Asynchronous play-by-post


Rules
-----
 * The board shall be defined as a rectangular grid of tiles
 * A tile belongs to one member of a set of "terrains", with various properties
 * Some tiles can be captured by some units and owned by a player
 * A tile can be occupied by one or zero units
 * Units are under the control of players.
 * Each turn, each unit under the control of a player may MOVE and then take
   a number of ACTIONs (usually one).
 * An action is represented in the following format:
   ```[(x,y),(x2,y2)...(xZ,yZ)],action,[(x1,y1)...],action2,...```
 * The first set of coordinates are the starting position of the unit and
   each tile the unit moves between to its destination. None of these tiles
   may be occupied by enemy units
 * An action is some action that the unit is permitted to take, such as
   attack, capture, load, etc.
 * The second set of coordinates is the area of effect of the action.
 * Some units maybe permitted to take multiple actions.

 (I wonder if moving should be part of the action list).


Notes
-----
Part of the reason for defining the rules in this way is that, once again,
the game should be abstract enough to support many different types of games.
Ideally, the game will be modular where there are two types of rules -
the low-level rules (how moving and attacking work) and the high-level rules
(how much damage units do to each other). The idea is that after you decide
your low-level rules, you should be able to add new units and rebalance them
without ever changing the source code required to implement the low-level
rules (similar to how we abstract away from curses with a drawing library).

The rules should be definable in something like JSON. What kinds of units
and terrain there are. The kinds of actions that can be taken. The actions
should then hook into python functions that actually affect the board. As
long as the API for making a move is as simple as "pick location, pick action,
pick AOE", it should be flexible enough to support a wide array of possible
rulesets.

The advantage to making the high-level rules JSONable is that you can share
rules with other players without forcing them to download and install new
python modules.


Folder Structure
----------------
    ./open-tactics.py	Engine launcher
    ./LICENSE		GPL
    ./README.md		Basic installation and running instructions
    ./docs/		Design Documents
    	  /design-doc
    ./code/		Python Source Code
          /graphics	SDL+ASCII graphics
	  /core		The core engine (common to all rulesets)
	  /rulesets	A directory where ruleset modules go
	  /server	Play-by-post server









