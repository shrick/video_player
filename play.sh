#!/bin/sh

PLAYER_CMD="python player.py"
ABORT_CODE=42

. .env/bin/activate

VIDEO_DIR="$1"; shift
$PLAYER_CMD "$VIDEO_DIR" -a $ABORT_CODE "$@"
if [ $? -eq $ABORT_CODE ]; then
    echo "Aborted ($ABORT_CODE)"
fi