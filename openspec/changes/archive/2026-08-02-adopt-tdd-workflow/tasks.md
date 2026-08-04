## 1. Config

- [x] 1.1 In `openspec/config.yaml`, set `context` to state red/green TDD as the required workflow for new work: write a failing test first, implement the minimum code to pass it, then refactor with tests green. Include the scope note (forward-looking only, not retroactive).
- [x] 1.2 Add a `rules.tasks` entry requiring that each implementation task in future `tasks.md` files is paired with a preceding task to write its failing test.
- [x] 1.3 Add an `operations.apply.guidance` entry spelling out the red/green/refactor sequence to follow while working through tasks during `openspec apply`.

## 2. Verification

- [x] 2.1 Run `openspec context --json` (or `openspec instructions <artifact> --json` for an existing change) and confirm the new `context`/`rules` text is present in the output.
- [x] 2.2 Run `openspec validate` (or equivalent config lint) to confirm `config.yaml` is still well-formed after the edit.
