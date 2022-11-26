# battleActions.py
# Library file for Python-based battler programs that provides translation
# to/from the arena's bytecode API.
# ! IMPORTANT !
# This file defines the bytecode format
# For a given bytecode,
# 0x0000000000000000...
#   aaaabbbbccddeeff...
# where
#  aaaa    The Action as a hex value (see ActionType enum)
#  = 0000  == ActionType.DELAY (default)
#  bbbb    The id# of the entity performing the Action
#  = 0000  == init by controller, *only* for spawn requests
#  cc, dd, ee, ff, ...
#          Params as 2-digit pairs for the Action
#  = 0000  == zero, false, etc; see action defns
# Note that the 'minimum'/default action would be:
# 0x0000000000
# Which would indicate an attempt by the player to delay;
# however, note that the size of the string is 10 chars:
#  0000 = ActionType.Delay,
#  0000 = id=(player),
#  00   = no params (null)
# Return values are defined by the actions.
#import battler.py
from enum import Enum
from abc import ABC, abstractmethod

class Dir(Enum):
	# Defines the set of directions on the map
	# FIXME: set up a mapping from Dir to x,y pairs
	NONE = 0x00
	UP = 0x10
	DOWN = 0xA0
	LEFT = 0x01
	RIGHT = 0x0A

class ActionType(Enum):
	# Defines the set of actions that Actors may take
	DELAY = 0 # Default, do nothing for one turn
	SCAN = 1 # Reveals neighboring tiles to subject
	MOVE = 2 # Moves subject to new location
	ATTACK = 3 # Strike at a location, attempting to damage a bot
	SPAWN = 4 # Create a new bot at specified location
	# ActionTypes with num > 0x0100 are reserved?

class Action:
	Type = ActionType.DELAY
	Subject = 0x0000 # corr. to the unit's ID

	@abstractmethod
	def Do(self):
		pass

class BattleParser:
	# Provides methods for converting to/from bytecode and Actions
	def ConvertToValues(inputCodeString):
		# Given a hexadecimal string of at least 8 digits,
		# Returns a tuple of values: an ActionType, a unit ID, and addtl params
		# Returns false if there was a problem
		#print("|   :      " + inputCodeString) # DEBUG
		if inputCodeString[:2] == '0x':
			#print("|   Removed hex prefix from code string") # DEBUG
			inputCodeString = inputCodeString[2:]
		if len(inputCodeString) < 8:
			#print("| ! ERR: action input too short to parse: {}".format(inputCodeString)) # DEBUG
			# FIXME: throw exception here prolly?
			return False
		inputCodeString = inputCodeString.ljust(12, '0') # pad with zeroes if too short
		# Slice the whole string up into pieces
		actionString = inputCodeString[:4]
		idString = inputCodeString[4:8]
		paramString = inputCodeString[8:]
		# Convert the part strings
		actionType = ActionType(int(actionString))
		params = list()
		if len(paramString) > 2:
			# Slice params into 2-digit chunks
			n = 0
			p = 2
			keepSlicing = True
			while keepSlicing:
				if p >= len(paramString):
					keepSlicing = False
				params.append(paramString[n:p])
				n += 2
				p = n + 2
		else: # length of paramString <= 2
			params.append(paramString)
		#print("|   : action " + actionString) # DEBUG
		#print("|   : id     " + idString) # DEBUG
		#print("|   : params {}".format(params)) # DEBUG
		return (actionType, idString, params)

	def ConvertToBytecode(inputAction, params):
		# WARNING! This is untested/unused
		# FIXME: There is no definition for the format of params yet
		bytecodeString = ""
		bytecodeString += inputAction.Type.value
		bytecodeString += inputAction.Subject
		for entry in params:
			# Currently, this presumes all params to be Enums with hex value
			# equivalents; this will be improved as use-cases become clear
			bytecodeString += entry
		return bytecodeString

# EOF
