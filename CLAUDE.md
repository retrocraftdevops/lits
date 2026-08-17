# lits — working notes for agents

The machine-wide rules in `~/.claude/CLAUDE.md` apply here in full.

---

## Never stash

**`git stash` is forbidden in this repo.** Not discouraged — forbidden.

The stash is shared machine state, and several agent sessions run at the same time. A stash
silently reverts tracked files that may belong to another session, leaving no record of whose
they were. It also splits the work in half: plain `git stash` reverts tracked files and leaves
untracked ones behind, so the tree ends up part-new and part-reverted, and frequently stops
building. This has already cost real work on this machine — a stash that looked like a clean
shelve took back one half of a feature, orphaned the other half, and left a tree that no
longer compiled while reading to its author as "my changes were reverted".

This is **enforced, not asked**: a PreToolUse hook (`~/.claude/hooks/block-git-stash.sh`)
denies every mutating `git stash` subcommand — bare `stash`, `push`, `save`, `pop`, `apply`,
`drop`, `clear`, `store`, `create`. `git stash list` and `git stash show` stay allowed,
because recovering an existing stash means reading it first.

| Instead of stashing | Do this |
| --- | --- |
| You want a clean tree for parallel work | `git worktree add --detach <sha> /tmp/<name>` |
| Another session's edits are in your way | Leave them; coordinate via `~/.claude/ACTIVE-WORK.md` |
| Something is broken | Fix it — do not shelve it |
| Your own work is finished | Commit it, staging by explicit path |
| A stash already exists | Restore only what you need: `git restore --source='stash@{0}' --worktree -- <paths>`. Never `pop` it wholesale, and never `drop` one you did not create |

**Coordinate and enhance the code. Never hide it.**
