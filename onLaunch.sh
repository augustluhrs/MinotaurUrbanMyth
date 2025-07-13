#!/bin/sh
#onLaunch.sh
cd ~/Minotaur
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa
source ~/.env/bin/activate
python3 -O maskDemo.py

