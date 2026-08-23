# SuperCool Storyboard Execution — SC001–SC005

## Single execution command

Use the authenticated `supercool` MCP server and execute
`production/supercool/SUPERCOOL_STORYBOARD_QUEUE_SC001_SC005.yaml` exactly.

## Non-negotiable runtime rules

1. Generate **still images only**, exactly **one candidate per shot**, in the queue order.
2. The run begins at `SC001_SH001` and may advance only after the current candidate is retrievable in the authenticated SuperCool account.
3. Before the first paid generation, inspect available SuperCool tools and choose a still-image tool that can accept the references required by the shot. Do not use video generation.
4. Create/reuse the SuperCool session `ANAADHI Storyboard SC001-SC005 Run 01`.
5. After `SC001_SH001`, verify its asset/session/download retrieval inside SuperCool. If this cannot be verified, stop before spending on `SC001_SH002`.
6. Use existing SuperCool credits only. **Pay As You Go stays OFF. No top-up, subscription change, purchase, or external paid API is authorized.**
7. Query live SuperCool credits before each shot when the MCP exposes balance/cost information. If it does not, continue only until SuperCool explicitly rejects a generation for insufficient credits, then stop without retry.
8. No aesthetic retries. A generated candidate is `CANDIDATE_READY`, never `FINAL_APPROVED` until the user reviews it.
9. Do not skip a failed/blocked shot to spend credits on later shots.
10. Update `production/supercool/runs/ANAADHI_SC001_SC005_SUPERCOOL_RUN01/ledger.yaml` after every successful generation. Commit ledger progress at each completed scene and once when the run stops.

## Source resolution

- SC001: read `scenes/001/scene.yaml`; use each existing `visual_prompt`/`negative_prompt` plus the queue's locked TP001/SB001 continuity.
- SC002–SC005: read each deterministic Remotion shot package under `production/remotion/shot_specs/SC00x/`.
- Resolve repository-approved reference assets before generation. If the selected image tool cannot ingest a reference that is essential to character/location/prop continuity, stop before spending credits.

## Output naming

`ANAADHI_<SHOT_ID>_CANDIDATE_01`

Keep the generated asset in the authenticated SuperCool account/session and store its returned asset ID plus download/retrieval URL in the ledger. Do not download or commit binary generated images to GitHub during the bulk run.

## End conditions

The run ends at the first of:
- `SC005_SH024` completed;
- SuperCool has insufficient credits for the next shot;
- a required reference cannot be passed safely;
- the generated asset cannot be retrieved from SuperCool;
- any source/continuity blocker occurs.

On stop, report: last completed shot, next shot, candidates generated, live remaining credits if available, SuperCool session ID/name, and ledger commit SHA.
