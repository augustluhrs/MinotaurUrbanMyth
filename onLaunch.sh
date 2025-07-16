#!/bin/bash
#onLaunch.sh
cd /home/august/Minotaur
eval "$(ssh-agent -s)"
ssh-add /home/august/.ssh/id_rsa
source /home/august/.env/bin/activate
python3 -O maskDemo.py

