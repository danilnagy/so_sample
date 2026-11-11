#!/bin/sh
# Publish the current master to the public repository as one new commit, without the
# private history.
#
#   ./publish-public.sh "Describe the update"
#
# Development happens on master and is pushed to the private repository (remote "origin").
# The public repository (remote "public") has its own history on the local branch "public":
# each run copies master's tracked files onto it exactly (additions, changes and deletions)
# as a single commit and pushes it to public's main. master itself is never pushed there,
# since its history holds material that may not be published (see docs/release.md).
# Ignored local files (sample packs, presets-tr, research captures) are never touched.
set -eu

message="${1:-}"
if [ -z "$message" ]; then
  echo "usage: ./publish-public.sh \"Describe the update\"" >&2
  exit 1
fi

cd "$(dirname "$0")"

# Guards: on master, nothing uncommitted, and "public" is a different repository from "origin".
if [ "$(git rev-parse --abbrev-ref HEAD)" != "master" ]; then
  echo "Run this from master." >&2
  exit 1
fi
if [ -n "$(git status --porcelain)" ]; then
  echo "Commit or stash your changes on master first." >&2
  exit 1
fi
public_url="$(git remote get-url public 2>/dev/null || true)"
if [ -z "$public_url" ]; then
  echo "No remote named public. Add it: git remote add public git@github.com:<you>/<repo>.git" >&2
  exit 1
fi
if [ "$public_url" = "$(git remote get-url origin)" ]; then
  echo "The public remote points at the private repository ($public_url). Fix it: git remote set-url public <new repo URL>" >&2
  exit 1
fi
if ! git rev-parse --verify --quiet public >/dev/null; then
  echo "No local branch named public. Create it once: git checkout --orphan public && git commit -m \"Initial public release\" && git checkout master" >&2
  exit 1
fi

# Commits made on GitHub (a merged pull request, an edit in the browser) must reach master
# first: a snapshot of master would otherwise undo them, and the push would be rejected.
git fetch -q public
if git rev-parse --verify --quiet public/main >/dev/null && [ "$(git rev-parse public/main)" != "$(git rev-parse public)" ]; then
  if git merge-base --is-ancestor public/main public; then
    # A snapshot made by an earlier run whose push failed: send it now, then carry on.
    echo "Pushing an earlier snapshot that was not pushed:"
    git log --oneline public/main..public
    git push public public:main
  elif git merge-base --is-ancestor public public/main; then
    echo "The public repository has commits this folder has not published:" >&2
    git log --oneline public..public/main >&2
    echo "Bring them into master, then mark them as seen, and run this again:" >&2
    echo "  git cherry-pick $(git rev-list --reverse public..public/main | tr '\n' ' ')" >&2
    echo "  git branch -f public public/main" >&2
    exit 1
  else
    echo "The local public branch and the public repository have diverged; compare git log public and git log public/main." >&2
    exit 1
  fi
fi

source_commit="$(git rev-parse --short master)"
# Whatever happens from here (a failed push included), end on master.
trap 'git checkout -q master 2>/dev/null || true' EXIT
git checkout -q public
# Mirror master's tracked files exactly: clear the branch's tracked files, then take master's.
git rm -rq --ignore-unmatch .
git checkout master -- .
if git diff --cached --quiet; then
  echo "Nothing new to publish: public already matches master ($source_commit)."
  git checkout -q master
  exit 0
fi
git commit -q -m "$message"
git push public public:main
git checkout -q master
echo "Published master ($source_commit) to $public_url as: $message"
