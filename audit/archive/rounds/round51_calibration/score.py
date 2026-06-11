#!/usr/bin/env python3
"""Score R51 Phase-0 calibration: auditor findings vs ground-truth key.

Reads:
  ground_truth.json   (the key: planted/clean + wrong_claim + expected_severity)
  audit_results.json  (the workflow return: {results:[{fixture_id,n_findings,findings,...}]})

Produces a per-fixture adjudication table + aggregate FNR/FP/tier metrics with
Wilson 95% CIs. The planted-bug MATCH is heuristic (token overlap between the
auditor's findings and the planted wrong_claim); rows flagged LOW-CONF must be
adjudicated by hand before trusting the aggregates.
"""
import json, os, re, math

HERE = os.path.dirname(os.path.abspath(__file__))
gt = json.load(open(os.path.join(HERE, "ground_truth.json")))
res_path = os.path.join(HERE, "audit_results.json")
if not os.path.exists(res_path):
    raise SystemExit("audit_results.json not found - save the workflow return value there first.")
raw = json.load(open(res_path))
results = {r["fixture_id"]: r for r in (raw.get("results") or raw)}

IDENT = re.compile(r"\b(?:vm_|pm_|v\d+_|p\d+_|s\d+_|c\d+_|i\d+_|f\d+_|q\d+_|im_|fm_|pcm_)\w+\b")
REALIZ = re.compile(r"\b[a-z]+(?:_[a-z]+)*_(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{2}\b")

STOP = set("the a an of to in is are and or for with that this it its as by be at on from "
           "module modules realization realizations default value variable equation".split())
def tokens(s):
    s = s or ""
    t = set(m.lower() for m in IDENT.findall(s))
    t |= set(m.lower() for m in REALIZ.findall(s))
    t |= set(re.findall(r"module\s*\d+|\bm\d+\b|\b\d{2}_[a-z]+\b", s.lower()))
    # general content words + bare numbers (so non-identifier claims like counts match)
    t |= set(w for w in re.findall(r"[a-z]{4,}|\b\d+\b", s.lower()) if w not in STOP)
    return t

def wilson(k, n):
    if n == 0: return (0.0, 0.0, 0.0)
    p = k / n; z = 1.96
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (round(p, 3), round(max(0, c-h), 3), round(min(1, c+h), 3))

rows = []
for f in gt["fixtures"]:
    fid = f["neutral_id"]; r = results.get(fid)
    if not r:
        rows.append({"id": fid, "status": "NO_RESULT", "planted": f["planted"]}); continue
    findings = r.get("findings", []) or []
    if f["planted"]:
        key_tok = tokens(f["wrong_claim"]) | tokens(f["citation"])
        best = None
        for fi in findings:
            ftok = tokens(fi.get("flagged_claim", "")) | tokens(fi.get("code_evidence", "")) | tokens(fi.get("verify_cmd", ""))
            overlap = key_tok & ftok
            if best is None or len(overlap) > best[0]:
                best = (len(overlap), fi, overlap)
        caught = bool(best and best[0] >= 2)  # >=2 shared content tokens = real match
        spurious = [fi for fi in findings if fi is not (best[1] if best else None)]
        rows.append({
            "id": fid, "planted": True, "source": f["source"],
            "exp_sev": f["expected_severity"], "bug_class": f["bug_class"],
            "difficulty": f["difficulty"], "n_findings": len(findings),
            "caught": caught, "match_overlap": (best[0] if best else 0),
            "got_sev": (best[1].get("severity") if caught and best else None),
            "n_spurious": len(spurious),
            "low_conf": (best[0] == 1) if best else False,
            "wrong_claim": f["wrong_claim"],
            "matched_finding": (best[1].get("flagged_claim") if caught and best else None),
            "all_findings": [fi.get("flagged_claim") for fi in findings],
        })
    else:
        rows.append({
            "id": fid, "planted": False, "n_findings": len(findings),
            "fp": len(findings) > 0, "difficulty": f["difficulty"],
            "findings": [fi.get("flagged_claim") for fi in findings],
        })

planted = [r for r in rows if r.get("planted") and r.get("status") != "NO_RESULT"]
clean = [r for r in rows if r.get("planted") is False and r.get("status") != "NO_RESULT"]

def sens(subset):
    n = len(subset); k = sum(1 for r in subset if r["caught"])
    return k, n, wilson(k, n)

print("=" * 78)
print("PER-FIXTURE ADJUDICATION (verify LOW-CONF rows by hand)")
print("=" * 78)
for r in rows:
    if r.get("status") == "NO_RESULT":
        print(f"  {r['id']}: NO RESULT (agent dropped)"); continue
    if r["planted"]:
        flag = " [LOW-CONF MATCH]" if r["low_conf"] else ""
        miss = "" if r["caught"] else "  <<< MISSED"
        sev = f" sev={r['got_sev']}(exp {r['exp_sev']})" if r["caught"] else ""
        sp = f" +{r['n_spurious']}spurious" if r["n_spurious"] else ""
        print(f"  {r['id']} [{r['source']}/{r['exp_sev']}] caught={r['caught']}{sev}{sp}{miss}{flag}")
        if not r["caught"]:
            print(f"      planted: {r['wrong_claim']}")
            print(f"      auditor said: {r['all_findings'] or '(no findings)'}")
    else:
        fp = "  <<< FALSE POSITIVE" if r["fp"] else ""
        print(f"  {r['id']} [clean] findings={r['n_findings']}{fp}")
        if r["fp"]:
            print(f"      flagged: {r['findings']}")

print("\n" + "=" * 78)
print("AGGREGATES (heuristic match; adjudicate LOW-CONF first)")
print("=" * 78)
k, n, ci = sens(planted)
print(f"Overall sensitivity (FNR=1-sens): {k}/{n} = {ci[0]:.0%}  95%CI[{ci[1]:.0%},{ci[2]:.0%}]   FNR={1-ci[0]:.0%}")
for tier in ("Critical", "Major"):
    sub = [r for r in planted if r["exp_sev"] == tier]
    k, n, ci = sens(sub)
    print(f"  {tier:8} sensitivity: {k}/{n} = {ci[0]:.0%}  95%CI[{ci[1]:.0%},{ci[2]:.0%}]")
for src in ("replay", "invented"):
    sub = [r for r in planted if r["source"] == src]
    k, n, ci = sens(sub)
    print(f"  {src:8} sensitivity: {k}/{n} = {ci[0]:.0%}  95%CI[{ci[1]:.0%},{ci[2]:.0%}]")
kfp = sum(1 for r in clean if r["fp"]); nfp = len(clean); cifp = wilson(kfp, nfp)
print(f"False-positive rate (clean flagged): {kfp}/{nfp} = {cifp[0]:.0%}  95%CI[{cifp[1]:.0%},{cifp[2]:.0%}]")
# tier agreement among caught
caught = [r for r in planted if r["caught"] and r["got_sev"]]
agree = sum(1 for r in caught if r["got_sev"] == r["exp_sev"])
print(f"Severity-tier agreement (caught only): {agree}/{len(caught)}")
spur = sum(r["n_spurious"] for r in planted)
print(f"Spurious findings on planted fixtures (extra FPs): {spur}")
print(f"\nLOW-CONF matches to adjudicate by hand: {[r['id'] for r in planted if r.get('low_conf')]}")
