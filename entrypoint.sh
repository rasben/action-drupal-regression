#!/bin/bash
set -e

yes | pip3 install colorama requests validators beautifulsoup4 --quiet --exists-action i

cd drupal-regression
STATUS="fail"
MESSAGE=""
BASE_MESSAGE=""

while IFS= read -r LINE; do
    URL=$(echo $LINE | cut -d " " -f1)
    MESSAGE=$(python compare.py --url="$URL" --verbose=True --markdown=True)

    # If the last part of the message is "STATUSOK".
    if [[ $MESSAGE == *STATUSOK ]]
    then
      BASE_MESSAGE=":robot: :speech_balloon: \`beep-boop. github bot here. just here to say: you're awesome. drupal-regression fixed\` :star_struck: :sunglasses: <br/><br/>"
      STATUS="pass"
    fi

done < './.check-urls'

MESSAGE="$BASE_MESSAGE $MESSAGE"

echo "$MESSAGE"

# Remove newlines, as Github Comments dont like that..
MESSAGE=${MESSAGE//$'\n'/}

echo "::set-output name=message::$MESSAGE"
echo "::set-output name=status::$STATUS"

