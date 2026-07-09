# Module 10 (Land) — Notes

**Backfilled 2026-05-25** from `audit/validation_rounds.json` R15 + R23 findings (R6 Cluster C2).

---

## ⚠️ Warnings & Common Mistakes

### Net vs gross / between-type land transitions

`module_10.md` historically conflated **net** land transitions with **gross / between-type** transitions in 8 locations. The two are not the same:
- **Net transitions**: difference in stock between time steps (cropland_t - cropland_t-1).
- **Gross / between-type transitions**: actual area moving FROM one land class TO another, including both directions. Captured via `vm_lu_transitions(j, land_from, land_to)` in `landmatrix_dec18` (the default realization).

When describing how land changes, distinguish which one you mean. The default `landmatrix_dec18` realization tracks gross transitions; the alternative `feb15` realization uses a simpler net-stock formulation.

### Spatial resolution is configurable

`module_10.md` historically said "200 cells" in 2 locations. This is wrong as a hardcoded claim. MAgPIE's spatial resolution is configurable via `cfg$magpie_folder` and the input data; common runs use 200 cells but other resolutions exist. Don't cite a specific cell count as if it's a hard property of the module.

### Input source/vintage labels are preproc-owned claims (verify, don't trust the filename)

Source/vintage labels in `module_10.md`'s Data Sources section are input-provenance CLAIMS, owned by the preprocessing side. Verify them from the file's own madrat comment (`getComment(read.magpie("modules/10_land/input/avl_land_t.cs3"))` -> the `origin:` line), not the filename. As of 2026-07-09 the main land-init `avl_land_t.cs3` -> `f10_land` is **LUH3** (origin `calcOutput("LanduseInitialisation", ... mrlandcore 1.6.5)`; cf. `core_docs/Data_Flow.md:40`, audit P5-B1), not the "LUH2" older text asserted. The **side layers** (`luh2_side_layers.cs3`, `module_10.md:239`) are genuinely LUH2 (BendingTheCurve / Leclère) - so not every "LUH" here is wrong. A `luh2_*` filename is a legacy identifier, not a source (MAgPIE is mid LUH2->LUH3 migration). Only assert a vintage you have verified; route vintage questions to `PREPROC_AGENT.md`. (Source: 2026-07-09 session.)

---

## 💡 Lessons Learned

- 2026-05-25: When discussing Module 10 land transitions, always state which **realization** is active (default is `landmatrix_dec18`). Net stock differences != gross transitions matrix. (Source: R15 findings.)
- 2026-05-25: Module 10 is in `modification_safety_guide.md` top-4 (alongside M11/M17/M56) — extra care required when modifying. (Source: R23 G1 audit confirmed centrality.)

---

## 🧪 Real-World Examples

*Backfilled examples deferred — add when concrete user scenarios surface.*

---

## See also

- `module_10.md` — primary documentation
- `cross_module/modification_safety_guide.md` — M10 risk tier (HIGH centrality)
- `cross_module/land_balance_conservation.md` — `q10_land_area` conservation constraint
