export type ApprovedShotAsset = {
  readonly path: string;
  readonly lifecycle: 'APPROVED_SHOT';
  readonly version: string;
};

export const approvedShotAssets: Readonly<Record<string, ApprovedShotAsset>> = {
  SC001_SH001: {
    path: 'shots/SC001/SC001_SH001/B01_SC001_SH001_V001_APPROVED_3840x1600.png',
    lifecycle: 'APPROVED_SHOT',
    version: 'V001',
  },
};
