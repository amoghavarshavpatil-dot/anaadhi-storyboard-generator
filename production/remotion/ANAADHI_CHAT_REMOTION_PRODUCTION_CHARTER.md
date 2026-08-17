# ANAADHI Chat + GitHub + Remotion Production Charter

## Purpose
This charter replaces the previous generation backend without discarding any approved continuity work. GitHub is the canonical production database and codebase; ChatGPT chat generates storyboard stills from GitHub-grounded shot packages; Remotion assembles and renders them.

## Non-negotiable backend rules
- HeyGen: historical evidence only; no new execution.
- OpenAI Work page: not used for generation.
- Paid cloud media APIs: disabled unless explicitly re-authorized.
- Secrets: never committed to GitHub.
- Shot generation: only after the shot package is materialized in GitHub.
- Remotion: canonical scene/reel/final assembly layer.

## Continuation policy
Do not repeat already-completed ENV, continuity, P0/P1 or approved asset work merely because the generation backend changed.

Visual-preproduction inheritance:
- reuse all locked screenplay/ENV/character/location/prop/vehicle/technology records already in the repo;
- unresolved visual controls remain unresolved until a shot package can safely describe them;
- historical HeyGen references may supply identity evidence, but never trigger HeyGen execution.

Audio continuation:
- locked mastered prefix ends at `00:02:14.293333`;
- new theatrical audiobook mix work begins after that timestamp;
- explicit user redrafts may reopen any earlier section.

## Shot-package lifecycle
1. `SPEC_DRAFT` — screenplay beat and known continuity gathered.
2. `SPEC_READY` — all generation-critical fields resolved or deliberately marked as controlled inference.
3. `GENERATED` — still produced in ChatGPT from this exact package.
4. `REVIEW` — awaiting user acceptance/redraft.
5. `APPROVED_SHOT` — accepted still and crop/orientation.
6. `LOCKED_PICTURE` — Remotion timing locked for current revision.
7. `FINAL` — scene/reel/final master accepted.

## Scene-local redrafts
Every shot must be replaceable by ID. Redrafts may alter:
- horizontal orientation / screen direction;
- camera side / axis;
- crop / scale / pan / tilt;
- shot duration and order;
- location or state continuity when screenplay changes;
- dialogue, BGM and SFX cue windows;
- generated image asset;
without forcing unrelated scenes to rebuild.

## Master picture
- raster: 3840x1600
- aspect: 2.40:1
- fps: 30
- no baked letterbox
- shot still motion: subtle cinematic pan/zoom/parallax only where specified; do not invent motion that contradicts the frame.

## Audio architecture
Per scene, keep separate stems when available:
- dialogue
- BGM
- ambience
- Foley/SFX
- impacts/transitions
- final scene mix

Dialogue preservation rule:
- preserve creator performance and timing;
- no automatic voice replacement;
- cinematic processing may improve clarity, body, space and impact while preserving words, pauses and acting.

## Remotion assembly contract
- one composition for feature master;
- optional reel compositions for Scenes 001-020, 021-040, 041-060, 061-080, 081-100;
- one scene sequence per scene;
- one shot layer per approved shot;
- shot assets resolved through `staticFile()` from the Remotion public tree;
- audio stems are independently replaceable;
- scene timing derives from manifest data;
- visual layers use editable Remotion/Studio properties where practical.

## GitHub file layout
- `production/remotion/CONTINUATION_CURSOR.yaml`
- `production/remotion/MASTER_RENDER_SPEC.yaml`
- `production/remotion/SHOT_SPEC_SCHEMA.yaml`
- `production/remotion/shot_specs/SC###/SC###_SHOT_PACKAGE.json`
- `production/remotion/src/` Remotion source
- `production/remotion/public/shots/SC###/` generated stills when materialized outside the chat UI and committed by an available binary-safe path
- `production/remotion/public/audio/` scene/reel stems when materialized

## Binary-asset handling
The GitHub connector may not always expose a binary-upload path from chat-generated image objects. The production truth therefore separates:
1. canonical shot specification in GitHub;
2. generated visual in chat;
3. eventual binary import into the Remotion public tree through an available binary-safe path.
Never fake an image path or hash before the binary actually exists.

## Cost policy
Do not buy a new editor or generation service merely to satisfy the pipeline. Remotion plus the user's existing editing/audio tools are sufficient for the current architecture. Add one paid finishing tool only if a concrete missing capability is proven later.
