#!/bin/sh
FOLDER_PATH=$(pwd)
for i in {0..3}
do
    gnome-terminal -- sh "cd '$FOLDER_PATH' && python3 main.py $i"
done