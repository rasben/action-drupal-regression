from pathlib import Path
from bs4 import BeautifulSoup as bs
import requests
import shutil
import os
import argparse
import json
import requests
import validators

def validateJSON(jsonData):
    try:
        json.loads(jsonData)
    except ValueError as err:
        return False
    return True

# Generating a new baseline, based on the drupal_regression API.
def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--url', help='The URL to generate from. Defaults to local.docker')

  args = parser.parse_args()

  url = args.url

  valid_url = validators.url(url)

  if (url == None or valid_url != True):
    url = "http://local.docker"

  content_dir = Path('content')
  if content_dir.exists() and content_dir.is_dir():
      shutil.rmtree(content_dir)

  os.mkdir(str(content_dir))

  class txtmod:
      HEADER = '\033[95m'
      OKBLUE = '\033[94m'
      OKCYAN = '\033[96m'
      OKGREEN = '\033[92m'
      WARNING = '\033[93m'
      FAIL = '\033[91m'
      ENDC = '\033[0m'
      BOLD = '\033[1m'
      UNDERLINE = '\033[4m'

  return_message = "\r\n"

  api = requests.get(url + "/api/regression/content/all", headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}, timeout=15)

  if not validateJSON(api.content):
    return_message += "Could not find any valid json at " + api_url + txtmod.NEWLINE
    return_message += "STATUSERROR"
    print(return_message)
    return return_message

  api_data = json.loads(api.content)

  return_message += txtmod.BOLD + txtmod.UNDERLINE + "From " + txtmod.OKCYAN + url + txtmod.ENDC + txtmod.BOLD + txtmod.UNDERLINE + " these files were found and generated:" + txtmod.ENDC + "\r\n"

  for endpoint in api_data['endpoints']:
    file_name = api_data['endpoints'][endpoint]['file']
    return_message += "\r\n  - " + txtmod.OKGREEN + file_name + txtmod.ENDC

    endpoint_url = url + api_data['endpoints'][endpoint]['url']

    response = requests.get(endpoint_url)
    pretty_html = bs(response.content, 'html.parser').prettify()

    open(str(content_dir) + "/" + file_name, "w").write(pretty_html)

  return_message += "\r\n\r\n"

  if api_data['messages']['warnings']:
    return_message +=txtmod.BOLD + txtmod.UNDERLINE + "Encountered warnings:" + txtmod.ENDC + "\r\n"

    for warning in api_data['messages']['warnings']:
      return_message += "\r\n  - " + txtmod.WARNING + warning + txtmod.ENDC

  if api_data['messages']['errors']:
    return_message += "\r\n\r\n" + txtmod.BOLD + txtmod.UNDERLINE + "Encountered errors:" + txtmod.ENDC + "\r\n"

    for error in api_data['messages']['errors']:
      return_message += "\r\n  - " + txtmod.FAIL + error + txtmod.ENDC

  return_message += "\r\n"
  print(return_message)
  return return_message

main()
