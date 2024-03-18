#!/bin/zsh
FOLDER_PATH=$(pwd)
for i in {0..3}
do
    osascript -e "tell app \"Terminal\" to do script \"python3 '$FOLDER_PATH'/main.py $i\""
done