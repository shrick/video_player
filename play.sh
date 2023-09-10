#!/bin/sh

PLAYER_CMD="python player.py"
PLAYER_TITLE="Zu Annas 18. Geburtstag"
ABORT_CODE=23

. .env/bin/activate

VIDEO_DIR="$1"; shift
find "$VIDEO_DIR" -type f | while read f; do
    $PLAYER_CMD "$f" -t "$PLAYER_TITLE" "$@"
    if [ $? -eq $ABORT_CODE ]; then
        echo Aborting...
        break
    fi
done
