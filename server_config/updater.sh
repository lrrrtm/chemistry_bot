#!/bin/bash

cd /home/lartem/repos/chemistry_bot

source /home/lartem/repos/chemistry_bot/venv/bin/activate

git pull origin master

pip install -r requirements.txt

sudo systemctl restart chemistry_bot.service
sudo systemctl restart chemistry_stats.service
#sudo systemctl restart chemistry_control.service