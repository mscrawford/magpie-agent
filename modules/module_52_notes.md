# module_52_notes.md

**📌 User Feedback & Lessons Learned**

This file contains practical insights, warnings, and lessons from users working with Module 52.

Last updated: 2025-10-22

---

## ⚠️ Warnings - Don't Do This

---

## 💡 Lessons Learned

### [L001] Carbon Accumulation Depends on Age Class Structure
**Tags**: carbon, debugging, age_classes | **Added**: 2025-10-22
**Source**: feedback/integrated/20251022_132243_lesson_learned_module_52.md

**Context**: Debugging why carbon sequestration rates seemed too low in an afforestation scenario. New forests were planted, but carbon stocks weren't increasing as expected.

**Key insight**: Module 52 carbon accumulation depends critically on the **age class structure** (Module 28). Young forests (age class 1-5) have much lower carbon density than mature forests. When you plant new forests, they start at age class 1, and it takes decades to accumulate significant carbon.

The carbon density parameter `pm_carbon_density_ac(t,j,ac,"vegc")` increases with age class (ac), following the Chapman-Richards growth curve. This is realistic but can be surprising if you expect immediate carbon gains.

**Why it matters**:

For scenario design - If modeling carbon sequestration from afforestation, you need to:
1. Allow enough time steps for forests to mature (20-50 years)
2. Understand that early carbon gains are small
3. Check the age class distribution (`vm_land_ac`) not just total forest area

For debugging - If carbon stocks aren't changing as expected, ALWAYS check:
- Age class structure (Module 28)
- Carbon density by age class (Module 52 parameters)
- Time since afforestation started

**Where this applies**:
- Afforestation scenarios
- Carbon sequestration analysis
- Debugging unexpected carbon stock behavior
- Understanding why young forests have low BII (Module 44 - also age-dependent)

**Example**:

Situation: Afforestation with carbon price $100/tCO2. After 10 years, carbon stocks increased only 5 tC/ha, but expected 50 tC/ha based on mature forest values.

Solution:
```r
# Check age class distribution
display vm_land_ac;
# Shows: Most new forest is in ac=1-2 (young)

# Check carbon density by age
display pm_carbon_density_ac(t,j,ac,"vegc");
# Shows:
#   ac=1: 2 tC/ha
#   ac=2: 5 tC/ha  ← Where my new forests are
#   ac=10: 50 tC/ha ← What I was expecting
#   ac=20: 80 tC/ha (mature)

# Extend scenario to 50 years
# Now see realistic carbon accumulation curve
```

Result: After extending the time horizon and monitoring age class progression, carbon stocks accumulated realistically. The issue wasn't a bug—it was the expectation that forests would immediately have mature-forest carbon density.

**Related**: Module 28 (age classes), Module 44 (biodiversity - also age-dependent), module_52.md Section 2.2 (Chapman-Richards growth equation)

---

## ✏️ Corrections & Clarifications

---

## 📖 Missing Content - Now Documented

---

## 🧪 Practical Examples

