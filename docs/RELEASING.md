# Publishing NetDirector on GitHub

Use **the `NetDirector` directory as the repository root**, so `.github/workflows/release.yml` is directly under the repository root. Do not upload the enclosing scripts directory or unrelated files.

## First-time repository setup

1. Create an empty **public** repository on GitHub with your preferred name. Do not initialize a second README or license remotely.
2. Open PowerShell in this project's root and initialize Git if it is not already a repository:

   ```powershell
   git init -b main
   git add .
   git diff --cached --stat
   git diff --cached
   git commit -m "Initial public release of NetDirector"
   git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-REPOSITORY.git
   git push -u origin main
   ```

   Replace the URL with the actual repository URL. Inspect staged files before committing; `.gitignore` does not remove files that were already tracked. Avoid `git add -f` for ignored data.

3. Confirm that the repository's Actions settings allow GitHub-owned actions and that the Windows builds finish successfully. Organization policies may restrict `contents: write`; the release job needs that permission.

No GitHub repository is created or published merely by adding these files. The commands above are the publishing step.

## Create a release

1. Edit `VERSION`, using `MAJOR.MINOR.PATCH` with numeric components.
2. Commit and push the release changes.
3. Create a matching tag, for example:

   ```powershell
   git tag v1.1.0
   git push origin v1.1.0
   ```

4. The tag triggers both Windows jobs. Only after tests, packaging, PE checks, and smoke tests pass does the release job publish these assets:

   ```text
   NetDirector-1.1.0-windows-x64.zip
   NetDirector-1.1.0-windows-x64.sha256
   NetDirector-1.1.0-windows-x86.zip
   NetDirector-1.1.0-windows-x86.sha256
   ```

Re-running the same tag workflow refreshes its assets. Do not move published tags to new code; publish a new version instead. Manual branch runs upload artifacts without creating a release.

## Architecture and compatibility

| Build | Interpreter | Qt | psutil |
|---|---|---|---|
| x64 | Python 3.12 x64 | PySide6 6.11.2 | 7.2.2 |
| x86 legacy | Python 3.10 x86 | PySide2 5.15.2.1 | 7.0.0 |

PySide6 does not provide win32 wheels. psutil 7.0.0 is pinned for its published win32 wheel; newer psutil releases do not provide that wheel. The x86 runtime is older and should be treated as a legacy compatibility option. The CI runner is x64 Windows, so x86 smoke tests run through Windows' 32-bit compatibility subsystem; test on physical 32-bit Windows before making guarantees about those systems.

`qt_compat` normalizes Qt imports and event-loop naming; it does not change routing logic. Opposite Qt bindings are excluded from each package. `build_metadata.py` validates the interpreter, tag and version. `package_release.py` independently reads the built PE header before assigning an architecture label.

## Workflow permissions

- Build jobs have read-only repository permissions and do not receive publishing credentials.
- The release job runs only for version tags, after both matrix jobs succeed, and has `contents: write`.
- Third-party action code is pinned to commit SHAs; Dependabot proposes updates.
- No `pull_request_target` or execution of fork code with publishing permissions is used.
- Builds are unsigned. The release builds provide both portable ZIPs and Inno Setup Windows installers with ForceBindIP bundled.

## Public screenshots

`python scripts/capture_ui.py` generates documentation previews using example adapter identities and documentation-only address ranges. It never launches the example applications or alters routing. `--live` captures local network details under `docs/local-screenshots/`, which is ignored by Git. Do not move live captures into public documentation without reviewing them.
