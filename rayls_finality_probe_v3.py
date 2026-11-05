#!/usr/bin/env python3
"""Rayls finality probe: first-hand, timestamped evidence from a Rayls (Axyl) RPC endpoint.

Version 3 also reads block timestamps at epoch boundaries (so epoch length and block time are
measured, not assumed) and samples every one of the newest epochs to pin down committee changes.
Steps 1-3 are read-only and need only the Python standard library:
  1. identity   chain id, client version, latest EVM block
  2. cadence    how fast EVM blocks (and consensus headers, if exposed) advance
  3. history    finds the newest epoch, then samples committees across all epochs:
                committee size, whether the member keys ever changed, how many members
                signed each epoch record, and the average block time implied by
                parent_state block numbers (epochs last 24 hours per the Rayls docs)
Step 4 is optional and sends real transactions:
  4. latency    N timed 1-wei self-transfers, submit -> receipt.
                Needs: pip install eth-account, a THROWAWAY private key in the env var
                RAYLS_TEST_KEY, and a small balance of the gas token (USDr on mainnet).

Output: a folder with raw call logs, CSVs, RESULTS.md and SHA256SUMS.txt.
The folder never contains your private key. Read it before you publish it.
Example: python3 rayls_finality_probe_v3.py          (read-only)
         python3 rayls_finality_probe_v3.py --send 20  (also times real transfers)
"""
import argparse, csv, hashlib, json, math, os, platform, re, statistics, sys, time, urllib.request
from datetime import datetime, timezone

VERSION = "3.0"
DEFAULT_RPC = "https://mainnet-rpc.rayls.com"


def iso(t=None):
    t = time.time() if t is None else t
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class Rpc:
    """Minimal JSON-RPC client that logs every request and response."""

    def __init__(self, url, log_path, timeout=20):
        self.url, self.timeout, self.n = url, timeout, 0
        self.log = open(log_path, "w", encoding="utf-8")

    def call(self, method, params=None):
        self.n += 1
        body = {"jsonrpc": "2.0", "id": self.n, "method": method, "params": params or []}
        req = urllib.request.Request(
            self.url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "rayls-finality-probe/" + VERSION})
        t_wall, t0 = time.time(), time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                text = r.read().decode("utf-8", "replace")
            try:
                resp = json.loads(text)
            except ValueError:
                resp = {"non_json_response": text[:300]}
        except Exception as e:  # network or HTTP error
            resp = {"transport_error": repr(e)}
        rtt = time.perf_counter() - t0
        self.log.write(json.dumps({"t_utc": iso(t_wall), "rtt_s": round(rtt, 4),
                                   "request": body, "response": resp}) + "\n")
        self.log.flush()
        return resp, rtt


def ok(resp):
    return isinstance(resp, dict) and resp.get("result") is not None


def to_int(x):
    try:
        return int(x, 16) if isinstance(x, str) and x.startswith("0x") else int(x)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- step 1
def identity(rpc):
    info = {}
    for key, method in (("chain_id", "eth_chainId"), ("client_version", "web3_clientVersion"),
                        ("latest_block", "eth_blockNumber")):
        r, _ = rpc.call(method)
        info[key] = r["result"] if ok(r) else {"error": r.get("error") or r}
    info["chain_id_decimal"] = to_int(info["chain_id"]) if isinstance(info["chain_id"], str) else None
    return info


# ---------------------------------------------------------------- step 2
def find_number(obj, keys=("number", "block_number", "blockNumber", "consensus_number")):
    queue = [obj]
    while queue:
        o = queue.pop(0)
        if isinstance(o, dict):
            for k in keys:
                v = to_int(o.get(k)) if o.get(k) is not None else None
                if v is not None:
                    return v
            queue.extend(o.values())
        elif isinstance(o, list):
            queue.extend(o[:5])
    return None


def cadence(rpc, seconds, poll_ms, outdir):
    rows, rtts, start = [], [], time.perf_counter()
    next_tick = start
    header_ok, header_error = True, None
    while time.perf_counter() - start < seconds:
        b, rtt_b = rpc.call("eth_blockNumber")
        rtts.append(rtt_b)
        hdr = None
        if header_ok:
            h, rtt_h = rpc.call("rayls_latestHeader")
            rtts.append(rtt_h)
            if ok(h):
                hdr = h["result"]
            else:
                header_ok, header_error = False, h.get("error") or h  # stop asking, keep the reason
        t = time.perf_counter() - start
        rows.append({"t_s": round(t, 3),
                     "evm_block": to_int(b["result"]) if ok(b) else None,
                     "header_sha256": sha256_bytes(canon(hdr).encode())[:16] if hdr is not None else "",
                     "consensus_number": find_number(hdr) if hdr is not None else ""})
        next_tick += poll_ms / 1000
        time.sleep(max(0, next_tick - time.perf_counter()))
    with open(os.path.join(outdir, "cadence_samples.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["t_s", "evm_block", "header_sha256", "consensus_number"])
        w.writeheader()
        w.writerows(rows)
    out = {"samples": len(rows), "poll_ms_requested": poll_ms,
           "median_rpc_round_trip_s": round(statistics.median(rtts), 3) if rtts else None}
    dt = rows[-1]["t_s"] - rows[0]["t_s"] if len(rows) > 1 else 0
    out["duration_s"] = round(dt, 3)
    blks = [r["evm_block"] for r in rows if r["evm_block"] is not None]
    if len(blks) > 1 and dt:
        adv = blks[-1] - blks[0]
        out.update(evm_first=blks[0], evm_last=blks[-1], evm_blocks_advanced=adv,
                   evm_blocks_per_s=round(adv / dt, 3),
                   implied_seconds_per_block=round(dt / adv, 3) if adv else None)
        hist = {}
        for a, b2 in zip(blks, blks[1:]):
            hist[str(b2 - a)] = hist.get(str(b2 - a), 0) + 1
        out["blocks_gained_between_polls_histogram"] = hist
    if not header_ok:
        out["rayls_latestHeader"] = {"usable": False, "first_error": header_error}
    else:
        hdrs = [(r["t_s"], r["header_sha256"]) for r in rows if r["header_sha256"]]
        changes = [t for (t, h), (_, hp) in zip(hdrs[1:], hdrs[:-1]) if h != hp]
        gaps = [b2 - a for a, b2 in zip(changes, changes[1:])]
        out["rayls_latestHeader"] = {"usable": True, "changes_observed": len(changes),
                                     "median_gap_between_observed_changes_s": round(statistics.median(gaps), 3) if gaps else None}
    return out


# ---------------------------------------------------------------- step 3
A58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(text):
    n = 0
    for ch in text:
        n = n * 58 + A58.index(ch)
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * (len(text) - len(text.lstrip("1"))) + body


def roaring_positions(b):
    """Decode a portable Roaring bitmap made of array containers (what a small signer set uses)."""
    try:
        if int.from_bytes(b[0:4], "little") != 12346:
            return None
        size, pos, desc = int.from_bytes(b[4:8], "little"), 8, []
        for _ in range(size):
            desc.append((int.from_bytes(b[pos:pos + 2], "little"), int.from_bytes(b[pos + 2:pos + 4], "little") + 1))
            pos += 4
        offs = []
        for _ in range(size):
            offs.append(int.from_bytes(b[pos:pos + 4], "little"))
            pos += 4
        out = []
        for (key, card), off in zip(desc, offs):
            if card > 4096:
                return None
            out += [(key << 16) | int.from_bytes(b[off + 2 * i:off + 2 * i + 2], "little") for i in range(card)]
        return sorted(out)
    except Exception:
        return None


def parse_epoch(resp):
    res = resp.get("result") if isinstance(resp, dict) else None
    rec = cert = None
    for it in (res if isinstance(res, list) else [res]):
        if isinstance(it, dict):
            rec = it if "committee" in it else rec
            cert = it if "signed_authorities" in it else cert
    return rec, cert


def newest_epoch(rpc, cap=20000):
    def exists(e):
        return parse_epoch(rpc.call("rayls_epochRecord", [e])[0])[0] is not None
    if not exists(1):
        return None
    lo, hi = 1, 2
    while hi < cap and exists(hi):
        lo, hi = hi, hi * 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if exists(mid) else (lo, mid)
    return lo


def fingerprint(keys):
    return sha256_bytes("|".join(sorted(keys)).encode())[:12]


def history(rpc, step, extra, tail, want_ts, outdir):
    newest = newest_epoch(rpc)
    if newest is None:
        return {"error": "rayls_epochRecord gave no usable answer, so no committee history could be read"}
    recent = list(range(max(2, newest - tail + 1), newest + 1)) if tail > 0 else []
    epochs = sorted(set([0, 1] + list(range(step, newest + 1, step)) + [newest] + extra + recent))
    rows, all_keys = [], set()
    for e in epochs:
        resp, _ = rpc.call("rayls_epochRecord", [e])
        rec, cert = parse_epoch(resp)
        if rec is None:
            rows.append({"epoch": e, "note": "no record"})
            continue
        with open(os.path.join(outdir, f"epoch_record_{e}.json"), "w") as f:
            json.dump(resp, f, indent=1)
        com, nxt = rec.get("committee") or [], rec.get("next_committee") or []
        all_keys.update(com)
        pos = roaring_positions(b58decode(cert["signed_authorities"])) if cert and cert.get("signed_authorities") else None
        rows.append({"epoch": e, "committee_size": len(com), "next_committee_size": len(nxt),
                     "committee_id": fingerprint(com), "next_committee_id": fingerprint(nxt),
                     "parent_state_block": (rec.get("parent_state") or {}).get("number"),
                     "signer_positions": " ".join(map(str, pos)) if pos is not None else "",
                     "signers": len(pos) if pos is not None else ""})
    ts_errors = 0
    if want_ts:
        for r in rows:
            b = r.get("parent_state_block")
            if isinstance(b, int):
                resp, _ = rpc.call("eth_getBlockByNumber", [hex(b), False])
                res = resp.get("result") if isinstance(resp, dict) else None
                ts = to_int(res.get("timestamp")) if isinstance(res, dict) else None
                if ts is None:
                    ts_errors += 1
                r["boundary_unix"] = ts if ts is not None else ""
                r["boundary_utc"] = iso(ts)[:19] + "Z" if ts is not None else ""
    cols = ["epoch", "committee_size", "next_committee_size", "committee_id", "next_committee_id",
            "parent_state_block", "boundary_unix", "boundary_utc", "signer_positions", "signers", "note"]
    with open(os.path.join(outdir, "epoch_history.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    good = [r for r in rows if "committee_size" in r]
    changes = []
    for a, b in zip(good, good[1:]):
        if a["committee_id"] != b["committee_id"]:
            changes.append({"between_epochs": [a["epoch"], b["epoch"]], "size": [a["committee_size"], b["committee_size"]],
                            "pinned_to_one_epoch": b["epoch"] - a["epoch"] == 1,
                            "new_set_first_seen_epoch": b["epoch"],
                            "boundary_block_time_utc_of_that_epoch": b.get("boundary_utc", "")})
    spans = []
    for a, b in zip(good, good[1:]):
        if isinstance(a["parent_state_block"], int) and isinstance(b["parent_state_block"], int) and b["epoch"] > a["epoch"]:
            de, db = b["epoch"] - a["epoch"], b["parent_state_block"] - a["parent_state_block"]
            if db > 0:
                sp = {"epochs": [a["epoch"], b["epoch"]], "blocks_per_epoch": round(db / de),
                      "implied_seconds_per_block_if_epoch_is_24h": round(86400 * de / db, 3)}
                ta, tb = a.get("boundary_unix"), b.get("boundary_unix")
                if isinstance(ta, int) and isinstance(tb, int) and tb > ta:
                    sp["measured_seconds_per_epoch"] = round((tb - ta) / de)
                    sp["measured_seconds_per_block"] = round((tb - ta) / db, 3)
                spans.append(sp)

    def mmm(vals):
        return [min(vals), round(statistics.median(vals), 3), max(vals)] if vals else None
    sig = [r["signers"] for r in good if isinstance(r["signers"], int)]
    below_quorum = [r["epoch"] for r in good if isinstance(r["signers"], int) and r["signers"] < (2 * r["committee_size"]) // 3 + 1]
    first = next((r for r in good if r["epoch"] == 0), None)
    return {"newest_epoch_with_a_record": newest, "epochs_sampled": len(good),
            "chain_start_block_time_utc": first.get("boundary_utc", "") if first else "",
            "newest_epoch_boundary_time_utc": good[-1].get("boundary_utc", "") if good else "",
            "committee_sizes_seen": sorted(set(r["committee_size"] for r in good)),
            "distinct_member_keys_seen_in_all_samples": len(all_keys),
            "committee_member_set_changes_between_samples": changes,
            "epochs_where_next_committee_differs_from_committee": [r["epoch"] for r in good if r["committee_id"] != r["next_committee_id"]],
            "signers_per_record_min_median_max": mmm(sig),
            "records_below_quorum": below_quorum,
            "timestamp_lookups_failed": ts_errors if want_ts else "not requested",
            "measured_seconds_per_epoch_min_median_max": mmm([x["measured_seconds_per_epoch"] for x in spans if "measured_seconds_per_epoch" in x]),
            "measured_seconds_per_block_min_median_max": mmm([x["measured_seconds_per_block"] for x in spans if "measured_seconds_per_block" in x]),
            "implied_seconds_per_block_if_24h_min_median_max": mmm([x["implied_seconds_per_block_if_epoch_is_24h"] for x in spans]),
            "block_time_spans": spans}


# ---------------------------------------------------------------- step 4
def pct(sorted_vals, q):  # nearest-rank percentile
    return sorted_vals[max(1, math.ceil(q * len(sorted_vals))) - 1]


def timed_transfers(rpc, n, poll_ms, outdir, assume_yes):
    try:
        from eth_account import Account
    except ImportError:
        sys.exit("Step 4 needs: pip install eth-account")
    key = os.environ.get("RAYLS_TEST_KEY")
    if not key:
        sys.exit("Set RAYLS_TEST_KEY to a THROWAWAY private key. Never use your main wallet.")
    acct = Account.from_key(key)
    chain_id = to_int(rpc.call("eth_chainId")[0].get("result"))
    bal = to_int(rpc.call("eth_getBalance", [acct.address, "latest"])[0].get("result")) or 0
    print(f"Sender and recipient: {acct.address}\nBalance: {bal} wei of the gas token")
    if bal == 0:
        sys.exit("Balance is 0. Fund this throwaway address with a small amount of the gas token, or skip --send.")
    if not assume_yes:
        input(f"About to send {n} real self-transfers of 1 wei. Enter to continue, Ctrl+C to abort: ")
    nonce = to_int(rpc.call("eth_getTransactionCount", [acct.address, "pending"])[0].get("result"))
    rows = []
    for i in range(n):
        gp = to_int(rpc.call("eth_gasPrice")[0].get("result")) or 0
        tx = {"to": acct.address, "value": 1, "gas": 21000, "gasPrice": int(gp * 1.25) + 1,
              "nonce": nonce, "chainId": chain_id}
        signed = acct.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        t_wall, p0 = time.time(), time.perf_counter()
        r, _ = rpc.call("eth_sendRawTransaction", ["0x" + bytes(raw).hex()])
        p_acc = time.perf_counter()
        if not ok(r):
            print("Send failed:", r.get("error") or r)
            break
        txh, receipt = r["result"], None
        while time.perf_counter() - p0 < 60:
            rr, _ = rpc.call("eth_getTransactionReceipt", [txh])
            if ok(rr):
                receipt, p_rec = rr["result"], time.perf_counter()
                break
            time.sleep(poll_ms / 1000)
        if receipt is None:
            print(f"No receipt for {txh} within 60 s; stopping.")
            rows.append({"i": i + 1, "tx_hash": txh, "submitted_utc": iso(t_wall), "accepted_s": round(p_acc - p0, 4),
                         "receipt_s": "", "block": "", "status": "NO_RECEIPT_60S"})
            break
        rows.append({"i": i + 1, "tx_hash": txh, "submitted_utc": iso(t_wall), "accepted_s": round(p_acc - p0, 4),
                     "receipt_s": round(p_rec - p0, 4), "block": to_int(receipt.get("blockNumber")),
                     "status": receipt.get("status")})
        print(f"{i + 1:>3}/{n}  receipt in {p_rec - p0:.3f} s  {txh}")
        nonce += 1
        time.sleep(1.0)
    with open(os.path.join(outdir, "latency_samples.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["i", "tx_hash", "submitted_utc", "accepted_s", "receipt_s", "block", "status"])
        w.writeheader()
        w.writerows(rows)
    vals = sorted(r["receipt_s"] for r in rows if isinstance(r["receipt_s"], float))
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "min_s": vals[0], "median_s": round(statistics.median(vals), 4),
            "mean_s": round(statistics.mean(vals), 4), "p90_s": pct(vals, 0.90),
            "p99_s": pct(vals, 0.99), "max_s": vals[-1], "sender": acct.address,
            "note": "nearest-rank percentiles; with n < 100, p99 equals the maximum"}


# ---------------------------------------------------------------- outputs
def write_results(outdir, args, started, ident, cad, comm, lat):
    L = ["# Rayls finality probe results", "",
         f"- Run started: {started}", f"- Run finished: {iso()}",
         f"- Endpoint: {args.rpc}", f"- Chain ID: {ident.get('chain_id_decimal')}",
         f"- Client version: {ident.get('client_version')}",
         f"- Script: {os.path.basename(sys.argv[0])} v{VERSION}, Python {platform.python_version()}", "",
         "## Cadence (read-only)", "", "```", json.dumps(cad, indent=1), "```", "",
         "Header changes are counted when two polls return different rayls_latestHeader responses, so they are a",
         "lower bound set by the poll interval.", "", "## Epoch history (read-only)", "", "```",
         json.dumps(comm, indent=1), "```", "",
         "Blocks per epoch come from parent_state block numbers. Measured values use block timestamps at epoch boundaries;",
         "implied values assume 24-hour epochs, as the Rayls docs state.",
         "Signer positions are decoded from the signed_authorities bitmap. See epoch_history.csv for every sample.", ""]
    if lat is not None:
        L += ["## Submit-to-receipt latency", "", "```", json.dumps(lat, indent=1), "```", ""]
    L += ["## Limits", "",
          "- Times are measured on the client, so they include network round trips and polling delay.",
          "- One machine, one region, one run. Small samples do not describe production reliability.",
          "- A public RPC endpoint may rate-limit, cache or not expose the rayls_ methods.",
          "- Block timestamps are whole seconds, so sub-second claims need client-side timing like the above.", ""]
    with open(os.path.join(outdir, "RESULTS.md"), "w") as f:
        f.write("\n".join(L))


def write_manifest(outdir):
    lines = []
    for name in sorted(os.listdir(outdir)):
        p = os.path.join(outdir, name)
        if name != "SHA256SUMS.txt" and os.path.isfile(p):
            with open(p, "rb") as f:
                lines.append(f"{sha256_bytes(f.read())}  {name}")
    with open(os.path.join(outdir, "SHA256SUMS.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rpc", default=DEFAULT_RPC)
    ap.add_argument("--out", default=None, help="output folder (default: rayls_probe_<UTC time>)")
    ap.add_argument("--cadence-seconds", type=float, default=60)
    ap.add_argument("--cadence-poll-ms", type=float, default=200)
    ap.add_argument("--history-step", type=int, default=10, help="sample every Nth epoch in the history scan (0 = skip)")
    ap.add_argument("--tail", type=int, default=16, help="also sample every one of the newest N epochs")
    ap.add_argument("--no-timestamps", action="store_true", help="skip reading block timestamps at epoch boundaries")
    ap.add_argument("--epochs", default="", help="extra epoch numbers to include, comma-separated")
    ap.add_argument("--send", type=int, default=0, help="number of timed 1-wei self-transfers (0 = read-only)")
    ap.add_argument("--receipt-poll-ms", type=float, default=20)
    ap.add_argument("--yes", action="store_true", help="skip the confirmation before sending")
    args = ap.parse_args()

    started = iso()
    outdir = args.out or "rayls_probe_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(outdir, exist_ok=True)
    rpc = Rpc(args.rpc, os.path.join(outdir, "raw_rpc_log.jsonl"))

    print("1/4 identity ...")
    ident = identity(rpc)
    print("   ", ident)
    print(f"2/4 cadence for {args.cadence_seconds:g} s ...")
    cad = cadence(rpc, args.cadence_seconds, args.cadence_poll_ms, outdir)
    print("   ", cad)
    extra = [int(x) for x in args.epochs.split(",") if x.strip()]
    comm = {"skipped": True}
    if args.history_step > 0:
        print(f"3/4 epoch history scan (every {args.history_step} epochs) ...")
        comm = history(rpc, args.history_step, extra, args.tail, not args.no_timestamps, outdir)
        print("   ", {k: v for k, v in comm.items() if k != "block_time_spans"})
    lat = None
    if args.send > 0:
        print(f"4/4 {args.send} timed self-transfers ...")
        lat = timed_transfers(rpc, args.send, args.receipt_poll_ms, outdir, args.yes)
        print("   ", lat)
    else:
        print("4/4 skipped (read-only run; add --send 20 to time real transactions)")
    rpc.log.close()
    write_results(outdir, args, started, ident, cad, comm, lat)
    write_manifest(outdir)
    print(f"\nDone. Results are in {os.path.abspath(outdir)} (start with RESULTS.md).")


if __name__ == "__main__":
    main()
