export const ANAADHI_MASTER_WIDTH = 3840;
export const ANAADHI_MASTER_HEIGHT = 1608;
export const ANAADHI_MASTER_ASPECT = '2.39:1';

// Current working timeline rate only. Final delivery FPS remains a P7 mastering decision.
export const ANAADHI_WORKING_FPS = 30;
export const ANAADHI_WORKING_FPS_IS_CANONICAL = false;

// Remotion requires a positive bootstrap duration before P2 shot manifests exist.
// This one-second empty timeline is infrastructure-only and is not movie content.
export const BOOTSTRAP_DURATION_IN_FRAMES = ANAADHI_WORKING_FPS;
