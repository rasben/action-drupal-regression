# action-drupal-regression

GitHub action to be used in tandem with reload/drupal-regression Drupal Module, to automatically check PRs if the Drupal DOM has changed on entities.

Basically a HTML/text-based alternative to backstopJS.

See https://github.com/reload/drupal-regression for the required Drupal Module.

## Using the action

You can either use the action alone, or use the full workflow, which sets relevant comments/action statuses.

Example setup: https://github.com/reload/storypal/blob/main/.github/workflows/drupal-regression.yml

## Testing locally:

- Have python3 + pip3 installed
- `pip3 install install wheel colorama requests validators pytidylib`
- `python3 compare.py --url=https://some-remote-api-url.com`

If you want to test with the exact, markdown output that GitHub Action uses:

- `python3 compare.py --url=https://some-remote-api-url.com --workdir=drupal-regression --markdown=True --verbose=True`
