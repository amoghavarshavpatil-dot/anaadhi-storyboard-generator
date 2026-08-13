# ANAADHI — AI Movie Production Rules

## Master objective
Build a feature-length **approximately 2-hour AI movie** from the evolving ANAADHI screenplay and uploaded visual/audio references.

The screenplay is **living material**. It may change during production. No generated scene is permanently canonical merely because it was generated earlier.

## Authority order
1. Latest approved scene override in `scenes/`
2. Latest approved character/location/prop reference assets
3. Latest approved screenplay version
4. Older generated material only as continuity reference

A newer explicit scene override always beats an older screenplay paragraph or generated shot.

## Dialogue / voice rule
- **Do not generate final spoken dialogue.**
- No AI TTS is part of the master soundtrack unless explicitly approved later.
- Dialogue regions must remain available for the creator's recorded performances.
- Where visible mouth movement is required, the pipeline must support later lip-sync against uploaded recorded voice clips.
- Where lip-sync is not required, use reaction shots, profiles, backs, inserts, atmosphere, montage, cutaways or non-speaking performance as appropriate.

## Audio rule
The automated movie pipeline may create and mix:
- BGM
- ambience
- Foley
- cinematic SFX
- transitions / impacts / risers where dramatically justified

It must **not bake generated dialogue into the final master**.

Recommended deliverables per scene:
1. `picture_only.mp4`
2. `bgm_sfx.wav`
3. `dialogue_placeholder.wav` (silence / guide timing only)
4. `preview_with_temp_mix.mp4`
5. shot manifest and continuity metadata

## Picture rule
- Scope target: **2.39:1**
- No baked-in letterbox bars.
- Keep a consistent master raster across the project.
- Maintain character height, age, body, hair, costume, injuries and prop states scene by scene.
- Uploaded identity/location references override model defaults.
- Shots must be generated independently enough that a single failed shot can be replaced without rebuilding the entire film.

## Production rule
Never generate a two-hour monolithic file directly.

Generate in this hierarchy:
`movie -> scene -> shot -> approved shot -> scene assembly -> reel assembly -> final movie`

Suggested reels:
- Reel 01: Scenes 001–020
- Reel 02: Scenes 021–040
- Reel 03: Scenes 041–060
- Reel 04: Scenes 061–080
- Reel 05: Scenes 081–100

## Revision rule
Every scene has an editable `scene.yaml` file. When screenplay material changes, edit only the affected scene manifest and regenerate only affected shots.

Statuses:
- `DRAFT`
- `GENERATING`
- `REVIEW`
- `LOCKED_PICTURE`
- `LOCKED_AUDIO_BED`
- `FINAL`

`LOCKED_PICTURE` does not prevent a later explicit screenplay revision; it simply records the current approved state.

## Cost rule
Use local/open-source generation whenever practical. Do not silently call paid APIs or cloud-credit nodes.

## First production principle
**Story and continuity first, generation second.** Large batch generation is allowed only after the look/identity grammar for the relevant character/location family has been validated on representative test shots.
