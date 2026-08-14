# ANAADHI — Whole-Movie Batch Production Architecture

This directory is the foundation layer for building the full ANAADHI feature as manageable production batches instead of one monolithic generation.

## Current phase: P0 — Batch Foundation

The master batch file divides Scenes 001–100 exactly once into 34 production batches organised by reusable interior/exterior locations, character life-stage continuity, Anaadhi's exact age/body/hair/costume/injury state, and location-specific props.

This phase deliberately does **not** define final action blocking, dialogue timing, lip sync, Kannada voice files, inner voice/VO placement, BGM, SFX, mix or mastering yet.

## Why location + continuity batches

A simple 20-scene reel split is useful for editing but not sufficient for AI generation. The generator must know which exact version of every location and returning character belongs to a shot. The batches are designed to prevent age drift, hairstyle drift, costume drift, injury drift, architecture drift and generic replacement props.

## Absolute Anaadhi identity rule

- Adult Anaadhi height: **193 cm / 6'4**. Never shorten him to fit composition.
- Adult facial identity follows the latest approved uploaded identity references.
- Age, hair, body condition, injuries and costume roll backward/forward according to each batch.
- Scene 100 uses the final post-recovery state: healed long scars, lean defined body, dense voluminous medium-long hair with natural lift/side taper, medium-full beard and disciplined moustache.
- Child/teen Anaadhi must never be rendered by simply shrinking the Scene-100 adult body.

## Character-age rule

Where the screenplay gives an exact Anaadhi age, use that exact age. Where another character's numeric age is not stated, use the screenplay's life-stage/time-period description instead of inventing a number.

Parallel-Earth variants inherit the same base identity and location anchor unless the screenplay explicitly changes age, role, injury, costume or world-state.

## Production phase order

1. **P0 Batch Foundation — CURRENT** — locations, characters, age/body/hair/costume/injury and props.
2. **P1 Look & Identity Lock** — approved location masters, character references, costume/hair references, prop masters.
3. **P2 Scene Action & Shot Timeline** — action, blocking, camera, shot IDs, duration, transitions and Parallel-Earth transformations.
4. **P3 Kannada Dialogue + Lip Sync** — creator-recorded Kannada clips mapped to speaker, scene, shot and visible-mouth windows. No automatic replacement voice is assumed.
5. **P4 Inner Voice / V.O. / Monologue** — creator-recorded non-lip-sync performances mapped separately.
6. **P5 BGM / Ambience / Foley / SFX** — second-by-second sound-design map after picture and voice timing are stable.
7. **P6 Mix & Master** — dialogue/BGM/SFX automation, stems and theatrical mastering.
8. **P7 Final Assembly** — approved shots -> scenes -> reels -> approximately two-hour feature master.

## Later scene-file contract

A later scene manifest can add fields such as:

```yaml
scene_id: SC091
batch_id: B30
picture:
  shots: []
action:
  blocking: []
voice:
  dialogue:
    - speaker: ANAADHI
      language: kn-IN
      uploaded_file: PENDING
      lip_sync: true
  inner_voice: []
  voice_over: []
audio:
  bgm: []
  ambience: []
  foley: []
  sfx: []
mix:
  automation: []
status: DRAFT
```

Those later fields are intentionally not populated in P0.

## Revision rule

The screenplay is living material. A later approved scene override changes only affected batch/scene instructions. It must not force a rebuild of the whole movie.

## Safety / story fidelity rule

Where the screenplay deliberately keeps a fatal act off-screen, symbolic or non-instructional, the visual pipeline must preserve that framing and must not invent explicit mechanics.

## Files

- `ANAADHI_BATCH_FOUNDATION.py` — machine-readable 34-batch foundation and future-phase contract.
- `README.md` — this explanation.

Do not ask the creator to manually repair Python on Android. GitHub is the readable source of truth; Kaggle/notebooks should consume these manifests.