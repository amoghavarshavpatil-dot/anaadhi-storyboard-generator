export type ShotManifestEntry = {
  shotId: string;
  source: string;
  durationInFrames: number;
  trimBefore?: number;
  volume?: number;
};

export type AnaadhiAssemblyProps = {
  shots: ShotManifestEntry[];
};
