#!/bin/bash
p1pipe="P1_fifo"
p2pipe="P2_fifo"
[ -e $p1pipe ] && rm $p1pipe
[ -e $p2pipe ] && rm $p2pipe
mkfifo $p1pipe
mkfifo $p2pipe
randoBot.py $p1pipe
randoBot.py $p2pipe
battler.py -p1 $p1pipe -p2 $p2pipe -v -t 20
pkill randoBot
