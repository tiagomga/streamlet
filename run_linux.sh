#!/bin/sh
FOLDER_PATH=$(pwd)
for i in {0..3}
do
    gnome-terminal -- sh "python3 $FOLDER_PATH/main.py $i"
done