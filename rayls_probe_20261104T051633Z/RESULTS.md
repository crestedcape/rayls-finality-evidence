# Rayls finality probe results

- Run started: 2026-11-04T05:16:33.879Z
- Run finished: 2026-11-04T05:17:07.846Z
- Endpoint: https://mainnet-rpc.rayls.com
- Chain ID: 72957
- Client version: 1.4.2 (b19896a12cfc1f1f775c33196c940f3345c00ede)
- Script: rayls_finality_probe.py v1.0, Python 3.14.8

## Cadence (read-only)

```
{
 "samples": 37,
 "poll_ms_requested": 200,
 "duration_s": 29.942,
 "evm_first": 13814712,
 "evm_last": 13814734,
 "evm_blocks_advanced": 22,
 "evm_blocks_per_s": 0.735,
 "rayls_latestHeader": "no usable responses (method not exposed on this endpoint?)"
}
```

Header changes are counted when two polls return different rayls_latestHeader responses, so they are a
lower bound set by the poll interval. If the median gap is close to the poll interval, rerun with a
smaller --cadence-poll-ms.

## Committee snapshots (read-only)

```
{
 "1": {
  "candidate_committee_sizes": [
   [
    "$[0].committee",
    7
   ],
   [
    "$[0].next_committee",
    7
   ]
  ],
  "shape": [
   [
    "$",
    "array",
    2
   ],
   [
    "$[0]",
    "object",
    6
   ],
   [
    "$[0].committee",
    "array",
    7
   ],
   [
    "$[0].next_committee",
    "array",
    7
   ],
   [
    "$[0].parent_state",
    "object",
    2
   ],
   [
    "$[1]",
    "object",
    3
   ]
  ]
 },
 "50": {
  "candidate_committee_sizes": [
   [
    "$[0].committee",
    7
   ],
   [
    "$[0].next_committee",
    7
   ]
  ],
  "shape": [
   [
    "$",
    "array",
    2
   ],
   [
    "$[0]",
    "object",
    6
   ],
   [
    "$[0].committee",
    "array",
    7
   ],
   [
    "$[0].next_committee",
    "array",
    7
   ],
   [
    "$[0].parent_state",
    "object",
    2
   ],
   [
    "$[1]",
    "object",
    3
   ]
  ]
 },
 "100": {
  "candidate_committee_sizes": [
   [
    "$[0].committee",
    7
   ],
   [
    "$[0].next_committee",
    7
   ]
  ],
  "shape": [
   [
    "$",
    "array",
    2
   ],
   [
    "$[0]",
    "object",
    6
   ],
   [
    "$[0].committee",
    "array",
    7
   ],
   [
    "$[0].next_committee",
    "array",
    7
   ],
   [
    "$[0].parent_state",
    "object",
    2
   ],
   [
    "$[1]",
    "object",
    3
   ]
  ]
 },
 "150": {
  "candidate_committee_sizes": [
   [
    "$[0].committee",
    7
   ],
   [
    "$[0].next_committee",
    7
   ]
  ],
  "shape": [
   [
    "$",
    "array",
    2
   ],
   [
    "$[0]",
    "object",
    6
   ],
   [
    "$[0].committee",
    "array",
    7
   ],
   [
    "$[0].next_committee",
    "array",
    7
   ],
   [
    "$[0].parent_state",
    "object",
    2
   ],
   [
    "$[1]",
    "object",
    3
   ]
  ]
 }
}
```

Candidate sizes are lengths of fields whose names look like committee or validator lists. Open the
epoch_record_*.json files to confirm which field is the committee.

## Limits

- Times are measured on the client, so they include network round trips and polling delay.
- One machine, one region, one run. Small samples do not describe production reliability.
- A public RPC endpoint may rate-limit, cache or not expose the rayls_ methods.
- Block timestamps are whole seconds, so sub-second claims need client-side timing like the above.
