# NetDirector — user guide

A Windows desktop application for managing application-specific network preferences, built with Python 3 and PySide6. Profiles store adapter identities and resolve current addresses before startup activation and **again immediately before each launch**.

### Version 1.1 — redesigned interface

The dashboard follows the supplied visual reference: a lavender-to-pink navigation bar, deep navy surfaces, soft shadows, vector line icons, an eight-tile action grid, and circular live download/upload displays. Profile activation and current adapter addresses appear in compact cards. New installations default to dark mode; existing saved theme choices are retained. Light and System remain available in Settings → Appearance.

Dashboard rates are the sum of measured available-adapter counters, not per-process bandwidth. Virtual and physical adapters can observe the same traffic, so this is interface activity rather than a deduplicated internet-speed measurement. The gauge arcs are decorative and do not claim a utilization percentage. A dash indicates that no counter sample is available.

## What works

- Live Windows adapter discovery: GUID, index, MAC, description, IPv4/IPv6, gateways, DNS, status, link speed, and outbound internet reachability testing.
- Conservative identity matching across renames and DHCP changes. A reused interface index or duplicate friendly name cannot silently select another device.
- Application rules, executable icons, drag-and-drop `.exe` files, arguments, working directories, enable/disable, auto-launch, and fallback choices.
- Running application picker: choose from active GUI windows with system icons in one click.
- Game library auto-discovery across multi-drive Steam and Epic Games installations.
- Profile creation, editing, duplication, import/export, deletion, activation, Wi-Fi SSID auto-triggering, and startup profile selection.
- System tray quick switcher to activate profiles with one click.
- Headless CLI commands (`--list-profiles`, `--list-adapters`, `--activate-profile`).
- ForceBindIP integration with automatic x86/x64 executable detection, safe argument parsing, backend detection, and bundled binaries.
- Serial background jobs keep discovery, launching, process inspection and traffic sampling off the UI thread.
- Windows startup registration for the current user, tray controls, launch-minimized, saved appearance, light/dark/system themes.
- Actual adapter byte counters, observed process trees, socket-local-address diagnostics and rotating logs.
- Folder-based standalone Windows packaging with app icon/version metadata, Inno Setup installer, and offline bundling.

This is a **launch-time routing manager**, not a traffic isolation system. Profile activation prepares rules and launches only enabled rules with auto-launch selected. It does not intercept every application started outside NetDirector. Pausing cancels pending launches; already-running programs retain their injected binding until closed. Changing a rule or receiving a new DHCP address does not rebind an existing process.

## Screenshots

The screenshots are rendered from the application with documentation-only example adapters; no private network identifiers are included.

![Light dashboard](screenshots/dashboard-light.png)
![Dark dashboard](screenshots/dashboard-dark.png)

Regenerate public-safe previews with `python scripts/capture_ui.py`. Use `--live` only for local inspection; live captures are saved in an ignored directory.

## Prerequisites

- Windows 10 or Windows 11 x64 (recommended), or the legacy x86 build for 32-bit Windows 10. The x64 app can launch both 32-bit and 64-bit targets.
- For source development: Python 3.11 or newer; Python 3.12 is used for the supplied build.
- Windows PowerShell and the standard NetTCPIP/NetAdapter modules (included with supported Windows installations).
- ForceBindIP is bundled with official installers and packages. Custom paths can be configured in Settings.

No system-wide network changes or administrative startup registration are required. Some protected processes deny socket inspection; diagnostics reports that limitation instead of silently elevating the whole app.

## Install and run the standalone build

Download the installer (`NetDirector-*-windows-x64-Setup.exe`) or extract the portable ZIP. Keep `_internal` and `ForceBindIP` beside the executable if running portable. Python does not need to be installed. Configuration is saved under `%LOCALAPPDATA%\NetDirector`, so the app works from read-only install locations.

## Development setup

```powershell
cd C:\path\to\NetDirector
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python scripts/create_assets.py
python main.py
```

Run `python -m pytest -q` for the test suite. `python main.py --smoke-test` discovers real adapters, suppresses automatic profile activation and the welcome dialog, and exits after 12 seconds. Use a temporary `NETDIRECTOR_DATA_DIR` when smoke-testing to avoid touching your normal data.

## First run and profiles

1. Wait for network discovery. The welcome dialog lists currently available adapters.
2. Choose **Create first rule** or open **Applications → Add application**. Steam can be found via its registry installation path or common installation folders.
3. Browse to an `.exe`, select its network, and save. Choose **Automatic / Windows default** to use normal Windows routing.
4. Create a profile in **Profiles** for each setup. Use the top-right selector to choose the profile whose rules you are editing.
5. Select **Launch automatically when this profile activates** only for applications you want started during activation.
6. Enable **Load this profile on startup** in profile details. Settings can enable starting NetDirector with Windows and launching minimized.
7. Activate the profile. Each launch runs a new discovery operation; unavailable adapters follow the rule's fallback.

Launch arguments use Windows command-line quoting. For example, `--profile "Work account"` passes a single argument containing a space. The executable is started directly without a command shell.

Only one startup profile is supported. Explicit startup profiles take precedence over restoring the last active profile. Multiple conflicting startup flags in manually edited JSON cause an error rather than arbitrary activation. Imported profiles receive new IDs and have startup/auto-launch disabled for review. Duplicate executable paths in a profile are rejected.

## Adapter matching and startup order

1. Discover all interfaces and their current addresses on a background thread.
2. Match saved identities by GUID, then unique MAC. If those are absent, require a corroborated description with name or index. Conflicting strong identity evidence prevents weaker matching.
3. Validate executable paths and adapter availability.
4. Select the configured startup profile and activate its rules.
5. Before launching each application, discover and resolve its adapter again.

Indexes alone and friendly names alone are insufficient. When a replacement device has a new GUID/MAC, reassign the rule explicitly. This conservative approach can ask for reassignment instead of guessing a connection.

Profiles never contain `ipv4`, `current_ip`, DNS, gateways or runtime traffic. The runtime may show multiple addresses; the first preferred, non-loopback, non-link-local IPv4 address not marked SkipAsSource is selected. IPv6 addresses are informational for the current backend.

## Fallbacks

| Choice | Behavior when the selected adapter has no usable IPv4 |
|---|---|
| Do not launch | Default. Report the problem and block the launch. |
| Windows default | Launch directly using Windows routing. |
| Ask me | Bring up a confirmation for that launch only. Unattended launches wait for the response. |
| Wait | Queue the launch until a later adapter scan reports it available. |

Wait requires automatic refresh or a manual Refresh Networks action. Editing rules, activating another profile, pausing, and exiting invalidate queued snapshots. A discovery failure blocks all new launches, including Windows-default fallbacks, because the mandatory discovery barrier was not satisfied.

## ForceBindIP setup

Download ForceBindIP from its [author's website](https://r1ch.net/projects/forcebindip). Install its required Visual C++ runtimes. Keep the loader and DLL pairs in the same directory:

```text
ForceBindIP.exe
BindIP.dll
ForceBindIP64.exe
BindIP64.dll
```

NetDirector checks PATH and common `ForceBindIP` installation folders. Or choose its directory under **Settings → ForceBindIP directory**. It reads the target PE header to select the matching loader. ARM targets are rejected.

Commands take this form, with the address supplied only at runtime:

```text
ForceBindIP64.exe CURRENT_ADAPTER_IPV4 "C:\path\application.exe" [arguments]
```

The target's working directory defaults to its executable folder. Loader success is not proof of successful interception: statuses say **binding requested / unverified** until the user inspects connections. The process monitor distinguishes the loader PID from the target process and checks process creation times to guard against PID reuse.

### Compatibility and child processes

ForceBindIP injects into compatible applications. Its author's documentation states that modern Chrome is incompatible. Some launchers, anti-cheat-protected games, and applications with nonstandard networking are unsuitable. DNS lookups may use the Windows DNS service, and IPv6 traffic is not enforced by this integration. **Do not use this as a VPN leak-prevention tool.**

The child-process setting enables **monitoring**, not guaranteed binding inheritance. Steam downloads, helpers, and games may use different processes; diagnostics can inspect observed children, but this release cannot guarantee Wi-Fi-only Steam downloads with Ethernet-only games. Explicit game rules require launching compatible game executables directly through NetDirector; Steam may reuse an already-running launcher. Existing running instances are detected and new routing launches are blocked to avoid misleading results.

## BindIP setup and native extension

`bindings/bindip_engine.py` and `bindings/native_engine.py` are explicit unsupported extension points. Settings labels them as not implemented; selecting either fails clearly for adapter-bound launches. No fabricated BindIP command line or undocumented driver setup is used. The independent [katlogic BindIP project](https://github.com/katlogic/bindip) has a different configuration model and is not interchangeable with ForceBindIP.

Implement `BindingEngine.launch_application()`, capability flags, and status behavior to add another backend. The UI consumes `RoutingService` and `Controller`, so the profile format and UI do not need a rewrite.

## Diagnostics, logs, and privacy

Select an application in **Diagnostics → Check network usage** to inspect its current sockets. Descendants are included when monitoring is enabled. Matching and mismatching local addresses are compared against the launch IP; wildcard/loopback addresses remain unverified. Access-denied processes and missing sockets are reported clearly. Inspection also finds the selected executable if it was launched externally, but does not claim it was bound by NetDirector.

Process discovery is sampled and can miss short-lived or detached children. A matching socket sample is not proof that all application traffic uses that adapter. Exact per-process bandwidth is not provided; the Traffic Monitor explicitly reports that limitation. Adapter rates use actual psutil counter deltas, including a blank initial sample and counter-reset handling.

Logs are stored in `%LOCALAPPDATA%\NetDirector\logs\netdirector.log` with rotation. Routine logs record actions and failures, not launch arguments, remote connection endpoints, or packet contents. Configuration and exports contain executable paths and adapter identifiers, so review them before sharing. Files are local to the current user; no telemetry is sent.

## Data and recovery

```text
%LOCALAPPDATA%\NetDirector\
    settings.json
    profiles\<profile-uuid>.json
    logs\netdirector.log
```

Override the root with `NETDIRECTOR_DATA_DIR` for portable/test usage. JSON writes use a temporary file, flush, and atomic replacement. Invalid profiles are retained and listed as errors. Invalid settings load defaults; saving first preserves the original as `settings.invalid.json`. If that recovery backup already exists, review it before overwriting settings. The single-instance lock prevents concurrent copies from racing on storage.

Windows startup uses `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\NetDirector`. Disable **Start with Windows** before removing the program. For development, that entry points to the current interpreter and `main.py`; save the setting again after moving installations.

## Build the Windows executable

Build on Windows using the activated development environment:

```powershell
.\scripts\build.ps1
# Optional single-file package:
.\scripts\build.ps1 -OneFile
```

The script runs tests first, creates the icon, includes the user guide and version resource, then invokes PyInstaller. Default output: `dist\x64\NetDirector\NetDirector.exe`. One-file output: `dist\x64\NetDirector.exe`. The folder build is recommended for debugging and distribution. The one-file option extracts dependencies at startup and takes longer to open.

Build through the supplied script: it isolates the build PATH so unrelated tools cannot contribute incompatible DLLs (for example, Poppler's `icuuc.dll` in place of Windows ICU).

For legacy x86 build instructions and the automated release process, see [Releasing](RELEASING.md). No installer or code-signing certificate is included. A distributable ZIP of the folder build is sufficient for portable installation. To produce an installer later, wrap the folder in your preferred installer and register the startup option only with user consent. Third-party components retain their own licenses; review PySide6/Qt and other dependency distribution obligations before commercial redistribution.

## Troubleshooting

| Problem | Action |
|---|---|
| Adapter needs reassignment | Edit the rule and select the intended current adapter; do not substitute an old saved IP. |
| Adapter missing / disconnected | Reconnect it, refresh adapters, or choose an explicit fallback. |
| Executable missing | Edit the rule and browse to its new location. |
| Application already running | Close its background/tray processes before launching again. |
| Backend unavailable | Install the matching ForceBindIP loader/DLL pair and select its folder. |
| Target not observed | Check backend compatibility and whether the target immediately exits or hands off to another process. |
| Different local IP | Inspect whether this is IPv6, a helper, or unsupported networking; do not assume interception succeeded. |
| Address changed while app runs | Close and relaunch the application through NetDirector. |
| Discovery fails | Check that Windows NetAdapter/NetTCPIP PowerShell modules work under the current account. The UI preserves the last display but blocks new launches. |
| Window seems closed | Open NetDirector from its tray icon. |
| Corrupt JSON | Review the Activity log and retained file; import a known-good profile. |

## Architecture and tests

`models/` contains profile-safe data, `services/` contains OS calls, `core/` owns matching/storage/routing/monitoring, `bindings/` provides swappable launch engines, `app/` sequences background work and startup, and `ui/` contains pages/dialogs/theme/widgets.

Tests cover parsing live discovery format, renames, reused indexes, duplicate names, MAC matching, profile persistence/import/corruption, duplicate rules, DHCP renewal, missing adapters/executables, fallback choices, ForceBindIP command generation, startup order, main-thread signal delivery, pause cancellation, PID reuse, real counter-delta calculations and rendering all UI pages/themes. Actual ForceBindIP interception still requires a compatible target and separately installed backend for end-to-end validation.
