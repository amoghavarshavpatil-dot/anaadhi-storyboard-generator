# ANAADHI Storyboard Generator

GitHub-first, revision-safe production pipeline for the ANAADHI feature storyboard audiobook.

## Current master path

`approved screenplay + continuity records -> GitHub shot package -> ChatGPT chat-page storyboard still -> Remotion scene/reel assembly -> theatrical dialogue/BGM/SFX mix -> 4K scope master`

## Backend policy

- No new HeyGen generation, avatar, look, consent, render or lip-sync work.
- No OpenAI Work-page generation.
- No paid media-generation API calls unless explicitly re-authorized later.
- Existing historical HeyGen assets/records stay in the repository as continuity evidence.
- Never commit API keys, tokens, cookies, passwords or other secrets.
- GitHub stores deterministic shot specifications and render code; the chat page generates storyboard stills from those specifications.

## Master delivery target

- 3840x1600
- 2.40:1
- 30 fps
- no baked-in letterbox bars
- feature-length scene/reel assembly
- independently replaceable shots and audio stems

## Revision model

Every scene and shot has a revision ID. A screenplay redraft may change framing, screen direction, scene orientation, shot order, duration, audio timing, continuity state or generated still without rebuilding unrelated scenes.

## Audio continuation

The already-mastered opening through `00:02:14.293333` is treated as a locked prefix. New storyboard-audiobook audio work resumes after that point unless an explicit revision reopens it.

## Remotion

The canonical Remotion project lives under `production/remotion/`. Shot stills are referenced from its `public/` asset tree and scene/shot timing is data-driven from GitHub manifests.

The Remotion structure is intentionally interactive and scene-local so revisions can be made in Studio and written back to code without rebuilding the complete film.

## Production order from the existing project state

1. Reuse all already-approved screenplay, ENV, continuity, character, location, prop, vehicle and technology records. Do not restart pre-production from Scene 001.
2. Materialize deterministic shot packages for Scenes 001–100 from those existing controls.
3. Generate storyboard stills in ChatGPT only after the relevant shot package is ready.
4. Approve or redraft each shot independently.
5. Assemble shots into scene compositions in Remotion.
6. Continue theatrical audiobook audio after `00:02:14.293333`, preserving the mastered opening.
7. Assemble five reels, then the feature master.

See `production/remotion/ANAADHI_CHAT_REMOTION_PRODUCTION_CHARTER.md` and `production/remotion/SHOT_SPEC_SCHEMA.yaml`.
