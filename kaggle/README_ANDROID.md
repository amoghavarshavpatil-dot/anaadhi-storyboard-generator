# ANAADHI — Android + Kaggle GPU workflow

This path is for phone-only production. GitHub stores the evolving screenplay/scene manifests; Kaggle provides the temporary GPU runtime.

## First target
Generate one approved still for `SC001_SH001` before scaling.

## Android steps
1. Open Kaggle in Chrome and switch to Desktop site if needed.
2. Create a new Notebook and enable a GPU accelerator.
3. Upload `kaggle/ANAADHI_SCENE_STILL_GENERATOR.ipynb` from this repository into Kaggle.
4. Run cells from top to bottom.
5. In the CONFIG cell, choose the scene/shot and optionally upload reference images.
6. Review the generated PNG before generating the next shot.

## Model
The notebook uses `stabilityai/stable-diffusion-xl-base-1.0` through Hugging Face Diffusers. The model is open-licensed under OpenRAIL++ and can be replaced later through `MODEL_ID`.

## Output
Working generations use a 1344x640 SDXL canvas, then centre-crop to the exact same ratio as the 3840x1608 ANAADHI master. No black bars are added. Final movie assembly remains 3840x1608, 30 fps.

## Production rules
- Do not generate the whole film in one notebook run.
- Generate shot-by-shot or in small approved batches.
- Scene-specific character state overrides generic character references.
- Creator-recorded dialogue remains the master dialogue source.
- Lip-sync is selective and happens only after the visual shot is approved.
- BGM, ambience, Foley and SFX stay separate from dialogue.
- Revised screenplay scenes only regenerate affected shots.

## Scene 001 continuity hard lock
Anaadhi is 27, 6'4 / 193 cm, heavy-athletic from forest labour, topless, with a completely shaved scalp and several days of rough regrowth. Do not use later long-hair continuity in Scene 001.
