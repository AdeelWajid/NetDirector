# Contributing

Use the setup instructions in [README.md](README.md). Work from a branch and submit a pull request describing the behavior change and how it was checked.

- Keep adapter addresses in runtime state; never add saved IPs to profile identities.
- Keep OS operations and routing logic out of UI widgets, and keep slow operations off the Qt UI thread.
- Import Qt through `qt_compat`, so x64/Qt 6 and legacy x86/Qt 5 remain compatible.
- Run `python -m pytest -q`. For packaging changes, build and smoke-test both architectures with their matching interpreters. CI repeats these checks.
- Use `NETDIRECTOR_DATA_DIR` to isolate development data. Never commit local profiles, logs, credentials, or real-network screenshots.
- Report limitations honestly: a launch request is not proof of routing, and observed socket counts are not bandwidth measurements.

Contributions are made under the repository's MIT license. Keep third-party code and notices clearly identified.
