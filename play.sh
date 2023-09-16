#!/bin/sh

PLAYER_CMD="python player.py"
ABORT_CODE=23

. .env/bin/activate

VIDEO_DIR="$1"; shift
find "$VIDEO_DIR" -type f | sort | while read f; do
    $PLAYER_CMD "$f" "$@"
    if [ $? -eq $ABORT_CODE ]; then
        echo Aborting...
        break
    fi
done
