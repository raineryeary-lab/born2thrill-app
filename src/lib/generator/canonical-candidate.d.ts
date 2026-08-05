/* eslint-disable @typescript-eslint/no-explicit-any */
export const ALLOWED_CANDIDATE_TRANSFORMS: readonly ["identity", "mirror_horizontal", "mirror_vertical"];
export function createCanonicalCandidate(input: { source: any; reference: any; transform: "identity" | "mirror_horizontal" | "mirror_vertical"; validate?: boolean }): any;

