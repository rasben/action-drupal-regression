#!/bin/bash
set -e

STATUS="fail"
MESSAGE=""
BASE_MESSAGE="drupal-regression <br/><br/>"

echo "$INPUT_URL"

MESSAGE=$(python /src/compare.py --url="$INPUT_URL" --verbose=True --markdown=True --workdir="$INPUT_WORK_DIR")

# If the message contains STATUSOK.
if [[ $MESSAGE == *STATUSOK* ]]
then
  BASE_MESSAGE=":robot: :speech_balloon: \`drupal-regression is OK\` :+1: <br/>"
  SIDE_MESSAGE="![good job](https://media4.giphy.com/media/XreQmk7ETCak0/giphy.gif?cid=ecf05e47prkmsjnp3szelwf0gsc37q5j0qdnjr10688fqqtv&rid=giphy.gif&ct=g)"
  STATUS="pass"
fi

MESSAGE="$BASE_MESSAGE $MESSAGE"

echo "$MESSAGE"

# Remove newlines, as Github Comments dont like that..
MESSAGE=${MESSAGE//$'\n'/}

GITHUB_MESSAGE="|   |   |%0D%0A|---|---|%0D%0A|$MESSAGE|$SIDE_MESSAGE|%0D%0A"

echo "$GITHUB_MESSAGE"

echo "::set-output name=message::$GITHUB_MESSAGE"
echo "::set-output name=status::$STATUS"
