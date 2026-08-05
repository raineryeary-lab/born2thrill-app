/* eslint-disable @typescript-eslint/no-explicit-any */
export const CORRECTION_SCHEMA: string;
export const DEFAULT_RIGHTS: string;
export const FLOORPLAN_RULEBOOK_VERSION: string;
export const FLOORPLAN_RULES: any;
export const CORRECTION_DEFAULTS: {
  exteriorWallMm: number;
  interiorWallMm: number;
  internalDoorMm: number;
  smallWcDoorMm: number;
  entranceDoorMm: number;
  stairWidthMm: number;
  sourceAxisSnapTolerancePx: number;
  editSnapMm: number;
};
export function canonicalJson(value: unknown): string;
export function correctionGeometryHash(document: any): string;
export function approvedGeometryHash(document: any): string;
export function snapCoordinate(value: number, grid?: number): number;
export function buildCorrectionDocument(variant: any, options?: { createdAt?: string }): any;
export function validateCorrectionDocument(document: any): {
  valid: boolean;
  errors: string[];
  warnings: string[];
  geometry_hash: string;
  hard_checks: Record<string, boolean>;
};
export function withUpdatedHash(document: any): any;
export function createEditorHistory(source: any): any;
export function commitEditorHistory(history: any, next: any): any;
export function undoEditorHistory(history: any): any;
export function redoEditorHistory(history: any): any;
export function resetEditorHistory(history: any): any;
