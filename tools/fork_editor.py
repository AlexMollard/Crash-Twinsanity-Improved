"""Point the editor submodule at our own fork, once that fork exists on GitHub.

The three fixes in tools/patches were carried as patches because the submodule was upstream's code. They are
now three commits on top of upstream master in tools/twinsanity-editor, on full history - but commits that
only exist locally are not something a fresh clone can fetch, so the submodule still has to be pinned at an
upstream commit until those commits live on a remote.

Creating the repository needs a logged-in GitHub session, so that one step is yours:

    https://github.com/Smartkin/twinsanity-editor  ->  Fork          (or: gh repo fork Smartkin/twinsanity-editor --clone=false)

then run this. It checks the fork really is a fork of upstream before pushing anything into it, pushes the
three commits, rewrites the submodule URL and moves the pin.

Nothing else in the build has to change: tools/twinsdump/twinsdump.csproj and build_mod.py reach the library
through the submodule's *path*, which is unaffected, and patch_editor() finds the fixes already present and
does nothing.

  python tools/fork_editor.py                                    # infer the fork from this repo's origin
  python tools/fork_editor.py https://github.com/you/twinsanity-editor.git
  python tools/fork_editor.py --check                            # say what would happen, touch nothing
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDITOR = os.path.join(ROOT, "tools", "twinsanity-editor")
UPSTREAM_TIP = "89f2c0b"          # the commit our three sit on; a real fork must contain it
EXPECTED = 3                      # how many commits we expect to be pushing


def git(*args, cwd=ROOT, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def infer_fork():
    """<owner>/twinsanity-editor, taking the owner from this repo's own origin."""
    origin = git("remote", "get-url", "origin")
    m = re.search(r"github\.com[/:]([^/]+)/", origin)
    if not m:
        raise SystemExit(f"cannot tell the GitHub owner from origin ({origin}); pass the fork URL instead")
    return f"https://github.com/{m.group(1)}/twinsanity-editor.git"


def main():
    args = [a for a in sys.argv[1:] if a != "--check"]
    dry = "--check" in sys.argv[1:]
    fork = args[0] if args else infer_fork()

    ahead = git("rev-list", "--count", f"{UPSTREAM_TIP}..HEAD", cwd=EDITOR)
    if ahead == "0":
        raise SystemExit(f"the submodule has no commits past {UPSTREAM_TIP} - nothing to push")
    print(f"fork:      {fork}")
    print(f"pushing:   {ahead} commit(s) on top of {UPSTREAM_TIP}")
    for line in git("log", "--oneline", f"{UPSTREAM_TIP}..HEAD", cwd=EDITOR).splitlines():
        print(f"             {line}")
    if ahead != str(EXPECTED):
        print(f"  note: expected {EXPECTED}; check the list above is what you meant to publish")

    # Push into the wrong repository and you have published someone else's history into it, so make sure the
    # target is reachable and really does share upstream's history before writing anything.
    ls = subprocess.run(["git", "ls-remote", fork, UPSTREAM_TIP, "refs/heads/*"],
                        cwd=EDITOR, capture_output=True, text=True)
    if ls.returncode:
        raise SystemExit(f"cannot reach {fork} - create the fork first (see the top of this file):\n{ls.stderr.strip()}")
    if UPSTREAM_TIP not in ls.stdout and ls.stdout.strip():
        raise SystemExit(f"{fork} does not contain upstream commit {UPSTREAM_TIP}; that is not a fork of "
                         f"Smartkin/twinsanity-editor and this refuses to push into it")
    if dry:
        return print("\n--check: stopping here, nothing changed")

    git("remote", "set-url", "origin", fork, cwd=EDITOR)
    git("push", "-u", "origin", "master", cwd=EDITOR)
    git("config", "-f", os.path.join(ROOT, ".gitmodules"), "submodule.tools/twinsanity-editor.url", fork)
    git("add", ".gitmodules", "tools/twinsanity-editor")
    print("\npushed, and .gitmodules + the submodule pin are staged. Commit them, then a fresh clone gets the "
          "fixes from the fork instead of having them patched in at build time.")


if __name__ == "__main__":
    main()
