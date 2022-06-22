# action-drupal-regression

GitHub action to be used in tandem with reload/drupal-regression Drupal Module, to automatically check PRs if the Drupal DOM has changed on entities.

Basically a HTML/text-based alternative to backstopJS.

See https://github.com/reload/drupal-regression for the required Drupal Module.

## Using the action

Example setup: https://github.com/reload/storypal/blob/main/.github/workflows/drupal-regression.yml

```yml
name: 'Drupal Regression'

on: pull_request
permissions: write-all

jobs:
  drupal-regression:
    uses: reload/action-drupal-regression/.github/workflows/drupal-regression.yml@main
    with:
      PLATFORMSH_ID: CHANGE_ME
```
