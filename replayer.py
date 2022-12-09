#!/usr/bin/python3
# replayer.py
# Handles (re)playing of battler output files
# Can be invoked standalone with an output file for a demo mode, or as part of
# the battler for a "live" playback of the battle
# HEX FORMAT
# 0x0000 0000 [0000...]
#   actn unit [params]
# The CSV will follow the same ordering and use the same values

# IMPORTS
import argparse
import curses
import magic
import os
from collections import deque
from enum import Enum
#from colorama import Fore, Back, Style

from battleActions import Dir, ActionType, Action
from battler import logmsg

animationSpeed = 1.0

class AnimType(Enum):
	# NOTE: python won't let me extend this using ActionType instead of Enum?
	# Defines the set of animation activities
	# Unit activities
	DELAY = 0
	SCAN = 1
	MOVE = 2
	ATTACK = 3
	SPAWN = 4
	# ... up to 255 (0x00FF); 0x0100 separates unit and meta activities
	# Meta activities
	DIE = 0x0101 # dec 257, used to animate a unit's death

class Animation():
	# Defines individual animations
	# An Animation is meant to be attached to an Actor
	animType = AnimType.DELAY
	frames = deque()

class VirtuaPrinter:
	def Parse(self):
		# Parses the given line of CSV into the internal defn
		pass

	def Display(self):
		# Displays the current state of the battle on-screen
		pass

	class Actor:
		# Display prop for attaching animations to
		animation = AnimType.DELAY
		xPos = 0
		yPos = 0

		def perform(self):
			# Performs an animation based on the current action
			pass

def main():
	# Throw an error if an input was not given
	argparser = argparse.ArgumentParser(prog='replayer.py',
			description='Plays back an output file from the robot battler.')
	argparser.add_argument('file', type=str,
			help='The path of the output file to be played back.')
	args = argparser.parse_args()
	if args.file is None:
		print("No output file was specified. Exiting.")
		return
	inputPath = str(args.file)
	# Make sure the file exists
	if os.path.exists(inputPath) is False:
		print("'{}' file does not exist. Exiting.".format(inputPath))
		return
	# Make sure the file is a csv
	filetype = magic.from_file(inputPath)
	if 'csv' not in filetype:
		print("'{}' is not a valid CSV file. Exiting.".format(inputPath))
	# Process the file:
	#	For each line in the output file:
	#		convert the line to an internal action
	#		put the action onto the playback stack
	#	For each action on the stack:
	#		execute the given action


if __name__ == "__main__":
	main()

# EOF
