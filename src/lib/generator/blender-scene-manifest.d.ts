/* eslint-disable @typescript-eslint/no-explicit-any */
export interface BlenderSceneOptions {
  validate?: boolean;
  renderView?: "garden" | "street" | "east" | "west";
  cameraAngleDeg?: number;
}
export function buildBlenderSceneManifest(canonical: any, options?: BlenderSceneOptions): any;
export function assertManifestMatchesCanonical(manifest: any, canonical: any): true;
