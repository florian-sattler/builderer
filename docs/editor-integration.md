# Editor integration

In order to minimize friction and maximize productivity, _builderer_ provides its own [schema.json](schema.json) for `.builderer.yml`. If your editor supports
YAML schema validation, it's definitely recommended to set it up.

## Visual Studio Code

1.  Install [`vscode-yaml`](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml) for YAML language support.
2.  Add the schema under the `yaml.schemas` key in your user or
    workspace [`settings.json`](https://code.visualstudio.com/docs/getstarted/settings):

    ```json
    {
      "yaml.schemas": {
        "https://builderer.florian-sattler.de/schema.json": ".builderer.yml"
      }
    }
    ```

## Other

1.  Ensure your editor of choice has support for YAML schema validation.
2.  Link the schema present at `https://builderer.florian-sattler.de/schema.json` to files named `.builderer.yml` or manually select the schema.
