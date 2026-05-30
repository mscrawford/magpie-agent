# Round 36 Adversarial Verification — module_42.md (CONSUMER/POPULATOR/DEPENDENCY-SET findings)

Verifier role: adversarial, default-skeptic. Ground truth: `/tmp/magpie_develop_ro` (develop worktree).

## Scope triage

The verifier mandate covers only CONSUMER / POPULATOR / DEPENDENCY-SET findings —
findings that assert WHICH MODULES consume / populate / depend-on an interface
variable or parameter (phantom member, omitted member, wrong producer/consumer set,
direct-vs-transitive).

**None of the four 42-B* findings is a consumer-set claim.** They are:
- 42-B1: hardcoded count of a *set's members* (195 vs 249 countries) — Pattern 6.
- 42-B2: content of a *set definition* (which sectors live in module sets.gms vs core) — Pattern 12.
- 42-B3: wrong *parameter name* for pumping costs — manual.
- 42-B4: content of a *set definition* (endogenous/exogenous subsets) — Pattern 12.

`class_is_consumer_set = false` for all four → verdict NOT_CONSUMER_SET; they pass to the
fixer unchanged. Per method, no consumer-set re-derivation is required for these.

I nonetheless ran the code probes (cheap, and useful as a sanity backstop). All four
auditor findings reproduce cleanly against develop — recorded below for the fixer's benefit,
but the formal verdict remains NOT_CONSUMER_SET (these are out of this verifier's correction scope).

---

## 42-B1 — "195 countries" should be 249 (NOT_CONSUMER_SET)

Probe:
```
$ sed -n '52,76p' modules/42_water_demand/all_sectors_aug13/input.gms | grep -oE '\b[A-Z]{3}\b' | grep -v 'EFP' | sort -u | wc -l
249
$ rg -n '^\s*iso ' core/sets.gms        # iso set header
37:  iso list of iso countries          # body spans lines 38-55
```
EFP_countries(iso) lists 249 unique ISO codes (the lone "EFP" token in the declaration
inflates a naive count to 250; excluding it = 249). The core `iso` set (core/sets.gms:38-55)
is the same 249. Comment at input.gms:50 = "all iso countries selected".

Doc lines carrying "195": 313, 652, 859, 904 (grep confirmed all four refer to EFP coverage).
Auditor evidence reproduces; fix (195→249) is correct. But this is a member-count claim about
a SET, not a module-consumer claim → NOT_CONSUMER_SET.

---

## 42-B2 — sets.gms:9-10 "5 sectors incl. agriculture" (NOT_CONSUMER_SET)

Probe:
```
$ rg -n 'wat_dem' core/sets.gms
247:   wat_dem Water demand sectors / agriculture, domestic, manufacturing, electricity, ecosystem /
$ rg -n 'watdem_exo|agriculture' modules/42_water_demand/all_sectors_aug13/sets.gms
9:   watdem_exo(wat_dem) Exogenous water demand   # / domestic, manufacturing, electricity, ecosystem /
# (no 'agriculture' match in module sets.gms — positive control: watdem_exo DID match, so search works)
```
Module sets.gms:9-10 defines `watdem_exo` = 4 exogenous sectors (domestic, manufacturing,
electricity, ecosystem); NO agriculture. Full 5-sector `wat_dem` (incl. agriculture) is in
core/sets.gms:247. Auditor evidence reproduces. This is set-content, not module-consumer →
NOT_CONSUMER_SET.

---

## 42-B3 — s42_watdem_nonagr_* is not the pumping-cost param (NOT_CONSUMER_SET)

Probe:
```
$ rg -n 's42_watdem_nonagr' modules/42_water_demand/
input.gms:9:  s42_watdem_nonagr_scenario  ... / 2 /
presolve.gms:44,47,50:  if/Elseif (s42_watdem_nonagr_scenario = ...)
# => s42_watdem_nonagr_* resolves ONLY to ..._scenario (already listed on doc line 1018)
$ rg -n 's42_pumping|s42_multiplier' modules/42_water_demand/all_sectors_aug13/input.gms
39:s42_pumping ...; 40:s42_multiplier_startyear ...; 41:s42_multiplier ...   # positive control: present
```
Auditor evidence reproduces; pumping-cost params are s42_pumping / s42_multiplier /
s42_multiplier_startyear (input.gms:39-41). Wrong-parameter-name finding, not a module-consumer
claim → NOT_CONSUMER_SET.

---

## 42-B4 — sets.gms:9-13 endogenous/exogenous (NOT_CONSUMER_SET)

Probe (same files as B2):
```
$ sed -n '8,14p' modules/42_water_demand/all_sectors_aug13/sets.gms
9-10:  watdem_exo(wat_dem) / domestic, manufacturing, electricity, ecosystem /   (4, exogenous)
12-13: watdem_ineldo(wat_dem) / domestic, manufacturing, electricity /            (3, humanly-induced exo)
```
No "endogenous" set in module sets.gms; agriculture (the endogenous member) lives only in
core/sets.gms:247 `wat_dem`. Auditor evidence reproduces. Set-content citation, not a
module-consumer claim → NOT_CONSUMER_SET.

---

## Summary

| Bug | consumer_set? | Verdict | Code reproduces? |
|-----|---------------|---------|------------------|
| 42-B1 | no | NOT_CONSUMER_SET | yes (249 confirmed) |
| 42-B2 | no | NOT_CONSUMER_SET | yes (watdem_exo=4, no agriculture) |
| 42-B3 | no | NOT_CONSUMER_SET | yes (pumping = s42_pumping/_multiplier[_startyear]) |
| 42-B4 | no | NOT_CONSUMER_SET | yes (watdem_exo + watdem_ineldo only) |

All four are out of consumer-set scope and pass to the fixer unchanged. As a backstop I
confirmed each reproduces against develop, so the fixer should not expect a hidden defect in them.
