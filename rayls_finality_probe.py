#!/usr/bin/env python3
"""Rayls finality probe: first-hand, timestamped evidence from a Rayls (Axyl) RPC endpoint.

Steps 1-3 are read-only and need only the Python standard library:
  1. identity   chain id, client version, latest EVM block
  2. cadence    how fast EVM blocks and consensus headers (rayls_latestHeader) advance
  3. committee  committee snapshots for chosen epochs (rayls_epochRecord)
Step 4 is optional and sends real transactions:
  4. latency    N timed 1-wei self-transfers, submit -> receipt.
                Needs: pip install eth-account, a THROWAWAY private key in the env var
                RAYLS_TEST_KEY, and a small balance of the gas token (USDr on mainnet).

Output: a folder with raw call logs, CSVs, RESULTS.md and SHA256SUMS.txt.
The folder never contains your private key. Read it before you publish it.
Example: python3 rayls_finality_probe.py --epochs 1,50,100,150 --send 20
"""
import argparse, csv, hashlib, json, math, os, platform, re, statistics, sys, time, urllib.request
from datetime import datetime, timezone

VERSION = "1.0"
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
    rows, start = [], time.perf_counter()
    next_tick = start
    while time.perf_counter() - start < seconds:
        b, _ = rpc.call("eth_blockNumber")
        h, _ = rpc.call("rayls_latestHeader")
        t = time.perf_counter() - start
        hdr = h["result"] if ok(h) else None
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
    out = {"samples": len(rows), "poll_ms_requested": poll_ms}
    dt = rows[-1]["t_s"] - rows[0]["t_s"] if len(rows) > 1 else 0
    out["duration_s"] = round(dt, 3)
    blks = [r["evm_block"] for r in rows if r["evm_block"] is not None]
    if len(blks) > 1 and dt:
        out.update(evm_first=blks[0], evm_last=blks[-1], evm_blocks_advanced=blks[-1] - blks[0],
                   evm_blocks_per_s=round((blks[-1] - blks[0]) / dt, 3))
    hdrs = [(r["t_s"], r["header_sha256"]) for r in rows if r["header_sha256"]]
    if len(hdrs) > 1 and dt:
        changes = [t for (t, h), (_, hp) in zip(hdrs[1:], hdrs[:-1]) if h != hp]
        gaps = [b - a for a, b in zip(changes, changes[1:])]
        out.update(header_changes_observed=len(changes), header_changes_per_s=round(len(changes) / dt, 3),
                   median_gap_between_observed_changes_s=round(statistics.median(gaps), 3) if gaps else None)
        if changes and "evm_blocks_advanced" in out:
            out["evm_blocks_per_observed_header_change"] = round(out["evm_blocks_advanced"] / len(changes), 2)
        nums = [r["consensus_number"] for r in rows if isinstance(r["consensus_number"], int)]
        if len(nums) > 1:
            out["consensus_number_advanced"] = nums[-1] - nums[0]
    else:
        out["rayls_latestHeader"] = "no usable responses (method not exposed on this endpoint?)"
    return out


# ---------------------------------------------------------------- step 3
CANDIDATE = re.compile(r"(committee|authorit|validator|member|signer)", re.I)


def walk(o, path, found, shape):
    if isinstance(o, dict):
        shape.append([path, "object", len(o)])
        for k, v in o.items():
            p = f"{path}.{k}"
            if CANDIDATE.search(str(k)) and isinstance(v, (list, dict)):
                found.append([p, len(v)])
            walk(v, p, found, shape)
    elif isinstance(o, list):
        shape.append([path, "array", len(o)])
        for i, v in enumerate(o[:2]):
            walk(v, f"{path}[{i}]", found, shape)


def committees(rpc, epochs, outdir):
    out = {}
    for e in epochs:
        r, _ = rpc.call("rayls_epochRecord", [e])
        with open(os.path.join(outdir, f"epoch_record_{e}.json"), "w") as f:
            json.dump(r, f, indent=1)
        if ok(r):
            found, shape = [], []
            walk(r["result"], "$", found, shape)
            out[str(e)] = {"candidate_committee_sizes": found, "shape": shape[:25]}
        else:
            out[str(e)] = {"error": r.get("error") or r}
    return out


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
         f"- Script: rayls_finality_probe.py v{VERSION}, Python {platform.python_version()}", "",
         "## Cadence (read-only)", "", "```", json.dumps(cad, indent=1), "```", "",
         "Header changes are counted when two polls return different rayls_latestHeader responses, so they are a",
         "lower bound set by the poll interval. If the median gap is close to the poll interval, rerun with a",
         "smaller --cadence-poll-ms.", "", "## Committee snapshots (read-only)", "", "```",
         json.dumps(comm, indent=1), "```", "",
         "Candidate sizes are lengths of fields whose names look like committee or validator lists. Open the",
         "epoch_record_*.json files to confirm which field is the committee.", ""]
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
    ap.add_argument("--cadence-seconds", type=float, default=30)
    ap.add_argument("--cadence-poll-ms", type=float, default=200)
    ap.add_argument("--epochs", default="1,50,100,150", help="comma-separated epoch numbers, or empty to skip")
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
    epochs = [int(x) for x in args.epochs.split(",") if x.strip()]
    print(f"3/4 committee snapshots for epochs {epochs} ...")
    comm = committees(rpc, epochs, outdir)
    for e, v in comm.items():
        print("    epoch", e, v.get("candidate_committee_sizes", v.get("error")))
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
