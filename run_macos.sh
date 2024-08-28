#!/bin/zsh
FOLDER_PATH=$(pwd)
for i in {0..2}
do
    osascript -e "tell app \"Terminal\" to do script \"cd '$FOLDER_PATH' && python3 src/main.py $i\""
done