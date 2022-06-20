from pathlib import Path
from bs4 import BeautifulSoup as bs
import json
import requests
import shutil
import os
import sys
import argparse
import difflib
import requests
import validators

def validateJSON(jsonData):
    try:
        json.loads(jsonData)
    except ValueError as err:
        return False
    return True

# Comparing existing baseline, with values presented
# by the drupal_regression content API.
def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--url', help='The URL to check against. Defaults to local.docker')
  parser.add_argument('--contentdir', help='Where the regressions will be generated. Defaults to "content"')
  parser.add_argument('--verbose', help='Display more info about diff. Defaults to False')
  parser.add_argument('--markdown', help='Display as Markdown safe values.')
  parser.add_argument('--failexit', help='Exit when failing.')

  args = parser.parse_args()

  # Applying a fallback to the URL parameter.
  url = args.url

  if (url == None):
    url = "http://local.docker"
  else:
    valid_url = validators.url(url)

    if (valid_url != True):
      url = "http://local.docker"

  api_url = url + "/api/regression/content/all"

  # Applying a fallback to the contentdir parameter.
  contentdir = args.contentdir

  if (contentdir == None):
    contentdir = 'content'

  # Setting the other parameters, with fallbacks.
  failexit = args.failexit

  if (failexit == None):
    failexit = False

  verbose = args.verbose

  if (verbose == None):
    verbose = False

  # Setting txtmod as variables - so we can easily
  # do different text-styling.
  class txtmod:
      HEADER = ''
      OKBLUE = ''
      OKCYAN = ''
      OKGREEN = ''
      WARNING = ''
      FAIL = ''
      ENDC = ''
      BOLD = '**'
      ENDBOLD = '**'
      UNDERLINE = '<ins>'
      ENDUNDERLINE = '</ins>'
      NEWLINE = '<br />'
      ENCODED_NEWLINE = '%0D%0A'
      CODE = '```'
      CODEEND = '```'


  # If the response should be markdown safe, we update
  # the txtmod to reflect this.
  markdown = args.markdown
  markdown_safe = True

  if (markdown == None):
    class txtmod:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        ENDBOLD = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        ENDUNDERLINE = '\033[0m'
        NEWLINE = '\r\n'
        ENCODED_NEWLINE = ''
        CODE = '  '
        CODEEND = ''

    markdown_safe = False

  return_message = ""

  content_dir = Path(contentdir)

  # If no content has already been generated, we have
  # nothing to compare against, and we'll quit.
  if not content_dir.exists() or not content_dir.is_dir():
      return_message += "No local content baseline." + txtmod.NEWLINE

      if (failexit):
        sys.exit(return_message)

      return_message += "STATUSERROR"
      print(return_message)

      return return_message

  # Loading the API endpoint from Drupal.
  api = requests.get(api_url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}, timeout=15)

  # Making sure the JSON is valid.
  if not validateJSON(api.content):
    return_message += "Could not find any valid json at " + api_url + txtmod.NEWLINE

    if (failexit):
      sys.exit(return_message)

    return_message += "STATUSERROR"
    print(return_message)

    return return_message

  api_data = json.loads(api.content)

  diffs = []

  # Removing our temporary baseline directory if it already exists.
  baseline_dir = Path(contentdir + '/baseline')
  if baseline_dir.exists() and baseline_dir.is_dir():
      shutil.rmtree(baseline_dir)

  # Re-creating the baseline directory.
  os.mkdir(str(baseline_dir))

  # Looping through the generated content in content_dir,
  # and comparing each file with the relevant content API endpoint.
  for file_name in os.listdir(str(content_dir)):
      # If the file name exists in the endpoint, we'll load
      # the HTML from the endpoint, prettify it, and run a diff.
      # If there is a diff, we'll run through every diff and generate
      # an output similar to `git diff`.
      if file_name in api_data['endpoints']:
          endpoint_url = url + api_data['endpoints'][file_name]['url']

          response = requests.get(endpoint_url)

          baseline_local_path = str(baseline_dir) + "/" + file_name

          pretty_html = bs(response.content, 'html.parser').prettify()

          open(baseline_local_path, "w").write(pretty_html)

          diff_local_path = str(content_dir.joinpath(file_name))

          with open(baseline_local_path) as baseline_file:
              baseline_lines = baseline_file.readlines()

          with open(diff_local_path) as diff_file:
              diff_lines = diff_file.readlines()

          diff = difflib.unified_diff(
                                 diff_lines, baseline_lines, fromfile=diff_local_path,
                                 tofile=baseline_local_path, lineterm='')

          _exhausted = object()

          if (next(diff, _exhausted) is not _exhausted):
            diffs.append(file_name)
            if (verbose):
              # If the response has to be markdown safe, we need to add
              # a codeblock indicator.
              if (markdown_safe):
                return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE + ' ```diff ' + txtmod.ENCODED_NEWLINE
                return_message += txtmod.ENCODED_NEWLINE
                return_message += txtmod.ENCODED_NEWLINE


              # Find and print the diff.
              for line in diff:
                  return_message += txtmod.ENCODED_NEWLINE
                  if (line.startswith('+')):
                    return_message += txtmod.OKGREEN + line + txtmod.ENDC
                  elif (line.startswith('-')):
                    return_message += txtmod.FAIL + line + txtmod.ENDC
                  elif (line.startswith('^')):
                    return_message += txtmod.OKBLUE + line + txtmod.ENDC
                  else:
                    return_message += line

              # Closing the codeblock indicator.
              if (markdown_safe):
                return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE
                return_message += ' ``` '
                return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE + txtmod.NEWLINE

      # If the file cant be found in the endpoint list, we
      # must assume that the file has been deleted.
      else:
          diffs.append(file_name + " has been deleted.")

  # Lines below basically just presents the results.
  return_message += txtmod.NEWLINE + txtmod.BOLD + "After checking " + txtmod.OKCYAN + url + txtmod.ENDBOLD + txtmod.ENDC + " the verdict is..." + txtmod.NEWLINE

  failed = False

  if api_data['messages']['errors']:
    return_message += txtmod.BOLD + txtmod.UNDERLINE + "Encountered errors:" + txtmod.ENDBOLD + txtmod.ENDUNDERLINE + txtmod.NEWLINE + txtmod.NEWLINE

    for error in api_data['messages']['errors']:
      return_message += "  - " + txtmod.FAIL + error + txtmod.ENDC + txtmod.NEWLINE
    failed = True

  if diffs:
    return_message += txtmod.BOLD + txtmod.UNDERLINE + txtmod.NEWLINE + "Found diffs in following files:" + txtmod.ENDBOLD + txtmod.ENDUNDERLINE + txtmod.NEWLINE

    for diff in diffs:
      return_message += txtmod.NEWLINE + "  - " + txtmod.WARNING + diff + txtmod.ENDC

    if not verbose:
      return_message += txtmod.NEWLINE + txtmod.NEWLINE + txtmod.BOLD + txtmod.UNDERLINE + "You can see the full diff by running:" + txtmod.NEWLINE + txtmod.NEWLINE + txtmod.ENDBOLD + txtmod.ENDUNDERLINE
      return_message += txtmod.OKBLUE + txtmod.CODE + "docker-compose exec web sh -c \"cd /var/www/ && (cd drupal-regression && python3 compare.py --url=" + url + " --verbose=True" + ")\"" + txtmod.CODEEND + txtmod.ENDC + txtmod.NEWLINE + txtmod.NEWLINE

    return_message += txtmod.NEWLINE + txtmod.NEWLINE + txtmod.BOLD + txtmod.UNDERLINE + "If the changes are correct, you can commit the changes after running:" + txtmod.NEWLINE + txtmod.NEWLINE + txtmod.ENDBOLD + txtmod.ENDUNDERLINE
    return_message += txtmod.OKBLUE + txtmod.CODE + "docker-compose exec web sh -c \"cd /var/www/ && (cd drupal-regression && python3 generate-baseline.py --url=" + url + ")\"" + txtmod.ENDC + txtmod.CODEEND + txtmod.NEWLINE + txtmod.NEWLINE

    if (failexit):
      sys.exit(return_message)

    return_message += "STATUSFAIL"

    failed = True

  # If we have experienced no issues, we'll inform the user that all's good, and set
  # a STATUSOK that GithubActions can understand.
  if failed:
    return_message += txtmod.BOLD + txtmod.OKGREEN + "No diffs or errors encountered :)" + txtmod.ENDBOLD + txtmod.ENDC + txtmod.NEWLINE + txtmod.NEWLINE
    return_message += "STATUSOK"

  # Printing the final message.
  print(return_message)
  return return_message

main()
