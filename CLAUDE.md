- Never edit `skills/` or `agents/`. Edit `source/` and run `rake build`
- Always opt to use the standard library. Never install any libraries.

## Evaluating a skill

The skill-creator skill assumes a flat skill directory; this repo is different. Adapt as follows.

- **Source vs. built.** Skills and agents live at `<plugin>/source/{skills,agents}/…` and build to `<plugin>/{skills,agents}/…` via `rake build`. The built files are ERB-rendered: `<%= partials("x.md") %>` inlines `source/_partials/x.md`, and constructs like `<%= \`measured-notes --help\` %>` embed command output at build time. **Always run a skill against the built `<plugin>/skills/.../SKILL.md`** (and built agents), not `source/` — the rendered version is what ships. Re-run `rake build` after editing source, before evaluating.
- **Skills don't self-invoke.** The skills here set `disable-model-invocation: true` and spawn agent teams. A test subagent can't reliably spawn its own team, so a with-skill run should `Read` the built `SKILL.md` plus the agent files it names and act as the primary author. Tell the run not to call `AskUserQuestion`, spawn further subagents, or call session-only CLIs like `measured-notes` — have it write outputs directly into the eval output dir instead.
- **Workspace location.** Put eval runs in `<plugin>/source/skills/<skill>-workspace/iteration-N/eval-*/` with `with_skill/` and `without_skill/` arms. These are scratch and gitignored (`*-workspace/`) — don't commit them, and don't commit the built `skills/<skill>/evals/` copy either. The committed eval set is `source/skills/<skill>/evals/evals.json`.
- **Grade, benchmark, view.** Prefer a small grading script (stdlib only) over eyeballing; write `grading.json` per run with `expectations: [{text, passed, evidence}]`. Generate `benchmark.json` to the skill-creator schema (`runs[]` with nested `result`, `configuration` exactly `with_skill`/`without_skill`, `run_summary`, `delta`) and review with skill-creator's `eval-viewer/generate_review.py`.
