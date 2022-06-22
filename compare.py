from pathlib import Path
import json
import requests
import shutil
import os
import sys
import argparse
import difflib
import requests
import validators
import tidylib

tidylib.BASE_OPTIONS = {}

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
  parser.add_argument('--verbose', help='Display more info about diff. Defaults to False')
  parser.add_argument('--markdown', help='Display as Markdown safe values.')
  parser.add_argument('--failexit', help='Exit when failing.')
  parser.add_argument('--workdir', help='The dir to create content checks.')

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
    CODE = ' ``` '
    CODEEND = ' ``` '
    CODEDIFF = ' ```diff '


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
      ENCODED_NEWLINE = '\r\n'
      CODE = ' '
      CODEEND = ' '

    markdown_safe = False

  return_message = ""

  work_dir_string = args.workdir

  if (work_dir_string == None):
    work_dir_string = 'drupal-regression'


  work_dir = Path(work_dir_string)

  # Create work folder if it doesnt exist.
  # This should only be the case the first time we run this.
  if not work_dir.exists() or not work_dir.is_dir():
    os.mkdir(str(work_dir))

  content_dir = Path(str(work_dir) + '/content')

  # Create content folder if it doesnt exist.
  # This should only be the case the first time we run this.
  if not content_dir.exists() or not content_dir.is_dir():
    os.mkdir(str(content_dir))

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
  baseline_dir = Path(str(work_dir) + '/baseline')
  if baseline_dir.exists() and baseline_dir.is_dir():
    shutil.rmtree(baseline_dir)

  # Re-creating the baseline directory.
  os.mkdir(str(baseline_dir))

  generate_commands = []
  html_errors = []

  # Looping through the generated content in content_dir,
  # and comparing each file with the relevant content API endpoint.
  for file_name in os.listdir(str(content_dir)):
    # If the file name exists in the endpoint, we'll load
    # the HTML from the endpoint, prettify it, and run a diff.
    # If there is a diff, we'll run through every diff and generate
    # an output similar to `git diff`.
    if file_name in api_data['endpoints']:
      endpoint_uri = api_data['endpoints'][file_name]['url']
      endpoint_url = url + endpoint_uri

      api_data['endpoints'].pop(file_name)

      response = requests.get(endpoint_url)

      baseline_local_path = str(baseline_dir) + "/" + file_name

      pretty_html, errors = tidylib.tidy_fragment(response.content, options = {
        'show-body-only': 'yes',
        'anchor-as-name': 'no',
        'doctype': 'omit',
        'drop-empty-paras': 'no',
        'fix-backslash': 'no',
        'fix-bad-comments': 'no',
        'fix-uri': 'no',
        'input-xml': 'yes',
        'join-styles': 'no',
        'lower-literals': 'no',
        'preserve-entities': 'yes',
        'quote-ampersand': 'no',
        'quote-nbsp': 'no'
      })

      if (errors):
        html_errors.append(file_name + ': ' + txtmod.ENCODED_NEWLINE + errors.replace('\n', txtmod.ENCODED_NEWLINE) + txtmod.ENCODED_NEWLINE)

      open(baseline_local_path, "wb").write(response.content)

      # We cant use tidy, cause it corrects the HTML.
      # We want broken HTML to show up.
      # open(baseline_local_path, "w").write(pretty_html)
      # tidylib removes the empty line at the end of the file.
      #open(baseline_local_path, "a").write('\r\n')

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
        generate_commands.append("rm -f " + file_name + " && wget -O " + file_name + " '" + endpoint_url + "' ")

        diffs.append(file_name)

        if (verbose and len(return_message) > 20000):
          return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE + "Too many total diffs; cannot show diff for " + file_name + txtmod.ENCODED_NEWLINE 
        elif (verbose):
          # If the response has to be markdown safe, we need to add
          # a codeblock indicator.
          if (markdown_safe):
            return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE + txtmod.CODEDIFF + txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE

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
            return_message += txtmod.CODEEND
            return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE + txtmod.NEWLINE

    # If the file cant be found in the endpoint list, we
    # must assume that the file has been deleted.
    else:
      diffs.append(file_name + " has been deleted.")
      generate_commands.append("rm -f " + file_name)

  # Looping through the remaining endpoints, that didnt exist in the content dir already.
  for file_name in api_data['endpoints']:
    diffs.append(file_name + " has been created.")

    endpoint_uri = api_data['endpoints'][file_name]['url']
    endpoint_url = url + endpoint_uri

    generate_commands.append("wget -O " + file_name + " '" + endpoint_url + "' ")


  # Lines below basically just presents the results.
  return_message += txtmod.NEWLINE + txtmod.BOLD + "After checking " + txtmod.OKCYAN + url + txtmod.ENDBOLD + txtmod.ENDC + " the verdict is..." + txtmod.NEWLINE

  failed = False

  if api_data['messages']['errors'] or html_errors:
    return_message += txtmod.BOLD + txtmod.UNDERLINE + "Encountered errors:" + txtmod.ENDBOLD + txtmod.ENDUNDERLINE + txtmod.NEWLINE + txtmod.NEWLINE
    failed = True

  for error in api_data['messages']['errors']:
    return_message += "  - " + txtmod.FAIL + error + txtmod.ENDC + txtmod.NEWLINE

  if html_errors:
    return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE + txtmod.CODE + txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE

    for error in html_errors:
      return_message += "  - " + txtmod.WARNING + error + txtmod.ENDC + txtmod.ENCODED_NEWLINE

    return_message += txtmod.ENCODED_NEWLINE + txtmod.CODEEND + txtmod.ENCODED_NEWLINE

  if diffs:
    return_message += txtmod.BOLD + txtmod.UNDERLINE + txtmod.NEWLINE + "Found diffs in following files:" + txtmod.ENDBOLD + txtmod.ENDUNDERLINE + txtmod.NEWLINE

    for diff in diffs:
      return_message += txtmod.NEWLINE + "  - " + txtmod.WARNING + diff + txtmod.ENDC

    return_message += txtmod.NEWLINE + txtmod.NEWLINE + txtmod.BOLD + txtmod.UNDERLINE + "If the changes are correct, you can commit the changes after running:" + txtmod.NEWLINE + txtmod.ENDBOLD + txtmod.ENDUNDERLINE
    return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE + txtmod.CODE + txtmod.ENCODED_NEWLINE

    return_message += "mkdir -p " + str(content_dir) + " && ( cd " + str(content_dir)

    generate_commands_string = ''

    for command in generate_commands:
      command = ' && ' + command

      generate_commands_string += command

    return_message += generate_commands_string
    return_message += ' ) '

    # We cant use tidy, cause it corrects the HTML.
    # We want broken HTML to show up.
    #return_message += ' && tidy -m -indent --indent-spaces 2 --show-body-only yes --input-xml yes --force-output no --wrap 0 --tidy-mark no -quiet --anchor-as-name no --doctype omit --drop-empty-paras no --fix-backslash no --fix-bad-comments no --fix-uri no --join-styles no --lower-literals no --preserve-entities yes --quote-ampersand no --quote-nbsp no ./*'
    return_message += txtmod.ENCODED_NEWLINE + txtmod.ENCODED_NEWLINE + txtmod.CODEEND + txtmod.ENCODED_NEWLINE + txtmod.NEWLINE

    if (failexit):
      sys.exit(return_message)

    failed = True

  if not diffs:
    return_message += txtmod.BOLD + txtmod.OKGREEN + "No diffs encountered :)" + txtmod.ENDBOLD + txtmod.ENDC + txtmod.NEWLINE

  # If we have experienced no issues, we'll inform the user that all's good, and set
  # a STATUSOK that GithubActions can understand - otherwise we'll say STATUSFAIL.
  if failed:
    return_message += txtmod.NEWLINE + "STATUSFAIL"
  else:
    return_message += txtmod.NEWLINE + "STATUSOK"

  # Printing the final message, to be used in the GitHub comment.
  print(return_message)
  return return_message

main()
