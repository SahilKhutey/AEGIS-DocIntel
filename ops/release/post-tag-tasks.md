# Post-tag tasks (v0.3.0)

Run these in order, in the same day as the tag push.

## A. Within 30 minutes
- [ ] Watch `release.yml` succeed.
- [ ] Confirm `gh release view v0.3.0` renders correctly.
- [ ] Confirm `ghcr.io/sahilkhutey/amdi:v0.3.0` and `:latest` resolve.

## B. Within 2 hours
- [ ] Run `pip install amdi-os==0.3.0` in a clean venv and re-run
      `python scripts/demo_reel.py --record /tmp/v030.check.json`
- [ ] Sign in the PyPI upload (or private index URL) for the wheel + sdist.
- [ ] Pin `release/v0.3.0` so issue-templates reference this version's links.

## C. Within 24 hours
- [ ] Update README's badges: pointer-badge pinned to v0.3.0 commit SHA.
- [ ] Publish `site/press/2026-09-30-v0.3.0.md` (PR + deploy).
- [ ] Email announcement to the maintainer list.
- [ ] Post in `#release` matrix channel.
- [ ] Mark `release/v0.3.0` branch as **read-only** in GitHub settings.

## D. Within 7 days
- [ ] First sweep-bot report has run.
- [ ] First weekly postmortem slot booked in the calendar.
