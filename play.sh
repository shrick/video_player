#!/bin/sh

PLAYER_CMD="python player.py"

. .env/bin/activate

VIDEO_DIR="$1"; shift
$PLAYER_CMD "$VIDEO_DIR" "$@"
