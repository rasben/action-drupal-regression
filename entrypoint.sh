#!/bin/bash
set -e

STATUS="fail"
MESSAGE=""
BASE_MESSAGE="drupal-regression <br/><br/>"

while IFS= read -r LINE; do
    URL=$(echo $LINE | cut -d " " -f1)
    MESSAGE=$(python /src/compare.py --url="$URL" --verbose=True --markdown=True --workdir="$INPUT_WORK_DIR")

    # If the last part of the message is "STATUSOK".
    if [[ $MESSAGE == *STATUSOK ]]
    then
      BASE_MESSAGE=":robot: :speech_balloon: \`you're awesome. drupal-regression fixed\` :star_struck: :sunglasses: <br/><br/>![good job](https://media4.giphy.com/media/XreQmk7ETCak0/giphy.gif?cid=ecf05e47prkmsjnp3szelwf0gsc37q5j0qdnjr10688fqqtv&rid=giphy.gif&ct=g)"
      STATUS="pass"
    fi

done < $INPUT_URLS

MESSAGE="$BASE_MESSAGE $MESSAGE"

echo "$MESSAGE"

# Remove newlines, as Github Comments dont like that..
MESSAGE=${MESSAGE//$'\n'/}

echo "::set-output name=message::$MESSAGE"
echo "::set-output name=status::$STATUS"

