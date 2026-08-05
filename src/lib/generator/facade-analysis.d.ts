export interface FacadeAnalysisOptions { preferredView?: "garden" | "street" | "east" | "west"; cameraAngleDeg?: number; }
export function analyzeFacades(canonical: Record<string, unknown>, options?: FacadeAnalysisOptions): Record<string, unknown>;
