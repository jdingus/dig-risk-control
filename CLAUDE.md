@AGENTS.md

# CLAUDE.md is only a pointer. Do not add anything to this file.

The rules for this folder live in AGENTS.md, which the line above imports.
Why: Josh runs more than one kind of agent (Claude Code, Codex, open models). The others read
AGENTS.md and never read CLAUDE.md, so a rule written here would reach Claude only and the
agents would drift apart. One home for every rule keeps them all the same.
To add or change a rule, edit AGENTS.md instead. A checker (instructions-check.py, check i)
fails any CLAUDE.md that holds more than this note. Standard: ~/brain/ops/systems/repo-bootstrap.md
