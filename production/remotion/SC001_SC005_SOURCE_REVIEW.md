# ANAADHI SC001-SC005 Remotion Source Review

This composition assembles the complete SC001-SC005 timing run from the canonical GitHub shot packages without SuperCool, HeyGen execution, paid image generation, generated dialogue, or replacement voice.

The original review encode is retracted as a storyboard deliverable because it used procedural source-review visuals rather than materialized storyboard stills. Approved stills now enter the sequential `public/shots/SC###/SC###_SH###/` tree one shot at a time. A corrected storyboard video must not be claimed until all required shot images are approved and resolved from that tree.

## What is locked in this build

- 106-shot order and exact package durations
- 3840x1600, 2.40:1, 30 fps composition geometry
- single SC002 door breach and persistent breach/wet-debris state
- B01 character identities and Anaadhi's 193 cm capture-state continuity
- SC001-SC005 physical/represented boundaries and zero-residue resets
- SC005 source-chronology lab bridge with the final editorial next segment still SC099B

## What remains review-only

The repository does not yet contain approved per-shot stills for these scenes or the creator dialogue/master-audio files. The current cut therefore uses the locked B01 identity sources, existing Bhaigaara ecology evidence, and deterministic Remotion staging as a source-review animatic. It does not mark any shot `APPROVED_SHOT`, `LOCKED_PICTURE`, or `FINAL`.

## Run

```bash
npm install
npm run assets:sync
npm run studio
```

Render the 1920x800 review encode:

```bash
npm run render:sc001-005-preview
```

Render the 3840x1600 scope encode:

```bash
npm run render:sc001-005
```
