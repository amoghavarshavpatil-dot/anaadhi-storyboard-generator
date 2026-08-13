# ANAADHI Storyboard Generator

Private, local-first screenplay-to-storyboard pipeline for **ANAADHI**.

## Goal

Turn the approved screenplay into scene-by-scene cinematic storyboard stills without monthly image credits:

`DOCX / FDX / Fountain / TXT -> scene parser -> shot plan -> continuity locks -> ComfyUI -> 2.39:1 stills -> Scene 001-100 folders`

The project is designed to keep generation local. It does **not** require InVideo, OpenArt, Claude, OpenAI API, or any other paid generation API.

## Current scope

- Parse numbered `SCENE 001` through `SCENE 100` screenplay structure.
- Build deterministic shot candidates from action/dialogue beats.
- Apply global and scene-specific continuity rules before image generation.
- Send prompts to a **local ComfyUI server** through its API.
- Save every image with deterministic names such as `SC001_SH004.png`.
- Native scope target: **2.39:1**, no baked-in black bars.
- Support dry-run mode so the complete shot plan can be reviewed before spending GPU time.

## ANAADHI continuity lock already included

Scene 001 Anaadhi is locked as:

- age 27
- 6 ft 4 in / 193 cm
- heavy-athletic forest-labour build
- topless
- scalp completely shaved with several days of rough regrowth
- no long hair

Scene-specific continuity must override later-character appearance.

## Quick start on Windows

1. Install Python 3.11 or 3.12.
2. Install and run ComfyUI locally.
3. Clone this repository.
4. Run `setup_windows.bat`.
5. Run `run_windows.bat`.
6. Upload the screenplay in the browser UI.
7. Review the parsed scene and shot plan.
8. In ComfyUI, save an API-format workflow as `workflows/workflow_api.json`.
9. Generate one test shot first. Only after continuity is correct, use batch generation.

## Important

The repository contains the pipeline, not a bundled diffusion checkpoint. Model files can be very large and should stay on the local machine under ComfyUI's model directories rather than being committed to GitHub.

The first milestone is **Scene 001 shot-plan + one locally generated scope still**. After that is validated, the same pipeline scales through Scene 100.
