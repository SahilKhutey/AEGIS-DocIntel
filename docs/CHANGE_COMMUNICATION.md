# How we communicate changes

| Audience | Channel | When |
| -------- | ------- | ---- |
| Operators | GitHub Releases + CHANGELOG.md | Every release |
| Operators (urgent) | `#aegis-docintel-ops` Matrix + email | Sev-1 / Sev-2 incidents |
| SDK consumers | PyPI / npm / Maven / Conan + GHSA | Patch + minor versions |
| Helm users | Artifact Hub annotations + GHSA | Every chart version |
| UI users | UI banner + Settings page changelog | Every minor / major |

## Routine cadence

* **Patch versions** ship without announcement.
* **Minor versions** ship with a one-page summary email.
* **Major versions** ship with a 14-day migration window and a live
  walkthrough webinar.

## Template for the one-page summary

```
## What's in v0.X.0
- ...

## What breaks
- ...

## How to upgrade
- ...

## Things to test before deploying
- ...
```
