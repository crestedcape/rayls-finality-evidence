# Rayls finality probe results

- Run started: 2026-11-04T14:55:53.275Z
- Run finished: 2026-11-04T14:57:09.656Z
- Endpoint: https://mainnet-rpc.rayls.com
- Chain ID: 72957
- Client version: 1.4.2 (b19896a12cfc1f1f775c33196c940f3345c00ede)
- Script: rayls_finality_probe_v2.py v2.0, Python 3.14.8

## Cadence (read-only)

```
{
 "samples": 197,
 "poll_ms_requested": 200,
 "median_rpc_round_trip_s": 0.287,
 "duration_s": 59.562,
 "evm_first": 13840627,
 "evm_last": 13840674,
 "evm_blocks_advanced": 47,
 "evm_blocks_per_s": 0.789,
 "implied_seconds_per_block": 1.267,
 "blocks_gained_between_polls_histogram": {
  "1": 44,
  "0": 151,
  "3": 1
 },
 "rayls_latestHeader": {
  "usable": false,
  "first_error": {
   "code": -32603,
   "message": "Internal error"
  }
 }
}
```

Header changes are counted when two polls return different rayls_latestHeader responses, so they are a
lower bound set by the poll interval.

## Epoch history (read-only)

```
{
 "newest_epoch_with_a_record": 187,
 "epochs_sampled": 21,
 "committee_sizes_seen": [
  7,
  8
 ],
 "distinct_member_keys_seen_in_all_samples": 8,
 "committee_member_set_changes_between_samples": [
  {
   "between_epochs": [
    170,
    180
   ],
   "size": [
    7,
    8
   ]
  }
 ],
 "epochs_where_next_committee_differs_from_committee": [],
 "signers_per_record_min_median_max": [
  5,
  6,
  7
 ],
 "block_time_spans": [
  {
   "epochs": [
    0,
    1
   ],
   "blocks_per_epoch": 66845,
   "implied_seconds_per_block_if_epoch_is_24h": 1.293
  },
  {
   "epochs": [
    1,
    10
   ],
   "blocks_per_epoch": 62748,
   "implied_seconds_per_block_if_epoch_is_24h": 1.377
  },
  {
   "epochs": [
    10,
    20
   ],
   "blocks_per_epoch": 65908,
   "implied_seconds_per_block_if_epoch_is_24h": 1.311
  },
  {
   "epochs": [
    20,
    30
   ],
   "blocks_per_epoch": 66131,
   "implied_seconds_per_block_if_epoch_is_24h": 1.306
  },
  {
   "epochs": [
    30,
    40
   ],
   "blocks_per_epoch": 66160,
   "implied_seconds_per_block_if_epoch_is_24h": 1.306
  },
  {
   "epochs": [
    40,
    50
   ],
   "blocks_per_epoch": 66183,
   "implied_seconds_per_block_if_epoch_is_24h": 1.305
  },
  {
   "epochs": [
    50,
    60
   ],
   "blocks_per_epoch": 63748,
   "implied_seconds_per_block_if_epoch_is_24h": 1.355
  },
  {
   "epochs": [
    60,
    70
   ],
   "blocks_per_epoch": 66584,
   "implied_seconds_per_block_if_epoch_is_24h": 1.298
  },
  {
   "epochs": [
    70,
    80
   ],
   "blocks_per_epoch": 66621,
   "implied_seconds_per_block_if_epoch_is_24h": 1.297
  },
  {
   "epochs": [
    80,
    90
   ],
   "blocks_per_epoch": 66565,
   "implied_seconds_per_block_if_epoch_is_24h": 1.298
  },
  {
   "epochs": [
    90,
    100
   ],
   "blocks_per_epoch": 66476,
   "implied_seconds_per_block_if_epoch_is_24h": 1.3
  },
  {
   "epochs": [
    100,
    110
   ],
   "blocks_per_epoch": 66403,
   "implied_seconds_per_block_if_epoch_is_24h": 1.301
  },
  {
   "epochs": [
    110,
    120
   ],
   "blocks_per_epoch": 66376,
   "implied_seconds_per_block_if_epoch_is_24h": 1.302
  },
  {
   "epochs": [
    120,
    130
   ],
   "blocks_per_epoch": 66568,
   "implied_seconds_per_block_if_epoch_is_24h": 1.298
  },
  {
   "epochs": [
    130,
    140
   ],
   "blocks_per_epoch": 107176,
   "implied_seconds_per_block_if_epoch_is_24h": 0.806
  },
  {
   "epochs": [
    140,
    150
   ],
   "blocks_per_epoch": 124147,
   "implied_seconds_per_block_if_epoch_is_24h": 0.696
  },
  {
   "epochs": [
    150,
    160
   ],
   "blocks_per_epoch": 115907,
   "implied_seconds_per_block_if_epoch_is_24h": 0.745
  },
  {
   "epochs": [
    160,
    170
   ],
   "blocks_per_epoch": 65067,
   "implied_seconds_per_block_if_epoch_is_24h": 1.328
  },
  {
   "epochs": [
    170,
    180
   ],
   "blocks_per_epoch": 63786,
   "implied_seconds_per_block_if_epoch_is_24h": 1.355
  },
  {
   "epochs": [
    180,
    187
   ],
   "blocks_per_epoch": 64204,
   "implied_seconds_per_block_if_epoch_is_24h": 1.346
  }
 ],
 "implied_seconds_per_block_min_median_max": [
  0.696,
  1.301,
  1.377
 ]
}
```

Blocks per epoch come from parent_state block numbers and assume 24-hour epochs, as the Rayls docs state.
Signer positions are decoded from the signed_authorities bitmap. See epoch_history.csv for every sample.

## Limits

- Times are measured on the client, so they include network round trips and polling delay.
- One machine, one region, one run. Small samples do not describe production reliability.
- A public RPC endpoint may rate-limit, cache or not expose the rayls_ methods.
- Block timestamps are whole seconds, so sub-second claims need client-side timing like the above.
