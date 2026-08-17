# ANAADHI — AI Movie Production Rules

## Master objective
Build a feature-length approximately 2-hour ANAADHI storyboard-audiobook / cinematic storyboard film from the evolving approved screenplay, existing continuity records, creator-recorded dialogue, BGM and SFX.

The screenplay is living material. No generated scene is permanently canonical merely because it was generated earlier.

## 2026-08-17 production-backend lock
The master production path is now:

`approved screenplay + GitHub continuity -> GitHub shot package -> ChatGPT chat-page storyboard still generation -> Remotion scene/reel assembly -> theatrical audio mix -> final master`

Hard rules:
- Do not use HeyGen for any new generation, avatar, look, consent, render or lip-sync work.
- Do not use OpenAI Work-page media generation for this project.
- Existing HeyGen/Work-page records remain historical evidence only and must not be deleted merely because the backend changed.
- Do not call paid media-generation APIs unless the user explicitly changes this rule later.
- GitHub is the canonical source for shot specifications, continuity bindings, scene manifests, revision history and Remotion code.
- Never commit raw API keys, access tokens, passwords, cookies or other secrets to GitHub.
- Storyboard shots are generated in the ChatGPT chat from GitHub-grounded shot packages, not from memory-only prompts.
- Remotion is the canonical picture-assembly and render-code layer.

## Authority order
1. Latest explicit user-approved scene override
2. Latest approved scene manifest / shot package in GitHub
3. Latest approved character/location/prop/technology reference evidence
4. Latest approved screenplay version
5. Older generated material only as continuity reference

## Dialogue / voice rule
- Do not generate replacement final dialogue unless the user explicitly changes this rule.
- Preserve the creator's recorded dialogue, pauses, breaths, Kannada/Kanglish pronunciation, timing and acting identity.
- Dialogue regions remain independently replaceable from picture.
- Visible-mouth shots may be revised around recorded audio; no HeyGen lip-sync backend is used.
- Non-speaking coverage may use reactions, profiles, backs, inserts, atmosphere, montage and cutaways.

## Audio rule
The pipeline may edit and mix:
- creator-recorded dialogue
- BGM
- ambience
- Foley
- cinematic SFX
- transitions / impacts / risers where dramatically justified

Opening mastered continuity already completed through 00:02:14.293333 is a locked prefix. New audiobook-audio work resumes after that point unless the user explicitly requests a revision inside the locked prefix.

Recommended per-scene audio deliverables:
1. `dialogue.wav`
2. `bgm_sfx.wav`
3. `scene_mix.wav`
4. `scene_mix_preview.wav`
5. timing / automation metadata in the scene package

## Picture rule
- Master scope target: 2.40:1.
- Master raster: 3840x1600.
- Master frame rate: 30 fps unless a later explicit delivery requirement overrides it.
- No baked-in letterbox bars.
- Preserve character height, age, body, hair, costume, injury, prop, vehicle, technology and location states scene by scene.
- Approved references and GitHub continuity override model defaults.
- Every shot must be independently replaceable without rebuilding the whole movie.

## Production hierarchy
Never generate a two-hour monolithic file directly.

`movie -> reel -> scene -> shot package -> generated still -> approved shot -> scene assembly -> reel assembly -> final movie`

Reels:
- Reel 01: Scenes 001–020
- Reel 02: Scenes 021–040
- Reel 03: Scenes 041–060
- Reel 04: Scenes 061–080
- Reel 05: Scenes 081–100

## Revision / redraft rule
Every scene and shot package must carry a revision ID. A revised screenplay scene may change shot order, camera orientation, screen direction, duration, audio timing or asset state without forcing unrelated scenes to regenerate.

Supported status flow:
- `SPEC_DRAFT`
- `SPEC_READY`
- `GENERATED`
- `REVIEW`
- `APPROVED_SHOT`
- `LOCKED_PICTURE`
- `LOCKED_AUDIO_BED`
- `FINAL`

`LOCKED_PICTURE` is revisable by later explicit user approval.

## GitHub shot-package rule
Every generated shot must be grounded in a GitHub shot package containing, at minimum:
- scene and shot IDs
- screenplay source beat
- asset bindings
- character substates
- environment/location state
- prop/vehicle/technology state
- camera/lens/framing/orientation/screen-direction plan
- lighting/weather/time condition
- continuity exclusions
- image-generation prompt contract
- Remotion timing / motion parameters
- audio cue windows
- revision metadata

## Cost rule
Use zero-additional-cost or already-available project capabilities wherever practical. Do not silently call paid APIs, cloud-credit nodes or subscription generation services.

## First production principle
Story and continuity first, shot specification second, generation third, assembly fourth. No large-scale shot generation until the corresponding GitHub shot packages are complete enough to reproduce and revise the frame deterministically.
