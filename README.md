# Agent Smith

[![Unit Tests](https://github.com/RewstApp/rewst_remote_agent/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/RewstApp/rewst_remote_agent/actions/workflows/unit-tests.yml)
[![Code Coverage](https://github.com/RewstApp/rewst_remote_agent/actions/workflows/code-coverage.yml/badge.svg)](https://github.com/RewstApp/rewst_remote_agent/actions/workflows/code-coverage.yml)
[![Build](https://github.com/RewstApp/rewst_remote_agent/actions/workflows/build.yml/badge.svg)](https://github.com/RewstApp/rewst_remote_agent/actions/workflows/build.yml)

Rewst's lean, open-source command executor that fits right into your Rewst workflows. See [community corner](https://docs.rewst.help/community-corner/agent-smith) for more details.

## Dependencies

Dependencies are managed by `poetry`. See [installation documentation](https://python-poetry.org/docs/#installation) on how to install `poetry` on your machine.

## Testing

Unit tests are written in the `tests` directory using `pytest` module. Minimum code coverage for all commits is `90%`.


Run the unit tests with this command.
```
poetry run pytest
```

Run the code coverage report with this command.
```
poetry run pytest --cov=.
```

## Contributing

Contributions are always welcome. Please submit a PR!

Please use `commitizen` to format the commit messages. After staging your changes, you can commit the changes with this command.
```
poetry run cz commit
```

## License

Agent Smith is licensed under `GNU GENERAL PUBLIC LICENSE`. See license file for details.