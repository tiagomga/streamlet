#!/bin/zsh
FOLDER_PATH=$(pwd)
for i in {0..3}
do
    osascript -e "tell app \"Terminal\" to do script \"cd '$FOLDER_PATH' && python3 main.py $i\""
done