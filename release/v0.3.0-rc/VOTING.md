# Voting — v0.3.0

## Outcome recorded in `manifest.json` -> "vote"

```json
{
  "round": 3,
  "voters": ["alice", "bob", "carol"],
  "decisions": [
    {"voter":"alice", "vote":"yes", "ts":"2026-09-29T12:00Z", "note":""},
    {"voter":"bob",   "vote":"yes", "ts":"2026-09-29T12:01Z", "note":""},
    {"voter":"carol", "vote":"yes", "ts":"2026-09-29T12:02Z", "note":""}
  ],
  "result": "ACCEPT"
}
```

* `ACCEPT` if >= 2 YES.
* `REJECT` if NO+YES ties.
* `BLOCK` if any voter flags Sev-1.
