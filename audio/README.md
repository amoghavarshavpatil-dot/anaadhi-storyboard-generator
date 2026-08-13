# Audio workflow

ANAADHI uses a **picture + BGM/SFX first** production model.

## Final spoken dialogue
Final dialogue comes from creator-uploaded recorded voice clips. The automated pipeline does not create replacement dialogue.

## Lip-sync clips
When a shot requires visible lip movement, place the final recorded line in:

`audio/dialogue/SC###/`

Recommended naming:

`SC003_V005_AARATHI_001.wav`

The corresponding shot manifest should set:

- `lip_sync_required: true`
- `dialogue_clip: audio/dialogue/SC003/SC003_V005_AARATHI_001.wav`

Shots that do not need visible lip movement should leave `lip_sync_required: false`.

## Automated audio beds
For every scene, the pipeline may build:

- score / BGM
- environment ambience
- Foley
- designed SFX
- dramatic impacts and transitions

These should be exported separately from dialogue so later voice replacement never damages the music/SFX master.

Recommended output:

`output/SC###/audio/SC###_BGM_SFX_MASTER.wav`

The final scene mix is created only after the creator's dialogue clips are placed.
