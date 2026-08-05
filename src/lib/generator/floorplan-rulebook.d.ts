export const FLOORPLAN_RULEBOOK_VERSION: string;
export const FLOORPLAN_RULES: any;
export function normalizedRoomRuleKey(room: any): string | null;
export function isHabitableRoom(room: any): boolean;
export function doorCategory(opening: any): "mainEntrance" | "smallWc" | "internal";
export function doorColour(opening: any): string;
