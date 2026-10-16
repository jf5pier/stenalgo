# Plan: rewrite the author of the 2024 `stenalgo` commits (jfstpierre -> jf5pier)

For a fresh session. Written 2026-10-09. **Nothing here has been run on `stenalgo`.** The same rewrite was done on
`stenalgo-plover` (6 commits) the same day; see "Precedent" at the end.

## Why

GitHub attributes a commit by its author email. 24 commits of `jf5pier/stenalgo` (2024-09-02 .. 2024-10-17) carry
`jf.stpierre@calculquebec.ca` (19 as `stpierre`, 5 as `Jean-Francois St-Pierre`), which belongs to the account `jfstpierre`, so
`jfstpierre` shows as a contributor (24). The wanted result: every commit is `jf5pier <jf.stpierre@gmail.com>`, which also removes the
work email from the public history. The commits are the root of the history, so they are ancestors of every branch.

Find them with: `git log --all --format='%h %an <%ae> %s' --author=calculquebec` (24 lines, first `7fce9c9` "Let's start !",
last `0dbcf14` "Linting and Typing"). Other identities in the repo are fine: `jf <jf.stpierre@gmail.com>` (217) and
`jf5pier <jf.stpierre@gmail.com>` (about 136).

## What the rewrite costs (read before starting)

- **Every commit hash changes**, on every branch, because the rewritten commits are the root.
- Remote branches to force-push: `main`, `abbreviations`, `affix-abbreviation-rules`, `cl_test_coverage`, `cpsatsolver`, `docs-refactor`,
  `performance-optim`, `phase-g-grouping`. Local branches: the same plus `lexique-completion`. There are no tags.
- **Hashes written in the repo become dangling**: `TODO.md`, `docs/*.md`, `CLAUDE.md`, code comments and commit messages cite commit ids
  (for example `ccd4d4b`, `37fdc4e`, `eb0a610`, `f80bdaf`). Grep for `\b[0-9a-f]{7}\b` in `*.md`, `*.py` and map old -> new with the
  `filter-branch` / `filter-repo` commit map. Also `stenalgo-plover`'s commit messages "Sync from stenalgo <hash>" cite stenalgo hashes
  (`eb0a610`, `35b9885`, `2553a62`, `f80bdaf`): after the rewrite they cite old hashes (leave them, or note the mapping).
- A second local worktree has `abbreviations` checked out (`git worktree list`): it must be rewritten or re-created too.
- The working tree of `/home/jfsp/Steno/stenalgo` holds uncommitted work (generated outputs, `LexiqueSynthetic.tsv`, 35 scratch files).
  **Do not rewrite in place.** Rewrite in a fresh clone, then move the branches.
- Anyone else with a clone (none known; no forks on GitHub as of 2026-10-09) would have to re-clone.

## Order (decided: rewrite BEFORE pushing the new work)

The local `main` (2 commits ahead) and `lexique-completion` (7 ahead) are not pushed. Rewrite first, so each branch is force-pushed once.

## Steps

0. **Backups** (outside the repo): `git bundle create .../stenalgo-before.bundle --all` from `/home/jfsp/Steno/stenalgo`, plus a copy of the
   untracked/uncommitted files if wanted (`git stash` is NOT needed; the clone below does not touch the working tree).
1. **Fresh clone**: `git clone --no-local /home/jfsp/Steno/stenalgo /tmp/.../stenalgo-rewrite` (gets every local branch under
   `origin/*`; check with `git branch -a`). Also fetch `origin` of the real repo first (`git fetch origin`) so the remote-only branches are
   current, then `git clone --mirror` is the simpler route: `git clone --mirror /home/jfsp/Steno/stenalgo mirror.git` copies all local
   branches AND remote-tracking refs as branches; delete the `refs/remotes/...` copies you do not want, or clone from GitHub instead and add
   the two unpushed local branches with `git fetch /home/jfsp/Steno/stenalgo main:main lexique-completion:lexique-completion`.
2. **Rewrite** all branches, author and committer, by email:
   ```
   git filter-branch -f --env-filter '
   if [ "$GIT_AUTHOR_EMAIL" = "jf.stpierre@calculquebec.ca" ]; then GIT_AUTHOR_NAME="jf5pier"; GIT_AUTHOR_EMAIL="jf.stpierre@gmail.com"; fi
   if [ "$GIT_COMMITTER_EMAIL" = "jf.stpierre@calculquebec.ca" ]; then GIT_COMMITTER_NAME="jf5pier"; GIT_COMMITTER_EMAIL="jf.stpierre@gmail.com"; fi
   ' -- --branches
   ```
   (`git filter-repo --mailmap` is the better tool if installed; it was not on 2026-10-09: `pip install git-filter-repo`.) Keep the map
   `.git/filter-repo/commit-map` (filter-repo) or compute one with `git rev-list` before/after for the doc fix.
3. **Verify**: for every branch, `git diff --stat OLD NEW` is empty (same trees); `git log --all --format='%an <%ae> | %cn <%ce>' | sort | uniq -c`
   shows no `calculquebec`; commit counts per branch unchanged; `git fsck`.
4. **Update the cited hashes** in `*.md` / `*.py` with the map (a separate commit on top, on each branch that has the files; at least `main` and
   `lexique-completion`; the pre-rewrite docs in the old branches are fixed only if cheap).
5. **Bring the rewritten branches back to `/home/jfsp/Steno/stenalgo`**: in the real repo, `git fetch /tmp/.../stenalgo-rewrite 'refs/heads/*:refs/rewritten/*'`,
   then for each branch `git branch -f BRANCH refs/rewritten/BRANCH` (for the checked-out branch use `git reset --soft` / `--mixed` so the
   uncommitted working tree stays; `--mixed` is right: the trees are identical, only the parent hashes changed). Do the `abbreviations` worktree
   the same way (`git -C <worktree> reset --mixed rewritten/abbreviations`, with its work tree clean first).
6. **Push (user approval for each force-push; the action classifier blocked an agent's force-push on 2026-10-09)**:
   `git push --force-with-lease=BRANCH:OLDHASH origin BRANCH` per branch, with OLDHASH the current `origin/BRANCH`; first `main` and
   `lexique-completion`/new work, then the others. Run it yourself with `! git push ...` if the agent is refused.
7. **Check on GitHub**: `gh api repos/jf5pier/stenalgo/contributors` lists only `jf5pier` (the cache can take minutes); the commit list of each
   branch shows no `jfstpierre`; the default branch is `main`.
8. **Cleanup**: keep the bundle for a few weeks; set the identity so it cannot recur (`git config user.name/user.email` in every clone; the
   global `~/.gitconfig` is `stpierre <jf.stpierre@calculquebec.ca>`, which is the root cause).

## Alternative (no rewrite)

Move the email `jf.stpierre@calculquebec.ca` from the `jfstpierre` account to `jf5pier` (GitHub Settings -> Emails, remove from one, add and
verify on the other): GitHub re-attributes all commits, no hash changes, but the work email stays in the public metadata.

## Precedent: `stenalgo-plover`, 2026-10-09

3 of its 6 commits (`cd3734a`, `13bdb00`, `ce54312`) had the work email. Rewritten locally with the `filter-branch` command above on `master`
(trees identical, backup bundle in the session scratchpad), identity set in the clone (`git config user.name jf5pier`, `user.email
jf.stpierre@gmail.com`). The force-push (`git push --force-with-lease=master:ce54312c4a46235379b44225b4463b6935b69a05 origin master`) was
NOT done by the agent (blocked); check `git -C /home/jfsp/Steno/stenalgo-plover status -sb` and `gh api repos/jf5pier/stenalgo-plover/commits`
to see whether the user pushed it.

## Status, 2026-10-09 evening: steps 0-4 DONE, 5-6 left for the user

Done in a scratch clone, now kept in `/home/jfsp/Steno/stenalgo-rewrite/` (`clone/` = the rewritten repo with the 9 branches,
`stenalgo-before.bundle` = backup of every ref before, `commit-map.txt` = old new id per commit, 377 lines):
all 377 commits re-authored (no `calculquebec` left; only `jf`, `jf5pier` and the 3 GitHub-web commits remain), checked: every tree identical,
commit counts per branch identical, `git fsck` clean. Note: the 3 GitHub-web commits (`Initial commit`, two `Update README.md`) were GPG-signed
by GitHub; the rewrite drops their signatures (they lose the "Verified" badge). Hash fix commits added on top of `main` (`fb6c511`) and
`lexique-completion` (`f81a988`): 75 commit ids remapped in docs, TODO and comments, plus `docs/history/COMMIT_MAP_2026-10-09.tsv`.
The other 7 branches only have the new author (their docs still cite old ids; the map resolves them).

The agent's attempt to bring the branches into `/home/jfsp/Steno/stenalgo` (`reset`, `branch -f`, `reset --hard` on the worktree) was refused by
the action classifier, so nothing changed there. To finish, review and run:
1. `/home/jfsp/Steno/stenalgo-rewrite/apply_local.sh` (local only; keeps the uncommitted working tree; resets the `abbreviations` worktree,
   whose tracked files are clean);
2. `/home/jfsp/Steno/stenalgo-rewrite/push_all.sh` (9 pushes, 8 force-pushes each leased on the current remote tip; or paste them with `!`).
Then check `gh api repos/jf5pier/stenalgo/contributors` (only `jf5pier`), and the mirror `stenalgo-plover` commit messages "Sync from stenalgo <id>"
(old ids; see the map).

## DONE, 2026-10-09 night

`apply_local.sh` and `push_all.sh` were run by the user: the 8 branches were force-pushed (leased) and `lexique-completion` was pushed as a new
branch. `git log --all` now has a single author email (`jf.stpierre@gmail.com`, 379 commits) and every `origin/*` tip is the rewritten one
(`main` fb6c511, `lexique-completion` f81a988, ...). GitHub's contributors cache still showed `jfstpierre 24` right after the push (it refreshes
within hours); recheck with `gh api repos/jf5pier/stenalgo/contributors`. Kept for a few weeks: `/home/jfsp/Steno/stenalgo-rewrite/`
(`stenalgo-before.bundle`, `commit-map.txt`, `undo_local.sh`). `stenalgo-plover` was fixed the same day (see Precedent).
