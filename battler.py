#!/usr/bin/python3
# battler.py
# Contains the main driver and components for running the autobattler
# IMPORTS
import sys
import os
import argparse
import random
from enum import Enum
from abc import ABC, abstractmethod
from colorama import Fore, Back, Style

from battleActions import Action, ActionType, Dir, BattleParser

# GLOBALS
WORLDSIDELENGTH = 10
STARTINGHP = 1
MAXDURATION = 10
SPAWNCOUNT = 5

# FIXME: move this debug tool out to a portable drop-in module
VERBOSEMODE = False
def logmsg(*args, **kwargs):
	global VERBOSEMODE
	if VERBOSEMODE == True:
		print(*args, file=sys.stderr, **kwargs)

# CLASSES
class Actor:
	# Defines the minimum reqs for an entity in the arena
	ID: int         # assigned by the engine
	Controller: str # corr. to the pipe of the player that created it
	xPos: int
	yPos: int
	HP: int
	color = Fore.WHITE # see colorama for defn
	def __init__(self, newID, newController, newLocation = (-1, -1), newHP = STARTINGHP, newColor = Fore.WHITE):
		self.ID = newID
		self.Controller = newController
		self.xPos = newLocation[0]
		self.yPos = newLocation[1]
		self.HP = newHP
		self.Color = newColor
		self.LastAction = Engine.DelayAction(self.ID)
		# DEBUG
		if self.Controller == Engine.p1Controller:
			self.Color = Fore.BLUE
		elif self.Controller == Engine.p2Controller:
			self.Color = Fore.GREEN
		# DEBUG-END
		logmsg("*   Actor created: {}:{} @{}, HP: {}".format(self.ID, self.Controller, self.Location(), self.HP)) # DEBUG

	def Location(self):
		return (self.xPos, self.yPos)

class Engine:
	# Defines the system that runs and referees the battle
	TurnCur = 0
	class Mode(Enum):
		OFFLINE = 0
		STARTUP = 1
		RUNNING = 2
		PAUSED = 3
		FINISH = 4
		SHUTDOWN = 5
	State = Mode.OFFLINE
	StatePrev = Mode.OFFLINE
	p1Controller = 'fifo_pipeP1'
	p2Controller = 'fifo_pipeP2'
	outFileName = 'default_out' # FIXME: unspecified output filenames should be timestamps
	ListActionsThisTurn = list()
	ListActors = list()
	ListDead = list()
	DirMap = {
		Dir.UP: (0, 1),
		Dir.DOWN: (0, -1),
		Dir.LEFT: (-1, 0),
		Dir.RIGHT: (1, 0)
	}

	def __init__(self):
		logmsg("*   Initializing game engine") # DEBUG
		self.SetToState(Engine.Mode.STARTUP)

	def SetToState(self, newMode):
		# Helper for setting the engine mode
		self.StatePrev = self.State
		self.State = newMode

	def SetUpComms(self):
		# Sets up the infrastructure between self and the players
		# NOTE that mkfifo only creates the pipes, it does not open them
		logmsg("*   Setting up pipes {} and {}".format(self.p1Controller, self.p2Controller)) # DEBUG
		if not os.path.exists(self.p1Controller):
			os.mkfifo(self.p1Controller)
		if not os.path.exists(self.p2Controller):
			os.mkfifo(self.p2Controller)

	def New_DisplayBattle(self):
		# Better method using python curses to do a crude animation
		import curses
		screen = curses.initscr()
		screen.addstr(0, 0, "my test string")
		# Start the indices at 1 to leave some padding
		yIndex = 1
		xIndex = 2
		topRuler = ""
		topBar = ""
		fieldLine = ""
		for val in range(WORLDSIDELENGTH):
			topRuler += str(val)
		for i in range(len(topRuler)):
			topBar += '|'
		# Add the top rulers to the screen
		screen.addstr(yIndex, xIndex, topRuler)
		yIndex += 1
		xIndex = 2
		screen.addstr(yIndex, xIndex, topBar)
		yIndex += 1
		xIndex = 0
		# Add the battlefield
		for yVal in reversed(range(WORLDSIDELENGTH)):
			#print(str(yVal) + '-', end='')
			fieldLine += str(yVal) + '-'
			for xVal in range(WORLDSIDELENGTH):
				if self.IsOccupied((xVal, yVal)):
					unit = Engine.GetIDAt(xVal, yVal)
					thisController = self.GetControllerOf(unit)
					match thisController:
						case self.p1Controller:
							#print(Fore.BLUE + '@' + Style.RESET_ALL, end='')
							fieldLine += '@'
						case self.p2Controller:
							#print(Fore.GREEN + '@' + Style.RESET_ALL, end='')
							fieldLine += '@'
						case _:
							#print('@', end='')
							fieldLine += '@'
				else:
					#print('┼', end='')
					fieldLine += '┼'
			#print('-' + str(yVal))
			fieldLine += '-' + str(yVal)
			screen.addstr(yIndex, xIndex, fieldLine)
			fieldLine = ""
			yIndex += 1
			xIndex = 0
		# Add the bottom rulers
		xIndex = 2
		screen.addstr(yIndex, xIndex, topBar)
		yIndex += 1
		xIndex = 2
		screen.addstr(yIndex, xIndex, topRuler)
		# Add the unit roster
		# FIXME: put the turncount here
		for guy in self.ListActors:
			nextLine = "U-" + str(guy.ID) + "[" + str(guy.HP) + "] :" + str(guy.xPos) + "," + str(guy.yPos) + ":" + str(guy.LastAction.Type)
			screen.addstr(yIndex, xIndex, nextLine)
			nextLine = ""
			yIndex += 1
			xIndex = 2
		for corpse in self.ListDead:
			nextLine = "D-" + str(corpse.ID) + "[" + str(corpse.HP) + "] :" + str(corpse.xPos) + "," + str(corpse.yPos) + ":" + str(corpse.LastAction.Type)
			screen.addstr(yIndex, xIndex, nextLine)
			nextLine = ""
			yIndex += 1
			xIndex = 2
		xIndex = 2
		screen.addstr(yIndex, xIndex, "  id   HP  x, y  ^last action taken")
		# Need to call .refresh in order to flush the buffer to output
		screen.refresh()
		curses.napms(300)
		curses.endwin()

	def DisplayBattle(self):
		# Pretty-prints the battlefield to stdout
		# prototype for "live mode" later on
		# the colorama module supplies Fore, Back, Style, useable like so:
		# print(Fore.RED + 'this is red text')
		# print(Back.GREEN + 'and now with a green background')
		# print(Style.DIM + 'and in dim text')
		# print(Style.RESET_ALL, 'back to normal')
		# FIXME: can't seem to use the colors if they are stored in vars?
		print("----TURN #{}----".format(str(self.TurnCur)))
		topRuler = "  "
		topBar = "  "
		for val in range(WORLDSIDELENGTH):
			topRuler += str(val)
		print(topRuler)
		for i in range(len(topRuler) - 2):
			topBar += '|'
		print(topBar)
		for yVal in reversed(range(WORLDSIDELENGTH)):
			#row = str(yVal)
			print(str(yVal) + '-', end='')
			for xVal in range(WORLDSIDELENGTH):
				if self.IsOccupied((xVal, yVal)):
					unit = Engine.GetIDAt(xVal, yVal)
					#glyphColor = Engine.GetColor(unit)
					thisController = self.GetControllerOf(unit)
					match thisController:
						case self.p1Controller:
							print(Fore.BLUE + '@' + Style.RESET_ALL, end='')
						case self.p2Controller:
							print(Fore.GREEN + '@' + Style.RESET_ALL, end='')
						case _:
							print('@', end='')
				else:
					print('┼', end='')
			print('-' + str(yVal))
		print(topBar)
		print(topRuler)
		# print a list of all the living actors
		for guy in self.ListActors:
			match guy.Controller:
				case self.p1Controller:
					print(Fore.BLUE, end='')
				case self.p2Controller:
					print(Fore.GREEN, end='')
			print("U-{}[{}] :{},{}:{}".format(guy.ID, guy.HP, guy.xPos, guy.yPos, guy.LastAction.Type))
		for corpse in self.ListDead:
			print(Fore.WHITE + Style.DIM, end='')
			print("U-{}[{}] :{},{}:{}".format(corpse.ID, corpse.HP, corpse.xPos, corpse.yPos, corpse.LastAction.Type))
		print(Style.RESET_ALL + "  id   HP  x, y  ^last action taken")

	@classmethod
	def GetNewIDNum(self):
		# Generates ID numbers in the range [0, 0xFFFF)
		# Additionally checks to ensure there are no ID number clashes
		idStr = hex(random.randrange(0xFFFF))
		for unit in self.ListActors:
			if idStr == unit.ID:
				idStr = self.GetNewIDNum()
		idStr = idStr[2:].rjust(4, '0')
		return idStr

	@classmethod
	def CreateUnit(self, controller, location):
		# System method for creating new units
		logmsg("*   Creating new unit under {} at {}".format(controller, location)) # DEBUG
		newID = Engine.GetNewIDNum()
		newUnit = Actor(newID, controller, location)
		self.ListActors.append(newUnit)
		logmsg("*   U-{}:{} created at {}".format(newID, controller, location)) # DEBUG
		return newUnit.ID

	@classmethod
	def IsOccupied(self, location):
		# Given a specified tuple (x, y),
		# is there a unit that occupies those coordinates?
		flag = False
		for unit in self.ListActors:
			if unit.xPos == location[0] and unit.yPos == location[1]:
				flag = True
		return flag

	@classmethod
	def GetColor(self, target):
		# Untested
		for unit in self.ListActors:
			if unit.ID == target:
				return unit.Color
		return Fore.WHITE

	def KillUnit(self, target):
		# Not working, opted for safer in-place method
		for index in range(len(self.ListActors)):
			if self.ListActors[index].ID == target:
				self.ListActors.pop(index)
				logmsg("* x U-{} has died".format(target))
			else:
				logmsg("* ! Did not find target for culling...")

	def ExecuteGameLoop(self, duration, startingSize):
		# Runs the game loop from start to finish
		for round in range(duration + 1): # add one to cover the zeroth-round of setup
			match self.State:
				case Engine.Mode.OFFLINE:
					logmsg("*!! ERR: Engine is offline") # DEBUG
					return
				case Engine.Mode.STARTUP:
					logmsg("*   Starting up game") # DEBUG
					self.SetupBattle(startingSize) # Spawn the starting units
					self.SetToState(Engine.Mode.RUNNING)
					continue
				case Engine.Mode.RUNNING:
					logmsg("*---TURN " + str(self.TurnCur)) # DEBUG
					# Check whether the battle should end
					if self.IsBattleOver():
						self.SetToState(Engine.Mode.FINISH)
					else:
						self.IterateBattle()
					continue
				case Engine.Mode.PAUSED:
					logmsg("*   Game has been paused") # DEBUG
					# FIXME: causes loop lock without a way to trap input
					# FIXME: good thing there's no way to get here...?
					continue
				case Engine.Mode.FINISH:
					logmsg("*   The battle has ended") # DEBUG
					# FIXME: display battle outcomes if requested
					self.SetToState(Engine.Mode.SHUTDOWN)
					continue
				case Engine.Mode.SHUTDOWN:
					logmsg("*   The game engine will now shut down") # DEBUG
					self.Cleanup()
					return

	def IterateBattle(self):
		# Performs a single round of battle
		logmsg("*   Iterating again") # DEBUG
		if self.State == Engine.Mode.SHUTDOWN:
			logmsg("*!! ERR: Attempting to iterate during shutdown!") # DEBUG
			return
		for unit in self.ListActors:
			logmsg("*   Requesting next action for U-{}".format(unit.ID)) # DEBUG
			actionVals = self.GetNextActionFor(unit)
			# 0=type, 1=subject, 2=params
			nextAction = self.BuildActionFrom(actionVals[0], unit.ID, actionVals[2])
			unit.LastAction = nextAction
			self.ListActionsThisTurn.append(nextAction)
			result = self.ListActionsThisTurn[-1].Do() # The action is not removed until recorded
			with open(unit.Controller, "w") as outputPipe: # Send retval to the controller
				logmsg("* > {}: returning {}".format(unit.Controller, str(result)))
				outputPipe.write(str(result))
		logmsg("*   All units have acted; checking for dead...")
		deadActors = list(filter(lambda unit: unit.HP <= 0, self.ListActors))
		if len(deadActors) > 0:
			logmsg("*   Culling...")
			for target in deadActors:
				self.ListDead.append(target)
				self.ListActors.remove(target)
		logmsg("*   Next turn beginning")
		#self.DisplayBattle()
		self.New_DisplayBattle()
		# FIXME: Use pop() to write each action out to a gameplay record
		# instead of just wiping the list
		#while len(self.ListActionsThisTurn) > 0:
			#self.Record(self.ListActionsThisTurn.pop(0))
		self.ListActionsThisTurn.clear()
		self.TurnCur += 1 # *Always* the last action of this method

	def BuildActionFrom(self, actionType, actionUnitID: int, actionParams) -> Action:
		# Create an Action of the correct type
		# The class Action has only a Type(ActionType) and a Subject(hex string)
		logmsg("*   Building action: t:{}, u:{}, p:{}".format(actionType, actionUnitID, actionParams)) # DEBUG
		match actionType:
			case ActionType.DELAY: # = 0
				newAction = self.DelayAction(actionUnitID)
			case ActionType.SCAN: # = 1
				newAction = self.ScanAction(actionUnitID)
			case ActionType.MOVE: # = 2
				direction = Dir(int(actionParams[0], base=16))
				newAction = self.MoveAction(actionUnitID, direction)
			case ActionType.ATTACK: # = 3
				direction = Dir(int(actionParams[0], base=16))
				newAction = self.AttackAction(actionUnitID, direction)
			case ActionType.SPAWN: # = 4
				# FIXME: add sanity checking for the spawn location
				location = (int(actionParams[0]), int(actionParams[1]))
				newAction = self.SpawnAction(actionUnitID, location)
		# FIXME: need to make sure there is a Null value of ActionType
		return newAction

	@classmethod
	def GetControllerOf(self, unitID):
		# Gets the controller (pipe name) of the specified unit
		for unit in self.ListActors:
			if unit.ID == unitID:
				return unit.Controller
		return ""

	@classmethod
	def GetIDAt(self, xVal, yVal):
		# Gets the ID of a unit at a given coordinate
		for unit in self.ListActors:
			if unit.xPos == xVal and unit.yPos == yVal:
				return unit.ID
		return False

	@classmethod
	def GetLocation(self, target):
		# Returns the grid coordinates of the target
		for unit in self.ListActors:
			if unit.ID == target:
				return (unit.xPos, unit.yPos)
		# Could not find in the list
		return (-1, -1)

	@classmethod
	def SetLocation(self, target, newLocation):
		# Moves target to specified absolute coordinates
		for unit in self.ListActors:
			if unit.ID == target:
				unit.xPos = newLocation[0]
				unit.yPos = newLocation[1]
				return (unit.xPos, unit.yPos)
		# Could not find in the list
		return (-1, -1)

	@classmethod
	def AdjustHP(self, target, offset):
		# Adjust HP of a single unit by the given offset
		for unit in self.ListActors:
			if unit.ID == target:
				unit.HP += offset
				return unit.HP
		return -1

	def Record(self, nextAction):
		# Writes an action line to the output file
		#csvwriter.writerow((nextAction.Type, nextAction.Subject, nextAction.params))
		pass

	def SetupBattle(self, armySize):
		# Creates the starting units
		for index in range(armySize):
			self.ListActors.append(Actor(self.GetNewIDNum(), self.p1Controller))
			self.ListActors.append(Actor(self.GetNewIDNum(), self.p2Controller))

	def GetNextActionFor(self, target):
		# Requests action values for a given unit
		# Calls the controller pipe from the specified unit
		logmsg("* > {} -> U-{}".format(target.Controller, target.ID)) # DEBUG
		# Start by notifying the player of the waiting unit:
		with open(target.Controller, "w") as outputPipe:
			outputPipe.write(str(target.ID))
		# As per API, target controller should respond with a move/spawn req:
		with open(target.Controller, "r") as inputPipe:
			for bytecode in inputPipe:
				logmsg("* < {} <- {}".format(target.Controller, bytecode)) # DEBUG
				if len(bytecode) == 0:
					logmsg("* ! {} closed at other end".format(target.Controller)) # DEBUG
					break
			logmsg("*   Parsing new action")
			# FIXME: is there a null value i can set for the variable 'bytecode'?
			newValues = BattleParser.ConvertToValues(bytecode)
			logmsg("*   Values obtained:", newValues) # DEBUG
		return newValues

	def IsBattleOver(self):
		# Simple boolean helper for checking the ongoing battle state
		if self.TurnCur >= MAXDURATION:
			return True
		if len(self.ListActors) <= 1:
			return True
		return False

	def Cleanup(self):
		# Runs manual cleanup procedures: pipe deletion, &c
		if os.path.exists(self.p1Controller):
			os.remove(self.p1Controller)
		if os.path.exists(self.p2Controller):
			os.remove(self.p2Controller)

	# ACTIONS
	class DelayAction(Action):
		Type = ActionType.DELAY
		
		def __init__(self, newSubject):
			self.Subject = newSubject
		
		def Do(self):
			# enjoy ur break
			logmsg("*   U-{}: Do.DELAY".format(self.Subject)) # DEBUG
			return True

	class ScanAction(Action):
		Type = ActionType.SCAN

		def __init__(self, newSubject):
			self.Subject = newSubject

		def Do(self):
			# give the subject an image of the neighboring tiles
			#return TileString
			logmsg("*   U-{}: Do.SCAN".format(self.Subject)) # DEBUG
			# FIXME: this is just a stub, the return value is undecided
			return True

	class MoveAction(Action):
		Type = ActionType.MOVE
		Direction = (-1, -1)

		def __init__(self, newSubject, newDirection):
			self.Subject = newSubject
			self.Direction = Engine.DirMap[newDirection]

		def Do(self):
			#posnCurrent = Engine.GetLocation(self.Subject)
			oldX, oldY = Engine.GetLocation(self.Subject)
			offX, offY = self.Direction
			newX = oldX + offX
			newY = oldY + offY
			logmsg("*   U-{}: Do.MOVE from {} to {}".format(self.Subject, (oldX, oldY), (newX, newY))) # DEBUG
			if newX >= WORLDSIDELENGTH or newY >= WORLDSIDELENGTH or newX < 0 or newY < 0:
				# New position is out of bounds, don't move
				return (oldX, oldY)
			if Engine.IsOccupied((newX, newY)):
				return (oldX, oldY)
			result = Engine.SetLocation(self.Subject, (newX, newY))
			return (newX, newY)

	class AttackAction(Action):
		Type = ActionType.ATTACK
		Direction = Dir.NONE
		DirOffset = (-1, -1)

		def __init__(self, newSubject, newDirection):
			self.Subject = newSubject
			self.Direction = newDirection
			self.DirOffset = Engine.DirMap[newDirection]

		def Do(self):
			result = False
			logmsg("*   U-{}: Do.ATTACK to {}".format(self.Subject, self.Direction)) # DEBUG
			# get the location of the subject
			oldX, oldY = Engine.GetLocation(self.Subject)
			offX, offY = self.DirOffset
			# combine w/ direction to get target location
			newX = oldX + offX
			newY = oldY + offY
			if Engine.IsOccupied((newX, newY)): # if target location contains a robot,
				target = Engine.GetIDAt(newX, newY)
				result = Engine.AdjustHP(target, -1) # then that robot loses 1 pt hp
				logmsg("*   U-{}: Successful attack on U-{}".format(self.Subject, target))
			return result # otherwise return false

	class SpawnAction(Action):
		# To use this, the Engine should have already generated an ID number
		# for the new actor; the Action merely places the unit on the board at
		# the specified location.
		# That is, this is an Action generated in response to the Engine
		# allocating a new unit to a player
		Type = ActionType.SPAWN
		Location = (0, 0)

		def __init__(self, target, newLocation):
			self.Subject = target # corr. to team ID
			self.Location = newLocation

		def Do(self):
			# Move the premade unit to the board
			logmsg("*   U-{}: Do.SPAWN at {}".format(self.Subject, self.Location)) # DEBUG
			result = Engine.SetLocation(self.Subject, self.Location)
			return result

def main():
	# This is where the main stuff goes
	argparser = argparse.ArgumentParser(prog='battler.py',
			description='Conducts a swarm robot fight in a virtual space.',
			epilog='[The epilog var contains the text at the bottom of the help.]')
	#argparser.add_argument('playerOne', type=str, nargs=1,
			#help='The path to the executable of the first player program')
	#argparser.add_argument('playerTwo', type=str, nargs=1,
			#help='The path to the executable of the second player program')
	argparser.add_argument('--pipe1', '-p1', type=str, nargs=1,
			help='The path to the named pipe for the first player.')
	argparser.add_argument('--pipe2', '-p2', type=str, nargs=1,
			help='The path to the named pipe for the second player.')
	argparser.add_argument('--size', '-s', type=int, default=SPAWNCOUNT,
			help='The number of units to spawn at battle start.')
	argparser.add_argument('--time', '-t', type=int, default=MAXDURATION,
			help='The maximum number of rounds to allow in the battle.')
	argparser.add_argument('--verbose', '-v', action='store_true', default=False,
			help='Display debugging output.')
	args = argparser.parse_args()
	engine = Engine()
	if args.pipe1 is not None:
		engine.p1Controller = str(args.pipe1[0])
	if args.pipe2 is not None:
		engine.p2Controller = str(args.pipe2[0])
	if args.verbose is True:
		global VERBOSEMODE
		VERBOSEMODE = True
	duration = args.time
	spawnQty = args.size
	# *** FIXME: Logic for invoking the player programs at engine runtime
	#engine.SetUpComms() # FIXME: this is a stupid method
	#p1Invocation = args.playerOne[0] + ' ' + engine.p1Controller
	#p2Invocation = args.playerTwo[0] + ' ' + engine.p2Controller
	#logmsg("*   Starting first player: " + p1Invocation) # DEBUG
	#os.system(p1Invocation)
	#logmsg("*   Starting second player: " + p2Invocation) # DEBUG
	#os.system(p2Invocation)
	# ***
	engine.ExecuteGameLoop(duration, spawnQty)

if __name__ == "__main__":
	main()

#EOF
