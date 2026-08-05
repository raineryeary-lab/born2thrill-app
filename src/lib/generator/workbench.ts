import type { PlanVariant, PlannedRoom } from "./floorplan";

type RoomPlacement = Pick<
  PlannedRoom,
  "x" | "y" | "width" | "height" | "area" | "side" | "zone" | "polygon"
>;

function copyRoomPlacement(room: PlannedRoom): RoomPlacement {
  return {
    x: room.x,
    y: room.y,
    width: room.width,
    height: room.height,
    area: room.area,
    side: room.side,
    zone: room.zone,
    polygon: room.polygon?.map((point) => ({ ...point })),
  };
}

function applyRoomPlacement(room: PlannedRoom, placement: RoomPlacement) {
  room.x = placement.x;
  room.y = placement.y;
  room.width = placement.width;
  room.height = placement.height;
  room.area = placement.area;
  room.side = placement.side;
  room.zone = placement.zone;
  room.polygon = placement.polygon?.map((point) => ({ ...point }));
}

export function swapRoomPlacements(
  source: PlanVariant,
  floorNumber: number,
  firstRoomId: string,
  secondRoomId: string,
): PlanVariant {
  if (firstRoomId === secondRoomId) {
    throw new Error("Bitte zwei unterschiedliche Räume auswählen.");
  }

  const variant = structuredClone(source);
  const floor = variant.floors.find((candidate) => candidate.floor === floorNumber);
  if (!floor) throw new Error("Das ausgewählte Geschoss wurde nicht gefunden.");

  const first = floor.rooms.find((room) => room.id === firstRoomId);
  const second = floor.rooms.find((room) => room.id === secondRoomId);
  if (!first || !second) {
    throw new Error("Mindestens einer der ausgewählten Räume wurde nicht gefunden.");
  }

  const firstPlacement = copyRoomPlacement(first);
  const secondPlacement = copyRoomPlacement(second);
  applyRoomPlacement(first, secondPlacement);
  applyRoomPlacement(second, firstPlacement);

  variant.score = 0;
  variant.checks = [{
    label: "Manueller Raumtausch: Türen, Fenster, Erschließung und Flächen müssen fachlich geprüft werden.",
    passed: false,
  }];
  return variant;
}
