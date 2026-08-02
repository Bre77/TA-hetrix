# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- This app runs on `splunk_input_runtime` (https://github.com/Bre77/splunk-input-runtime), not `splunklib`/`splunk-sdk`. `lib/requirements.txt` pins it to an exact commit archive URL with a `sha256:` hash recorded in a comment above it (no PyPI package exists yet, so there is no `==version` line to pin against). Bump both the commit and the recorded hash together when the runtime releases a new version; never point at a branch.
- Credential handling goes through `self.context.credentials.protect_input_fields(...)` (see `bin/hetrix.py`), not manual `storage_passwords` list/delete/create calls. This preserves the credential identity `(owner=nobody, app=TA-hetrix, realm=<stanza name>, username=key)` that existing installs already have - do not change that tuple without a captain-level decision; it strands users' stored secrets.
- `.build.sh` vendors `lib/` fresh on every build (`pip install -t lib -r lib/requirements.txt --no-dependencies`); `lib/` is gitignored except `lib/requirements.txt`. Do not commit vendored packages into `lib/`.
- The runner (`Script.run_script`) owns `EventWriter.close()`; app code must not call it explicitly. `splunk_input_runtime`'s `close()` is idempotent by design as a defense.
- `Bre77/SplunkUI-devcontainer`'s `test-harness/verify-splunklib-app.sh` is app-agnostic - point it at this repo to get a `dependency=splunk_input_runtime` build+import check on both Python 3.9 and 3.13. `test-harness/credential-continuity-gate.sh` is parameterised (`--app-id`, `--kind`, `--field`, `--old-app`/`--new-app`) - run it against real `--old-app`/`--new-app` builds of this repo using `--app-id TA-hetrix --kind hetrix --field key` to prove credential continuity across the migration.
- Version is recorded in three places that must stay in sync: `package.json` and both `version =` lines in `default/app.conf` (`[launcher]` and `[id]`). A mismatch fails AppInspect.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
