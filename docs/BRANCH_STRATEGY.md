# Branch strategy

## Trunk + release branches

| Branch | Owner | Lifetime | May merge into… |
| ------- | ----- | -------- | --------------- |
| `master` | bot + maintainer | always | releases only |
| `release/X.Y.Z` | release captain | until tagged | `master` |
| `feature/<name>` | contributor | until merged | `master` |
| `fix/<issue>-<slug>` | maintainer | until merged | `master` |
| `bot/sweep-*` | sweep bot | ephemeral (≤1 d) | `master` |

## Rules

1. `master` is **always deployable**. Required CI = lint, types, unit, migration, demo reel.
2. Releases are cherry-pick-free: every commit on `release/vX.Y.Z` is also on `master`.
3. Bot PRs must include the issue tracker IDs in the title.

## Tag protection

* `vX.Y.Z` tags are immutable.
* Force-push to `master` is blocked.
* `release.yml` runs on tag push (Deliverable J).
