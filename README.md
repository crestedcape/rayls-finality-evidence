# Rayls finality evidence

Read-only measurements of Rayls mainnet taken on 4 and 5 November 2026, with the scripts that produced them.

Article: (add the link here after you publish it)

## What is here

- `rayls_finality_probe.py`, `rayls_finality_probe_v2.py`, `rayls_finality_probe_v3.py`: three versions of the same script. Each run is read-only and sends no transactions unless you pass `--send`.
- One folder per run, named `rayls_probe_<UTC timestamp>`:
  - Run 1, 4 November, about 05:17 UTC (v1): 30 seconds of block pace and committees for epochs 1, 50, 100 and 150.
  - Run 2, 4 November, about 14:56 UTC (v2): 60 seconds of block pace and a scan of 21 epochs.
  - Run 3, 5 November, about 00:35 UTC (v3): adds block timestamps at epoch boundaries and samples the newest 16 epochs.
- Each run folder holds `RESULTS.md` (summary), `raw_rpc_log.jsonl` (every request and response with timings), CSV files, the epoch records as JSON, and `SHA256SUMS.txt`.

## Headline results

| Measurement | Result |
| --- | --- |
| Block pace in three live windows | One block every 1.36 s, 1.27 s and 1.37 s |
| Epoch length (block timestamps at 35 epoch boundaries) | 86,400 or 86,401 seconds in all 16 consecutive pairs |
| Block pace over time | 1.31 s per block (epochs 0 to 130), 0.75 s (130 to 160), 1.34 s (160 to 188) |
| Committee | The same 7 keys from epoch 0 to 170, then 8 members from epoch 172 or 173 |
| Signers per epoch record | 5 to 8, and all 35 records meet the quorum for their committee size |

## Check the files

- Windows: run `certutil -hashfile <file> SHA256` and compare the result with the line for that file in `SHA256SUMS.txt`.
- Mac or Linux: run `sha256sum -c SHA256SUMS.txt` inside a run folder.

The checksums show the files were not changed after the script wrote them. They do not prove the chain data is true. To check that, repeat the queries yourself against `https://mainnet-rpc.rayls.com`.

## Limits

- One public RPC endpoint, one machine, one connection, three short windows.
- Signer positions assume the bitmap follows the order of the committee list. No signature was verified.
- No transactions were sent, so there is no submit-to-receipt latency here.
- `rayls_latestHeader` returned an internal error, so commit pace was not measured directly.
- Block pace in the three live windows was measured on a quiet chain, not under load.
