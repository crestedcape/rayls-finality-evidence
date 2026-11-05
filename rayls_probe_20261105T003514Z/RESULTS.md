# Rayls finality probe results

- Run started: 2026-11-05T00:35:14.315Z
- Run finished: 2026-11-05T00:36:52.913Z
- Endpoint: https://mainnet-rpc.rayls.com
- Chain ID: 72957
- Client version: 1.4.2 (b19896a12cfc1f1f775c33196c940f3345c00ede)
- Script: rayls_finality_probe_v3.py v3.0, Python 3.14.8

## Cadence (read-only)

```
{
 "samples": 158,
 "poll_ms_requested": 200,
 "median_rpc_round_trip_s": 0.33,
 "duration_s": 59.033,
 "evm_first": 13866579,
 "evm_last": 13866622,
 "evm_blocks_advanced": 43,
 "evm_blocks_per_s": 0.728,
 "implied_seconds_per_block": 1.373,
 "blocks_gained_between_polls_histogram": {
  "0": 114,
  "1": 43
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
 "newest_epoch_with_a_record": 188,
 "epochs_sampled": 35,
 "chain_start_block_time_utc": "2026-04-30T15:58:22Z",
 "newest_epoch_boundary_time_utc": "2026-11-04T15:59:02Z",
 "committee_sizes_seen": [
  7,
  8
 ],
 "distinct_member_keys_seen_in_all_samples": 8,
 "committee_member_set_changes_between_samples": [
  {
   "between_epochs": [
    170,
    173
   ],
   "size": [
    7,
    8
   ],
   "pinned_to_one_epoch": false,
   "new_set_first_seen_epoch": 173,
   "boundary_block_time_utc_of_that_epoch": "2026-10-20T15:58:56Z"
  }
 ],
 "epochs_where_next_committee_differs_from_committee": [],
 "signers_per_record_min_median_max": [
  5,
  6,
  8
 ],
 "records_below_quorum": [],
 "timestamp_lookups_failed": 0,
 "measured_seconds_per_epoch_min_median_max": [
  86400,
  86400.0,
  86401
 ],
 "measured_seconds_per_block_min_median_max": [
  0.696,
  1.342,
  1.458
 ],
 "implied_seconds_per_block_if_24h_min_median_max": [
  0.696,
  1.342,
  1.458
 ],
 "block_time_spans": [
  {
   "epochs": [
    0,
    1
   ],
   "blocks_per_epoch": 66845,
   "implied_seconds_per_block_if_epoch_is_24h": 1.293,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.293
  },
  {
   "epochs": [
    1,
    10
   ],
   "blocks_per_epoch": 62748,
   "implied_seconds_per_block_if_epoch_is_24h": 1.377,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.377
  },
  {
   "epochs": [
    10,
    20
   ],
   "blocks_per_epoch": 65908,
   "implied_seconds_per_block_if_epoch_is_24h": 1.311,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.311
  },
  {
   "epochs": [
    20,
    30
   ],
   "blocks_per_epoch": 66131,
   "implied_seconds_per_block_if_epoch_is_24h": 1.306,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.307
  },
  {
   "epochs": [
    30,
    40
   ],
   "blocks_per_epoch": 66160,
   "implied_seconds_per_block_if_epoch_is_24h": 1.306,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.306
  },
  {
   "epochs": [
    40,
    50
   ],
   "blocks_per_epoch": 66183,
   "implied_seconds_per_block_if_epoch_is_24h": 1.305,
   "measured_seconds_per_epoch": 86401,
   "measured_seconds_per_block": 1.305
  },
  {
   "epochs": [
    50,
    60
   ],
   "blocks_per_epoch": 63748,
   "implied_seconds_per_block_if_epoch_is_24h": 1.355,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.355
  },
  {
   "epochs": [
    60,
    70
   ],
   "blocks_per_epoch": 66584,
   "implied_seconds_per_block_if_epoch_is_24h": 1.298,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.298
  },
  {
   "epochs": [
    70,
    80
   ],
   "blocks_per_epoch": 66621,
   "implied_seconds_per_block_if_epoch_is_24h": 1.297,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.297
  },
  {
   "epochs": [
    80,
    90
   ],
   "blocks_per_epoch": 66565,
   "implied_seconds_per_block_if_epoch_is_24h": 1.298,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.298
  },
  {
   "epochs": [
    90,
    100
   ],
   "blocks_per_epoch": 66476,
   "implied_seconds_per_block_if_epoch_is_24h": 1.3,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.3
  },
  {
   "epochs": [
    100,
    110
   ],
   "blocks_per_epoch": 66403,
   "implied_seconds_per_block_if_epoch_is_24h": 1.301,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.301
  },
  {
   "epochs": [
    110,
    120
   ],
   "blocks_per_epoch": 66376,
   "implied_seconds_per_block_if_epoch_is_24h": 1.302,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.302
  },
  {
   "epochs": [
    120,
    130
   ],
   "blocks_per_epoch": 66568,
   "implied_seconds_per_block_if_epoch_is_24h": 1.298,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.298
  },
  {
   "epochs": [
    130,
    140
   ],
   "blocks_per_epoch": 107176,
   "implied_seconds_per_block_if_epoch_is_24h": 0.806,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 0.806
  },
  {
   "epochs": [
    140,
    150
   ],
   "blocks_per_epoch": 124147,
   "implied_seconds_per_block_if_epoch_is_24h": 0.696,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 0.696
  },
  {
   "epochs": [
    150,
    160
   ],
   "blocks_per_epoch": 115907,
   "implied_seconds_per_block_if_epoch_is_24h": 0.745,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 0.745
  },
  {
   "epochs": [
    160,
    170
   ],
   "blocks_per_epoch": 65067,
   "implied_seconds_per_block_if_epoch_is_24h": 1.328,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.328
  },
  {
   "epochs": [
    170,
    173
   ],
   "blocks_per_epoch": 64316,
   "implied_seconds_per_block_if_epoch_is_24h": 1.343,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.343
  },
  {
   "epochs": [
    173,
    174
   ],
   "blocks_per_epoch": 64239,
   "implied_seconds_per_block_if_epoch_is_24h": 1.345,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.345
  },
  {
   "epochs": [
    174,
    175
   ],
   "blocks_per_epoch": 64378,
   "implied_seconds_per_block_if_epoch_is_24h": 1.342,
   "measured_seconds_per_epoch": 86401,
   "measured_seconds_per_block": 1.342
  },
  {
   "epochs": [
    175,
    176
   ],
   "blocks_per_epoch": 64369,
   "implied_seconds_per_block_if_epoch_is_24h": 1.342,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.342
  },
  {
   "epochs": [
    176,
    177
   ],
   "blocks_per_epoch": 64299,
   "implied_seconds_per_block_if_epoch_is_24h": 1.344,
   "measured_seconds_per_epoch": 86401,
   "measured_seconds_per_block": 1.344
  },
  {
   "epochs": [
    177,
    178
   ],
   "blocks_per_epoch": 64154,
   "implied_seconds_per_block_if_epoch_is_24h": 1.347,
   "measured_seconds_per_epoch": 86401,
   "measured_seconds_per_block": 1.347
  },
  {
   "epochs": [
    178,
    179
   ],
   "blocks_per_epoch": 64209,
   "implied_seconds_per_block_if_epoch_is_24h": 1.346,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.346
  },
  {
   "epochs": [
    179,
    180
   ],
   "blocks_per_epoch": 59263,
   "implied_seconds_per_block_if_epoch_is_24h": 1.458,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.458
  },
  {
   "epochs": [
    180,
    181
   ],
   "blocks_per_epoch": 64100,
   "implied_seconds_per_block_if_epoch_is_24h": 1.348,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.348
  },
  {
   "epochs": [
    181,
    182
   ],
   "blocks_per_epoch": 64180,
   "implied_seconds_per_block_if_epoch_is_24h": 1.346,
   "measured_seconds_per_epoch": 86401,
   "measured_seconds_per_block": 1.346
  },
  {
   "epochs": [
    182,
    183
   ],
   "blocks_per_epoch": 64148,
   "implied_seconds_per_block_if_epoch_is_24h": 1.347,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.347
  },
  {
   "epochs": [
    183,
    184
   ],
   "blocks_per_epoch": 64171,
   "implied_seconds_per_block_if_epoch_is_24h": 1.346,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.346
  },
  {
   "epochs": [
    184,
    185
   ],
   "blocks_per_epoch": 64336,
   "implied_seconds_per_block_if_epoch_is_24h": 1.343,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.343
  },
  {
   "epochs": [
    185,
    186
   ],
   "blocks_per_epoch": 64235,
   "implied_seconds_per_block_if_epoch_is_24h": 1.345,
   "measured_seconds_per_epoch": 86400,
   "measured_seconds_per_block": 1.345
  },
  {
   "epochs": [
    186,
    187
   ],
   "blocks_per_epoch": 64257,
   "implied_seconds_per_block_if_epoch_is_24h": 1.345,
   "measured_seconds_per_epoch": 86401,
   "measured_seconds_per_block": 1.345
  },
  {
   "epochs": [
    187,
    188
   ],
   "blocks_per_epoch": 64399,
   "implied_seconds_per_block_if_epoch_is_24h": 1.342,
   "measured_seconds_per_epoch": 86401,
   "measured_seconds_per_block": 1.342
  }
 ]
}
```

Blocks per epoch come from parent_state block numbers. Measured values use block timestamps at epoch boundaries;
implied values assume 24-hour epochs, as the Rayls docs state.
Signer positions are decoded from the signed_authorities bitmap. See epoch_history.csv for every sample.

## Limits

- Times are measured on the client, so they include network round trips and polling delay.
- One machine, one region, one run. Small samples do not describe production reliability.
- A public RPC endpoint may rate-limit, cache or not expose the rayls_ methods.
- Block timestamps are whole seconds, so sub-second claims need client-side timing like the above.
