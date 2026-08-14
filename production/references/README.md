# ANAADHI — P1 Visual Reference Locking

This folder is the **P1 look / identity / location / prop reference layer** for the 34 whole-movie production batches defined in `production/batches/ANAADHI_BATCH_FOUNDATION.py`.

## Purpose

P0 already defines the screenplay-derived batch structure. P1 does **not** change scene action, dialogue, blocking or edit timing. It only tells later generation code which approved reference assets must control:

- character identity
- exact age state
- height/body proportion
- hair and facial-hair state
- costume state
- injury/scar state
- location/set identity
- recurring architecture/material language
- hero props and recurring props
- vehicles / devices / medical equipment where continuity matters
- scene-specific override assets

## Absolute rule

**Never invent an approved visual reference.**

If an approved asset has not yet been uploaded or registered, its status stays `MISSING_APPROVED_ASSET`. Generation for that identity/location/prop family must not be treated as visually locked.

Uploaded/approved visual assets override model defaults.

## Reference types

Each asset receives one stable reference ID:

- `CHR-*` — character identity
- `AGE-*` — age/body substate
- `HR-*` — hair / facial-hair substate
- `CST-*` — costume substate
- `INJ-*` — injury / scar / recovery substate
- `LOC-*` — location / set
- `PRP-*` — prop
- `VEH-*` — vehicle / mobile capsule
- `TEC-*` — device / embedded technology
- `ENV-*` — environment / weather / condition reference
- `GF-*` — parallel-Earth grammar reference

## Lock order

For each batch, lock in this order:

1. location identity
2. principal character identity
3. age/body substate
4. hair/facial-hair substate
5. costume substate
6. injury/scar substate
7. hero/recurring props
8. supporting characters
9. environmental condition
10. parallel-Earth variant grammar if present

## Anaadhi continuity rule

Adult Anaadhi is always **193 cm / 6'4** unless an explicit screenplay shot represents him at a younger age or a parallel variant with a different stated age.

Child/teen Anaadhi must never be produced by merely shrinking the Scene-100 adult body. Every childhood/adolescent phase is its own age/body reference state.

P1 must keep distinct at minimum:

- newborn
- age 5
- age 7
- age 8
- age 9
- age 10
- age 11
- age 12 institutional
- age 12 forest-survival progression
- ages 13, 14, 15, 16
- age 17
- age 18
- age 19
- age 20
- age 21
- age 22
- age 23
- age 24
- age 25
- age 26
- age 27 forest/capture
- age 27 post-surgery recovery
- age 27 Scene-100 healed-scar final state

## Costume / hair rule

Never allow one batch to silently inherit costume or hair from a later age.

Examples:

- age-12 institutional Anaadhi: close institutional haircut and institutional clothing
- age-12 forest escape: same base identity progressively soaked/torn/muddy and then repaired
- age-16: hair reaches neck
- age-18: long loosely tied hair + faint moustache
- age-19: shoulder-length hair tied with fibre + thin uneven moustache/light beard + rough-spun tunic/repaired trousers/weathered sandals
- age-27 capture: screenplay-specific capture state; do not substitute Scene-100 final hair/recovery look
- Scene 100: healed long scars + final approved Scene-100 identity/hair/costume references

## Dialogue is NOT part of P1

Do not place final Kannada dialogue or AI dialogue into this reference layer.

Later phases:

- P2: action, blocking, shots, durations
- P3: creator-recorded Kannada dialogue + lip-sync windows
- P4: creator-recorded Kannada inner voice / V.O. / monologues
- P5: BGM / ambience / Foley / SFX, second by second
- P6: mix and theatrical mastering
- P7: final assembly

## Folder convention for future approved files

Suggested structure:

```text
references/
  characters/
    anaadhi/
    aarathi/
    parvaran/
    anarvaa/
    manire/
    semmaa/
    marsyaa/
    asana/
    janne/
    ...
  locations/
    bhaigaara_raised_cabin/
    paraane/
    parlipatna_hospital/
    adraka_university/
    independent_surgery_centre/
    border_checkpoint/
    tribunal/
    judicial_medical_centre/
    ...
  props/
  vehicles/
  technology/
  environments/
```

The registry in `REFERENCE_REGISTRY.yaml` stores the authoritative asset path and approval state.

## Gate to P2

A batch becomes `P1_LOCKED` only when every item marked `required_for_generation: true` in `BATCH_REFERENCE_REQUIREMENTS.yaml` points to an approved asset in `REFERENCE_REGISTRY.yaml`.

Until then, the batch remains `P1_WAITING_FOR_ASSETS`.
