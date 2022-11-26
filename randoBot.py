#!/usr/bin/python3
# randoBot.py
# Simple testing/template robot that takes a random action every turn.
# Literally does not do anything except roll a die for every request.
import os
import random
import argparse
from battleActions import Action, ActionType, Dir
from battler import WORLDSIDELENGTH

# FIXME: need to set up a standalone mode that watches the pipe
# FIXME: need to write a custom Action spec for reflecting the API?

def getNextID(pipe):
	# attempts to read from the pipe until it gets a unit ID
	unitID = 0
	return unitID

def randomXYString():
	xval = random.randrange(0, WORLDSIDELENGTH)
	yval = random.randrange(0, WORLDSIDELENGTH)
	xstr = hex(xval)[2:]
	ystr = hex(yval)[2:]
	xstr = xstr.rjust(2, '0')
	ystr = ystr.rjust(2, '0')
	#print("%   Randobot generated loc {}, {}".format(xval, yval)) # DEBUG
	return xstr + ystr

def randomDirString():
	# UP = 01 00 -> 10
	# DN = 10 00 -> a0
	# LT = 00 01 -> 01
	# RT = 00 10 -> 0a
	# UP + LT = 01 01 -> 11
	# UP + RT = 01 10 -> 1a
	# DN + RT = 10 10 -> aa
	newDir = random.choice(list(Dir))
	if newDir == Dir.NONE:
		return randomDirString()
	newStr = hex(newDir.value)[2:]
	if len(newStr) == 1:
		newStr = newStr.rjust(2, '0')
	#print("%   Randobot generated dir {}({})".format(newDir, newStr)) # DEBUG
	return newStr

def randomAct(unitID):
	# Randomly selects from the set of actions
	result = random.randrange(0, 4)
	# Start with the enum value of the action type
	actionString = hex(result)[2:]
	actionString = actionString.rjust(4, '0')
	# Append the unit ID #
	actionString += unitID
	# Format any params, if needed
	params = list()
	match result:
		case 0:
			# delay - no params
			actionString += '0'
			#print("%   : U-" + str(unitID) + " will delay") # DEBUG
		case 1:
			# scan - no params
			actionString += '0'
			#print("%   : U-" + str(unitID) + " will scan") # DEBUG
		case 2:
			# move - direction
			newDir = randomDirString()
			actionString += newDir
			#print("%   : U-" + str(unitID) + " will move") # DEBUG
		case 3:
			# attack - direction
			newDir = randomDirString()
			actionString += newDir
			#print("%   : U-" + str(unitID) + " will attack") # DEBUG
		case 4:
			# spawn - location
			newLoc = randomXYString()
			actionString += newLoc
			#print("%   : U-" + str(unitID) + " will spawn") # DEBUG
	# FIXME: put togther a parser tool for the string conversion?
	actionString = actionString.ljust(12, '0') # pad with zeroes if too short
	actionString = '0x' + actionString
	return actionString

def spawnAct(unitID):
	# Creates a spawn request
	# does NOT validate!
	spawnReqString = hex(ActionType.SPAWN.value)[2:] # = 0x0004
	spawnReqString = spawnReqString.rjust(4, '0') # prepend zeroes
	spawnReqString = '0x' + spawnReqString
	spawnReqString += unitID
	spawnReqString += randomXYString()
	#print("%   New spawn action created: " + spawnReqString) # DEBUG
	return spawnReqString

def subproc(pipeName):
	# the set of instructions for the forked subprocess
	listUnits = list()
	random.seed()
	keepGoing = True
	currentTurn = 0
	while keepGoing == True:
		# read a unit ID from the pipe
		with open(pipeName, 'r') as inPipe:
			#print("%   {}: Awaiting request".format(pipeName)) # DEBUG
			unitID = inPipe.readline()
			#print("% < {}: unit {} requested new action".format(pipeName, unitID)) # DEBUG
		if unitID not in listUnits:
			#print("%   U-{} not in list, spawning".format(unitID)) # DEBUG
			listUnits.append(unitID)
			newCommand = spawnAct(unitID)
		else:
			# generate a random action for that unit
			newCommand = randomAct(unitID)
		with open(pipeName, 'w') as outPipe:
			#print("% > {}: cmd {} to {}".format(pipeName, newCommand, pipeName)) # DEBUG
			outPipe.write(newCommand)
		with open(pipeName, 'r') as inPipe:
			#print("%   {}: Awaiting return value".format(pipeName)) # DEBUG
			retVal = inPipe.readline() # discard
			#print("% < {}: Obtained retval: {}".format(pipeName, retVal)) # DEBUG
		currentTurn += 1

def main():
	argparser = argparse.ArgumentParser(
			prog='Randobot',
			description='A proof of concept and testing robot',
			epilog='The epilog is the bottom of the help text')
	argparser.add_argument('targetPipe', type=str, help='The filename of the pipe to connect to')
	args = argparser.parse_args()
	procID = os.fork()
	if procID != 0:
		return; # the parent dies
	else:
		subproc(args.targetPipe) # the child remains

if __name__ == "__main__":
	main()
	
# EOF
