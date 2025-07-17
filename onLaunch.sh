#!/bin/bash
#sleep 10
export DISPLAY=:0
#cd /home/august/Minotaur
eval "$(ssh-agent -s)"
ssh-add /home/august/.ssh/id_rsa
#. /home/august/.env/bin/activate
source /home/august/.env/bin/activate
python3 -O /home/august/Minotaur/maskDemo.py &

