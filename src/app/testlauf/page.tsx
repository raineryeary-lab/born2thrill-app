"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import type {
  FloorPlan,
  HouseBrief,
  PlanVariant,
  PlannedRoom,
} from "@/lib/generator/floorplan";
import { swapRoomPlacements } from "@/lib/generator/workbench";

type FeedbackRating = "up" | "down";

type TestlaufFeedback = {
  id: string;
  createdAt: string;
  rating: FeedbackRating;
  reason: string;
  variantId: string;
  variantName: string;
  score: number;
  brief: HouseBrief;
  metrics: PlanVariant["metrics"];
  failedChecks: string[];
};

type SelectedRoom = {
  floor: number;
  floorName: string;
  room: PlannedRoom;
};

type LearningCorrection = {
  id: string;
  createdAt: string;
  variantId: string;
  variantName: string;
  floor: number;
  floorName: string;
  targetRoomId: string;
  targetRoomName: string;
  action: "room_to_circulation" | "increase_room_area" | "decrease_room_area" | "door_window_issue";
  reason: string;
  before: {
    name: string;
    kind: PlannedRoom["kind"];
    area: number;
    x: number;
    y: number;
    width: number;
    height: number;
  };
  structuredConstraints: Array<Record<string, string | number>>;
};

type SavedWorkbenchPlan = {
  id: string;
  savedAt: string;
  reviewStatus: "generated_candidate";
  trainingEligible: false;
  brief: HouseBrief;
  variant: PlanVariant;
};

type WorkbenchGeneration = {
  brief: HouseBrief;
  variants: PlanVariant[];
};

type ReviewQueueResponse = {
  count: number;
  error?: string;
};

type SpeechRecognitionResultLike = {
  isFinal: boolean;
  [index: number]: { transcript: string };
};

type SpeechRecognitionEventLike = {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: SpeechRecognitionResultLike;
  };
};

type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  }
}

type StairPoint = { x: number; y: number };

function stairArrowHead(path: StairPoint[], size = 9) {
  const end = path.at(-1); const previous = path.at(-2);
  if (!end || !previous) return null;
  const dx = end.x - previous.x; const dy = end.y - previous.y;
  const length = Math.hypot(dx, dy);
  if (!length) return null;
  const ux = dx / length; const uy = dy / length;
  const nx = -uy; const ny = ux;
  const baseX = end.x - ux * size; const baseY = end.y - uy * size;
  return `${end.x},${end.y} ${baseX + nx * size * 0.55},${baseY + ny * size * 0.55} ${baseX - nx * size * 0.55},${baseY - ny * size * 0.55}`;
}
function FloorSvg({
  plan,
  selectedRoomId,
  onSelectRoom,
}: {
  plan: FloorPlan;
  selectedRoomId?: string | null;
  onSelectRoom?: (selection: SelectedRoom) => void;
}) {
  const stair = plan.stair;
  const referenceBased = Boolean(plan.referenceLayoutId);
  const referenceGeometry = useMemo(() => {
    if (!referenceBased) return null;
    const boxes = plan.rooms.map((room) => {
      const points = room.polygon ?? [];
      const xs = points.map((point) => point.x);
      const ys = points.map((point) => point.y);
      return { id: room.id, x1: xs.length ? Math.min(...xs) : room.x, y1: ys.length ? Math.min(...ys) : room.y, x2: xs.length ? Math.max(...xs) : room.x + room.width, y2: ys.length ? Math.max(...ys) : room.y + room.height, area: room.area };
    });
    const snapAxis = (values: number[], tolerance = 10) => {
      const groups: number[][] = [];
      [...values].sort((a, b) => a - b).forEach((value) => {
        const group = groups.find((candidate) => Math.abs(candidate.reduce((sum, item) => sum + item, 0) / candidate.length - value) <= tolerance);
        if (group) group.push(value); else groups.push([value]);
      });
      const centers = groups.map((group) => group.reduce((sum, value) => sum + value, 0) / group.length);
      return (value: number) => centers.reduce((best, center) => Math.abs(center - value) < Math.abs(best - value) ? center : best, centers[0] ?? value);
    };
    const snapX = snapAxis(boxes.flatMap((box) => [box.x1, box.x2]));
    const snapY = snapAxis(boxes.flatMap((box) => [box.y1, box.y2]));
    const rooms = new Map(boxes.map((box) => {
      const x1 = snapX(box.x1); const x2 = snapX(box.x2); const y1 = snapY(box.y1); const y2 = snapY(box.y2);
      return [box.id, { x: x1, y: y1, width: Math.max(1, x2 - x1), height: Math.max(1, y2 - y1) }];
    }));
    const rects = [...rooms.values()];
    const minX = Math.min(...rects.map((rect) => rect.x)); const minY = Math.min(...rects.map((rect) => rect.y));
    const footprint = plan.referenceFootprint ?? { x: minX, y: minY, width: Math.max(...rects.map((rect) => rect.x + rect.width)) - minX, height: Math.max(...rects.map((rect) => rect.y + rect.height)) - minY };
    const pixelArea = rects.reduce((sum, rect) => sum + rect.width * rect.height, 0);
    const floorArea = boxes.reduce((sum, box) => sum + box.area, 0);
    const pixelsPerMeter = Math.sqrt(pixelArea / Math.max(floorArea, 1));    const squarePixelsPerMeter = pixelsPerMeter * pixelsPerMeter;
    const htrRoom = plan.rooms.find((room) => /\bHTR\b|\bHWR\b/i.test(room.name));
    const htrRect = htrRoom ? rooms.get(htrRoom.id) : undefined;
    if (htrRect) {
      const desiredWidth = Math.min(footprint.width * 0.34, Math.max(htrRect.width, (10 * squarePixelsPerMeter) / Math.max(htrRect.height, 1)));
      const oldX = htrRect.x; const oldRight = htrRect.x + htrRect.width;
      if (htrRect.x + htrRect.width / 2 > footprint.x + footprint.width / 2) {
        htrRect.x = oldRight - desiredWidth; htrRect.width = desiredWidth;
        plan.rooms.filter((room) => room.kind === "circulation").forEach((room) => {
          const rect = rooms.get(room.id);
          if (rect && rect.x < oldX && rect.y < htrRect.y + htrRect.height && rect.y + rect.height > htrRect.y) rect.width = Math.max(1, htrRect.x - rect.x);
        });
      } else {
        htrRect.width = desiredWidth;
        plan.rooms.filter((room) => room.kind === "circulation").forEach((room) => {
          const rect = rooms.get(room.id);
          if (rect && rect.x > oldX && rect.y < htrRect.y + htrRect.height && rect.y + rect.height > htrRect.y) {
            const right = rect.x + rect.width; rect.x = htrRect.x + htrRect.width; rect.width = Math.max(1, right - rect.x);
          }
        });
      }
    }
    if (htrRect && plan.stairRect && htrRect.x > plan.stairRect.x) {
      const right = htrRect.x + htrRect.width;
      htrRect.x = plan.stairRect.x + plan.stairRect.width;
      htrRect.width = Math.max(1, right - htrRect.x);
    }    if (plan.floor > 0 && plan.stairRect) {
      const stairLeft = plan.stairRect.x; const stairRight = plan.stairRect.x + plan.stairRect.width;
      plan.rooms.filter((room) => /bad/i.test(room.name)).forEach((room) => {
        const rect = rooms.get(room.id); if (!rect) return;
        const leftGap = rect.x - stairRight; const rightGap = stairLeft - (rect.x + rect.width);
        if (leftGap > 0 && leftGap <= 60) { rect.x = stairRight; rect.width += leftGap; }
        else if (rightGap > 0 && rightGap <= 60) rect.width += rightGap;
      });
    }
    return {
      rooms,
      footprint,
      pixelsPerMeter,
      innerWallPx: Math.max(2, Math.min(5, pixelsPerMeter * 0.1)),
      outerWallPx: Math.max(7, Math.min(14, pixelsPerMeter * 0.35)),
    };
  }, [plan, referenceBased]);
  const projectOpeningToWall = (
    points: Array<{ x: number; y: number }>,
    openingType = "window",
  ) => {
    const first = points[0]; const second = points[1];
    if (!first || !second || !referenceGeometry) return null;
    const horizontal = Math.abs(second.x - first.x) >= Math.abs(second.y - first.y);
    const midpoint = { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2 };
    const rects = [...referenceGeometry.rooms.values(), referenceGeometry.footprint];
    const candidates = rects.flatMap((rect) => horizontal
      ? [{ axis: rect.y, start: rect.x, end: rect.x + rect.width }, { axis: rect.y + rect.height, start: rect.x, end: rect.x + rect.width }]
      : [{ axis: rect.x, start: rect.y, end: rect.y + rect.height }, { axis: rect.x + rect.width, start: rect.y, end: rect.y + rect.height }]);
    const along = horizontal ? midpoint.x : midpoint.y; const across = horizontal ? midpoint.y : midpoint.x;
    const best = candidates.reduce((winner, candidate) => {
      const outside = along < candidate.start ? candidate.start - along : along > candidate.end ? along - candidate.end : 0;
      const score = Math.abs(candidate.axis - across) + outside * 3;
      return !winner || score < winner.score ? { ...candidate, score } : winner;
    }, null as null | { axis: number; start: number; end: number; score: number });
    if (!best) return null;
    const adjacentRooms = plan.rooms.filter((room) => {
      const rect = referenceGeometry.rooms.get(room.id);
      if (!rect) return false;
      if (horizontal) {
        const sharesAxis = Math.min(
          Math.abs(rect.y - best.axis),
          Math.abs(rect.y + rect.height - best.axis),
        ) <= 4;
        return sharesAxis && along >= rect.x - 4 && along <= rect.x + rect.width + 4;
      }
      const sharesAxis = Math.min(
        Math.abs(rect.x - best.axis),
        Math.abs(rect.x + rect.width - best.axis),
      ) <= 4;
      return sharesAxis && along >= rect.y - 4 && along <= rect.y + rect.height + 4;
    });
    const footprint = referenceGeometry.footprint;
    const exterior = horizontal
      ? Math.min(Math.abs(best.axis - footprint.y), Math.abs(best.axis - (footprint.y + footprint.height))) <= 4
      : Math.min(Math.abs(best.axis - footprint.x), Math.abs(best.axis - (footprint.x + footprint.width))) <= 4;
    const smallWc = adjacentRooms.some((room) => /\bWC\b/i.test(room.name) && room.area <= 4);
    const entrance = plan.floor === 0
      && exterior
      && adjacentRooms.some((room) => room.kind === "circulation");
    const originalLength = Math.hypot(second.x - first.x, second.y - first.y);
    const targetDoorWidthM = entrance ? 1.1 : smallWc ? 0.76 : 0.88;
    const desiredLength = openingType === "door"
      ? targetDoorWidthM * referenceGeometry.pixelsPerMeter
      : originalLength;
    const minimumLength = openingType === "door" ? 12 : 18;
    const length = Math.max(
      minimumLength,
      Math.min(70, desiredLength, Math.max(minimumLength, best.end - best.start - 12)),
    );
    const center = Math.max(best.start + length / 2 + 4, Math.min(best.end - length / 2 - 4, along));
    return horizontal
      ? [{ x: center - length / 2, y: best.axis }, { x: center + length / 2, y: best.axis }]
      : [{ x: best.axis, y: center - length / 2 }, { x: best.axis, y: center + length / 2 }];
  };  const wcHallDoor = (() => {
    if (!referenceGeometry) return null;
    const wc = plan.rooms.find((room) => /\bWC\b/i.test(room.name));
    const wcRect = wc ? referenceGeometry.rooms.get(wc.id) : undefined;
    if (!wcRect) return null;
    const halls = plan.rooms.filter((room) => room.kind === "circulation").map((room) => referenceGeometry.rooms.get(room.id)).filter(Boolean) as Array<{ x: number; y: number; width: number; height: number }>;
    let best: null | { gap: number; x: number; y1: number; y2: number } = null;
    halls.forEach((hall) => {
      const y1 = Math.max(wcRect.y, hall.y); const y2 = Math.min(wcRect.y + wcRect.height, hall.y + hall.height);
      if (y2 - y1 < 22) return;
      const leftGap = Math.abs(wcRect.x - (hall.x + hall.width));
      const rightGap = Math.abs(wcRect.x + wcRect.width - hall.x);
      const candidate = leftGap <= rightGap ? { gap: leftGap, x: wcRect.x, y1, y2 } : { gap: rightGap, x: wcRect.x + wcRect.width, y1, y2 };
      if (!best || candidate.gap < best.gap) best = candidate;
    });
    const selectedDoor = best as null | { gap: number; x: number; y1: number; y2: number };
    if (!selectedDoor || selectedDoor.gap > 18) return null;
    const center = (selectedDoor.y1 + selectedDoor.y2) / 2;
    const length = Math.min(
      selectedDoor.y2 - selectedDoor.y1 - 8,
      0.76 * referenceGeometry.pixelsPerMeter,
    );
    return [
      { x: selectedDoor.x, y: center - length / 2 },
      { x: selectedDoor.x, y: center + length / 2 },
    ];
  })();  const entryDoor = (() => {
    if (!referenceGeometry || plan.floor !== 0) return null;
    const hall = plan.rooms.filter((room) => room.kind === "circulation").map((room) => referenceGeometry.rooms.get(room.id)).find((rect) => rect && rect.y + rect.height >= referenceGeometry.footprint.y + referenceGeometry.footprint.height - 12);
    if (!hall) return null;
    const wallY = referenceGeometry.footprint.y + referenceGeometry.footprint.height;
    const availableStart = Math.max(hall.x + 6, referenceGeometry.footprint.x + 12);
    const availableEnd = Math.min(hall.x + hall.width - 6, (plan.stairRect?.x ?? hall.x + hall.width) - 7);
    if (availableEnd - availableStart < 20) return null;
    const length = Math.min(1.1 * referenceGeometry.pixelsPerMeter, availableEnd - availableStart);
    const center = (availableStart + availableEnd) / 2;
    return [{ x: center - length / 2, y: wallY }, { x: center + length / 2, y: wallY }];
  })();  const wallStair = plan.layoutMode === "wall-stair";
  const hallX = wallStair ? 306 : 220;
  const hallWidth = wallStair ? 88 : 260;
  const wallStairX = plan.wallStairSide === "left" ? 56 : 512;
  const wallStairY = 100;
  const wallStairWidth = 132;
  const wallStairHeight = 184;
  const wallStairTextX = wallStairX + wallStairWidth / 2;
  const wallStairConnectorX = plan.wallStairSide === "left" ? wallStairX + wallStairWidth : hallX + hallWidth;
  const wallStairConnectorWidth = plan.wallStairSide === "left" ? hallX - wallStairConnectorX : wallStairX - wallStairConnectorX;
  const wallStairLandingX = wallStairConnectorX + 8;
  const wallStairLandingWidth = Math.max(44, wallStairConnectorWidth - 16);
  const internalDoorPx = 44;
  const smallWcDoorPx = 38;
  const frontDoorPx = 55;
  const doorSwingArc45 = (hingeX: number, hingeY: number, radius: number, direction: -1 | 1) => {
    const angle = Math.PI / 4;
    const startX = hingeX;
    const startY = hingeY - radius;
    const endX = hingeX + direction * radius * Math.sin(angle);
    const endY = hingeY - radius * Math.cos(angle);
    const controlX = hingeX + direction * radius * 0.38;
    const controlY = startY;
    return `M${startX} ${startY} Q${controlX} ${controlY} ${endX} ${endY}`;
  };
  const frontDoorLeafEndX = 330 + frontDoorPx * Math.cos(Math.PI / 4);
  const frontDoorLeafEndY = 480 - frontDoorPx * Math.sin(Math.PI / 4);
  return (
    <svg viewBox="0 0 700 500" className="w-full rounded-xl bg-[#faf9f6]" aria-label={`Grundriss ${plan.name}`}>
      {referenceGeometry ? <rect x={referenceGeometry.footprint.x} y={referenceGeometry.footprint.y} width={referenceGeometry.footprint.width} height={referenceGeometry.footprint.height} fill="white" /> : <rect x="20" y="20" width="660" height="460" fill="white" stroke="#1c1917" strokeWidth="8" />}
      {wallStair && !referenceBased && (
        <g>
          <rect x={Math.min(wallStairX, hallX)} y="86" width={Math.max(wallStairX + wallStairWidth, hallX + hallWidth) - Math.min(wallStairX, hallX)} height="216" fill="#f0eee8" stroke="#78716c" strokeWidth="2" />
          <text x={wallStairConnectorX + wallStairConnectorWidth / 2} y="246" textAnchor="middle" fontSize="10" fill="#57534e">TREPPENFLUR</text>
        </g>
      )}
      {!referenceBased && (<>
        <rect x={hallX} y="24" width={hallWidth} height="452" fill="#f0eee8" stroke="#78716c" strokeWidth="2" />
        <text x={hallX + hallWidth / 2} y="55" textAnchor="middle" fontSize="12" fill="#57534e">{wallStair ? "KURZER FLUR" : "FLUR"}</text>
      </>)}
      {plan.hasStair && stair && !wallStair && !referenceBased && (
        <g>
          <rect x="284" y="66" width="132" height="184" rx="3" fill="#e7e5e4" stroke="#292524" strokeWidth="2" />
          <rect x="284" y="66" width="132" height="58" fill="#d6d3d1" stroke="#292524" strokeWidth="1.5" />
          <line x1="345" x2="345" y1="124" y2="250" stroke="#292524" strokeWidth="2" />
          {Array.from({ length: 7 }, (_, index) => (
            <g key={index}>
              <line x1="284" x2="345" y1={142 + index * 16} y2={142 + index * 16} stroke="#78716c" />
              <line x1="345" x2="416" y1={142 + index * 16} y2={142 + index * 16} stroke="#78716c" />
            </g>
          ))}
          <path d="M314 235 L314 137 M314 137 L307 150 M314 137 L321 150" fill="none" stroke="#18392f" strokeWidth="3" />
          <path d="M380 137 L380 235 M380 235 L373 222 M380 235 L387 222" fill="none" stroke="#18392f" strokeWidth="3" />
          <rect x="224" y="66" width="52" height="270" fill="#fff" fillOpacity=".45" stroke="#0f766e" strokeDasharray="5 4" />
          <rect x="424" y="66" width="52" height="270" fill="#fff" fillOpacity=".45" stroke="#0f766e" strokeDasharray="5 4" />
          <text x="250" y="200" textAnchor="middle" fontSize="10" fill="#0f766e" transform="rotate(-90 250 200)">1,00 m FREIER WEG</text>
          <text x="450" y="200" textAnchor="middle" fontSize="10" fill="#0f766e" transform="rotate(90 450 200)">1,00 m FREIER WEG</text>
          <rect x="284" y="258" width="132" height="62" fill="none" stroke="#0f766e" strokeDasharray="6 4" />
          <text x="350" y="286" textAnchor="middle" fontSize="10" fill="#0f766e">FREIE ANKUNFT</text>
          <text x="350" y="302" textAnchor="middle" fontSize="9" fill="#57534e">mind. {stair.clearArrivalDepthM.toFixed(2)} m</text>
          <text x="350" y="45" textAnchor="middle" fontSize="10" fill="#57534e">U-TREPPE {stair.footprintWidthM.toFixed(2)} × {stair.footprintLengthM.toFixed(2)} m</text>
        </g>
      )}
      {plan.floor === 0 && !referenceBased && (
        <g>
          <line x1="330" y1="480" x2={330 + frontDoorPx} y2="480" stroke="white" strokeWidth="10" />
          <line x1="330" y1="480" x2={frontDoorLeafEndX} y2={frontDoorLeafEndY} stroke="#0f766e" strokeWidth="2.5" />
          <path d={`M${330 + frontDoorPx} 480 Q${330 + frontDoorPx} ${frontDoorLeafEndY} ${frontDoorLeafEndX} ${frontDoorLeafEndY}`} fill="none" stroke="#0f766e" strokeWidth="2" />
        </g>
      )}
      {plan.rooms.map((room) => {
        const doorX = room.side === "left" ? room.x + room.width : room.x;
        const windowX = room.side === "left" ? room.x : room.x + room.width;
        const cy = room.y + room.height / 2;
        const roomDoorPx = /\bWC\b/i.test(room.name) && room.area <= 4
          ? smallWcDoorPx
          : internalDoorPx;
        const doorFits = room.height >= roomDoorPx + 20;
        const doorDirection = room.side === "left" ? -1 : 1;
        const hingeY = cy + roomDoorPx / 2;
        const doorLeafEndX = doorX + doorDirection * roomDoorPx * Math.sin(Math.PI / 4);
        const doorLeafEndY = hingeY - roomDoorPx * Math.cos(Math.PI / 4);
        const farSideY = hingeY - roomDoorPx;
        const doorArc = doorSwingArc45(doorX, hingeY, roomDoorPx, doorDirection);
        const selected = selectedRoomId === room.id;
        const fill = room.kind === "circulation" ? "#f0eee8" : room.kind === "wet" ? "#dbeafe" : room.kind === "living" ? "#dcfce7" : room.kind === "service" ? "#fef3c7" : "#f5f5f4";
        const drawDoorAndWindow = !referenceBased && room.kind !== "circulation";
        const polygonPoints = room.polygon?.map((point) => `${point.x},${point.y}`).join(" ");        const displayRoom = referenceGeometry?.rooms.get(room.id);
        const labelX = displayRoom ? displayRoom.x + displayRoom.width / 2 : room.x + room.width / 2;
        const stairCoversRoom = Boolean(displayRoom && plan.stairRect && displayRoom.x < plan.stairRect.x + plan.stairRect.width && displayRoom.x + displayRoom.width > plan.stairRect.x && displayRoom.y < plan.stairRect.y + plan.stairRect.height && displayRoom.y + displayRoom.height > plan.stairRect.y);
        const labelY = displayRoom ? stairCoversRoom ? displayRoom.y + 25 : displayRoom.y + displayRoom.height / 2 : cy;
        const compactLabel = Boolean(displayRoom && displayRoom.width < 78);
        return (
          <g key={room.id} role="button" tabIndex={0} className="cursor-pointer" onClick={() => onSelectRoom?.({ floor: plan.floor, floorName: plan.name, room })} onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") onSelectRoom?.({ floor: plan.floor, floorName: plan.name, room });
          }}>            {displayRoom
              ? <rect x={displayRoom.x} y={displayRoom.y} width={displayRoom.width} height={displayRoom.height} fill={fill} stroke={selected ? "#f97316" : "#57534e"} strokeWidth={selected ? 4 : referenceGeometry?.innerWallPx ?? 2} />
              : polygonPoints
                ? <polygon points={polygonPoints} fill={fill} stroke={selected ? "#f97316" : "#57534e"} strokeWidth={selected ? "4" : "2"} />
                : <rect x={room.x} y={room.y} width={room.width} height={room.height} fill={fill} stroke={selected ? "#f97316" : "#57534e"} strokeWidth={selected ? "4" : "2"} />}
            <text x={labelX} y={labelY - 5} textAnchor="middle" fontSize={compactLabel ? 12 : 15} fontWeight="600" fill="#292524">{room.name}</text>
            <text x={labelX} y={labelY + 16} textAnchor="middle" fontSize="12" fill="#78716c">ca. {room.area} m²</text>            {drawDoorAndWindow && (
              <>
                <line x1={windowX} x2={windowX} y1={cy - 23} y2={cy + 23} stroke="white" strokeWidth="10" />
                <line x1={windowX} x2={windowX} y1={cy - 20} y2={cy + 20} stroke="#0ea5e9" strokeWidth="5" />
                {doorFits && (
                  <>
                    <line x1={doorX} x2={doorX} y1={farSideY} y2={hingeY} stroke="white" strokeWidth="9" />
                    <line x1={doorX} x2={doorLeafEndX} y1={hingeY} y2={doorLeafEndY} stroke="#0f766e" strokeWidth="2.5" />
                    <path d={doorArc} fill="none" stroke="#0f766e" strokeWidth="2" />
                  </>
                )}
              </>
            )}
          </g>
        );
      })}
      {wcHallDoor && <g><line x1={wcHallDoor[0].x} y1={wcHallDoor[0].y} x2={wcHallDoor[1].x} y2={wcHallDoor[1].y} stroke="white" strokeWidth={(referenceGeometry?.innerWallPx ?? 2) + 5} /><line x1={wcHallDoor[0].x} y1={wcHallDoor[0].y} x2={wcHallDoor[1].x} y2={wcHallDoor[1].y} stroke="#0f766e" strokeWidth="2" /></g>}      {referenceGeometry && <rect x={referenceGeometry.footprint.x} y={referenceGeometry.footprint.y} width={referenceGeometry.footprint.width} height={referenceGeometry.footprint.height} fill="none" stroke="#1c1917" strokeWidth={referenceGeometry.outerWallPx} />}      {entryDoor && <g><line x1={entryDoor[0].x} y1={entryDoor[0].y} x2={entryDoor[1].x} y2={entryDoor[1].y} stroke="white" strokeWidth={(referenceGeometry?.outerWallPx ?? 8) + 3} /><line x1={entryDoor[0].x} y1={entryDoor[0].y} x2={entryDoor[1].x} y2={entryDoor[1].y} stroke="#0f766e" strokeWidth="2.5" /></g>}
      {referenceBased && plan.stairPath && plan.stairPath.length >= 2 && plan.stairWidthPx && stair && (
        <g>
          <polyline points={plan.stairPath.map((point) => `${point.x},${point.y}`).join(" ")} fill="none" stroke="#292524" strokeWidth={plan.stairWidthPx + 4} strokeLinejoin="miter" strokeLinecap="butt" />
          <polyline points={plan.stairPath.map((point) => `${point.x},${point.y}`).join(" ")} fill="none" stroke="#e7e5e4" strokeWidth={plan.stairWidthPx} strokeLinejoin="miter" strokeLinecap="butt" />
          <polyline points={plan.stairPath.map((point) => `${point.x},${point.y}`).join(" ")} fill="none" stroke="#18392f" strokeWidth="2.5" strokeLinejoin="miter" strokeLinecap="butt" />
          {stairArrowHead(plan.stairPath) && <polygon points={stairArrowHead(plan.stairPath)!} fill="#18392f" />}
        </g>
      )}
      {plan.referenceElements?.filter((element) => element.type === "door" || element.type === "window").map((element) => {
        const opening = projectOpeningToWall(element.points, element.type);
        const first = opening?.[0]; const second = opening?.[1];
        if (!first || !second) return null;
        return <g key={element.id}><line x1={first.x} y1={first.y} x2={second.x} y2={second.y} stroke="white" strokeWidth={(referenceGeometry?.outerWallPx ?? 8) + 3} strokeLinecap="butt" /><line x1={first.x} y1={first.y} x2={second.x} y2={second.y} stroke={element.type === "window" ? "#0ea5e9" : "#0f766e"} strokeWidth={element.type === "window" ? "3" : "2"} strokeLinecap="round" /></g>;
      })}      {plan.hasStair && stair && wallStair && !referenceBased && (
        <g>
          <rect x={wallStairX} y={wallStairY} width={wallStairWidth} height={wallStairHeight} rx="3" fill="#e7e5e4" stroke="#292524" strokeWidth="2" />
          <rect x={wallStairX} y={wallStairY} width={wallStairWidth} height="58" fill="#d6d3d1" stroke="#292524" strokeWidth="1.5" />
          <line x1={wallStairX + 61} x2={wallStairX + 61} y1={wallStairY + 58} y2={wallStairY + wallStairHeight} stroke="#292524" strokeWidth="2" />
          {Array.from({ length: 7 }, (_, index) => (
            <g key={index}>
              <line x1={wallStairX} x2={wallStairX + 61} y1={wallStairY + 76 + index * 16} y2={wallStairY + 76 + index * 16} stroke="#78716c" />
              <line x1={wallStairX + 61} x2={wallStairX + wallStairWidth} y1={wallStairY + 76 + index * 16} y2={wallStairY + 76 + index * 16} stroke="#78716c" />
            </g>
          ))}
          <path d={`M${wallStairX + 30} ${wallStairY + 170} L${wallStairX + 30} ${wallStairY + 72} M${wallStairX + 30} ${wallStairY + 72} L${wallStairX + 23} ${wallStairY + 85} M${wallStairX + 30} ${wallStairY + 72} L${wallStairX + 37} ${wallStairY + 85}`} fill="none" stroke="#18392f" strokeWidth="3" />
          <path d={`M${wallStairX + 96} ${wallStairY + 72} L${wallStairX + 96} ${wallStairY + 170} M${wallStairX + 96} ${wallStairY + 170} L${wallStairX + 89} ${wallStairY + 157} M${wallStairX + 96} ${wallStairY + 170} L${wallStairX + 103} ${wallStairY + 157}`} fill="none" stroke="#18392f" strokeWidth="3" />
          <rect x={wallStairLandingX} y="258" width={wallStairLandingWidth} height="38" fill="#fff" fillOpacity=".65" stroke="#0f766e" strokeDasharray="6 4" />
          <text x={wallStairLandingX + wallStairLandingWidth / 2} y="278" textAnchor="middle" fontSize="9" fill="#0f766e">ANKUNFT</text>
          <text x={wallStairLandingX + wallStairLandingWidth / 2} y="291" textAnchor="middle" fontSize="8" fill="#57534e">≥ {stair.clearArrivalDepthM.toFixed(2)} m</text>
          <text x={wallStairTextX} y={wallStairY - 14} textAnchor="middle" fontSize="10" fill="#57534e">TREPPE AN AUSSENWAND</text>
        </g>
      )}
      <text x="30" y="16" fontSize="11" fill="#78716c">N ↑</text>
    </svg>
  );
}

function HouseRendering({ brief }: { brief: HouseBrief }) {
  const flat = brief.roof === "flat";
  return (
    <svg viewBox="0 0 900 520" className="w-full rounded-2xl bg-[#dfe8e2]" aria-label="Generierte Hausansicht">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#c9ddd9" /><stop offset="1" stopColor="#f4efe6" /></linearGradient>
        <linearGradient id="facade" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#f8f5ed" /><stop offset="1" stopColor="#d8d1c5" /></linearGradient>
      </defs>
      <rect width="900" height="520" fill="url(#sky)" />
      <circle cx="710" cy="95" r="42" fill="#fff4c4" opacity=".8" />
      <path d="M0 405 Q180 360 330 401 T650 392 T900 385 V520 H0Z" fill="#73936f" />
      <path d="M80 445 Q300 395 520 445 T900 430" fill="none" stroke="#b6a184" strokeWidth="26" opacity=".6" />
      <rect x="235" y={brief.floors > 1 ? 190 : 270} width="450" height={brief.floors > 1 ? 235 : 155} fill="url(#facade)" stroke="#554b40" strokeWidth="3" />
      {flat ? (
        <rect x="220" y={brief.floors > 1 ? 174 : 254} width="480" height="24" fill="#4b4b45" />
      ) : (
        <path d={brief.floors > 1 ? "M205 195 L460 75 L715 195Z" : "M205 275 L460 155 L715 275Z"} fill="#4f4a43" stroke="#352f2a" strokeWidth="4" />
      )}
      {Array.from({ length: brief.floors > 1 ? 2 : 1 }, (_, row) =>
        [285, 410, 555].map((x) => (
          <g key={`${row}-${x}`}>
            <rect x={x} y={brief.floors > 1 ? 230 + row * 100 : 310} width="72" height="65" fill="#8fb4bf" stroke="#3f4d50" strokeWidth="4" />
            <line x1={x + 36} x2={x + 36} y1={brief.floors > 1 ? 230 + row * 100 : 310} y2={brief.floors > 1 ? 295 + row * 100 : 375} stroke="#e9f2f2" strokeWidth="3" />
          </g>
        )),
      )}
      <rect x="442" y={brief.floors > 1 ? 332 : 332} width="52" height="93" fill="#8d6d4f" />
      <path d="M120 420 Q145 330 170 420 M735 420 Q760 315 790 420" stroke="#355f3d" strokeWidth="18" fill="none" />
      <text x="35" y="45" fontSize="16" fill="#38534d">KONZEPTANSICHT · {brief.projectName.toUpperCase()}</text>
      <text x="35" y="70" fontSize="12" fill="#59716b">{brief.style.replaceAll("-", " ")} · Garten {brief.gardenDirection}</text>
    </svg>
  );
}

function feedbackLabel(rating: FeedbackRating) {
  return rating === "up" ? "Daumen hoch" : "Daumen runter";
}

function upsertEntry(entries: Array<[string, string]>, name: string, value: string) {
  const next = entries.filter(([entryName]) => entryName !== name);
  next.push([name, value]);
  return next;
}

function compactCritique(text: string) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (cleaned.length <= 260) return cleaned;
  return `${cleaned.slice(0, 260).trim()} …`;
}

function cleanFeedbackReason(text: string) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  const chunks = cleaned
    .split(/[.·\n]+/)
    .map((chunk) => chunk.trim())
    .filter(Boolean);
  const uniqueChunks = chunks.filter((chunk, index) => chunks.findIndex((item) => item.toLowerCase() === chunk.toLowerCase()) === index);
  return (uniqueChunks.length ? uniqueChunks.join(" · ") : cleaned).slice(0, 800);
}

function storedArray<T>(storage: Storage, key: string): T[] {
  try {
    const parsed: unknown = JSON.parse(storage.getItem(key) ?? "[]");
    return Array.isArray(parsed) ? parsed as T[] : [];
  } catch {
    storage.removeItem(key);
    return [];
  }
}
export default function TestlaufPage() {
  const planSectionRef = useRef<HTMLElement>(null);
  const [entries, setEntries] = useState<Array<[string, string]>>([]);
  const [selected, setSelected] = useState(0);
  const [feedbackRating, setFeedbackRating] = useState<FeedbackRating | null>(null);
  const [feedbackReason, setFeedbackReason] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [feedbackCount, setFeedbackCount] = useState(0);
  const [reviewQueueCount, setReviewQueueCount] = useState(0);
  const [learningCount, setLearningCount] = useState(0);
  const [selectedRoom, setSelectedRoom] = useState<SelectedRoom | null>(null);
  const [swapSource, setSwapSource] = useState<SelectedRoom | null>(null);
  const [editedVariants, setEditedVariants] = useState<Record<string, PlanVariant>>({});
  const [savedPlanCount, setSavedPlanCount] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const [generation, setGeneration] = useState<WorkbenchGeneration | null>(null);
  const [generationError, setGenerationError] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const raw = window.sessionStorage.getItem("born2thrill-test-brief");
      if (raw) setEntries(storedArray<[string, string]>(window.sessionStorage, "born2thrill-test-brief"));
      const feedbackRaw = window.localStorage.getItem("born2thrill-test-feedback");
      if (feedbackRaw) setFeedbackCount(storedArray<TestlaufFeedback>(window.localStorage, "born2thrill-test-feedback").length);
      const learningRaw = window.localStorage.getItem("born2thrill-learning-corrections");
      if (learningRaw) setLearningCount(storedArray<LearningCorrection>(window.localStorage, "born2thrill-learning-corrections").length);
      const savedPlansRaw = window.localStorage.getItem("born2thrill-floorplan-workbench");
      if (savedPlansRaw) setSavedPlanCount(storedArray<SavedWorkbenchPlan>(window.localStorage, "born2thrill-floorplan-workbench").length);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/floorplan-workbench/reviews", {
      cache: "no-store",
      signal: controller.signal,
    })
      .then(async (response) => {
        const payload = await response.json() as ReviewQueueResponse;
        if (!response.ok) throw new Error(payload.error || "Freigabe-Queue nicht erreichbar.");
        return payload;
      })
      .then((payload) => setReviewQueueCount(payload.count))
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/floorplan-workbench/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entries }),
      signal: controller.signal,
    })
      .then(async (response) => {
        const payload = await response.json() as WorkbenchGeneration & { error?: string };
        if (!response.ok) throw new Error(payload.error || "Der lokale Grundriss-Generator ist nicht erreichbar.");
        return payload;
      })
      .then((payload) => {
        setGenerationError("");
        setGeneration({ brief: payload.brief, variants: payload.variants });
        setSelected(0);
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setGenerationError(error instanceof Error ? error.message : "Der lokale Grundriss-Generator ist nicht erreichbar.");
      });
    return () => controller.abort();
  }, [entries]);

  const brief = generation?.brief;
  const variants = generation?.variants ?? [];
  const baseVariant = variants[Math.min(selected, Math.max(0, variants.length - 1))];

  if (!brief || !baseVariant) {
    return (
      <main className="min-h-screen bg-stone-100 px-6 py-16 text-stone-900">
        <section className="mx-auto max-w-3xl rounded-3xl bg-white p-8 shadow-sm">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-800">Lokaler Grundriss-Arbeitsplatz</p>
          <h1 className="mt-3 text-3xl font-semibold">
            {generationError ? "Arbeitsplatz nicht aktiviert" : "Grundrisse werden geladen …"}
          </h1>
          <p className="mt-4 leading-7 text-stone-600">
            {generationError || "Die annotierten Referenzen werden ausschließlich serverseitig geladen."}
          </p>
          <Link href="/" className="mt-8 inline-flex rounded-full border border-stone-300 px-5 py-3 text-sm font-semibold">
            Zur Startseite
          </Link>
        </section>
      </main>
    );
  }

  const variantKey = `${brief.generationAttempt}:${selected}:${baseVariant.id}:${baseVariant.metrics.referenceLayoutId}`;
  const variant: PlanVariant = editedVariants[variantKey] ?? baseVariant;
  const hasLocalEdits = Boolean(editedVariants[variantKey]);

  const selectRoom = (selection: SelectedRoom) => {
    setSelectedRoom(selection);
    if (swapSource && swapSource.floor !== selection.floor) {
      setFeedbackStatus("Räume können nur innerhalb desselben Geschosses getauscht werden.");
    }
  };

  const startRoomSwap = () => {
    if (!selectedRoom) {
      setFeedbackStatus("Bitte zuerst den Raum anklicken, der getauscht werden soll.");
      return;
    }
    setSwapSource(selectedRoom);
    setFeedbackStatus(`${selectedRoom.room.name} ist vorgemerkt. Jetzt den zweiten Raum im selben Geschoss anklicken.`);
  };

  const completeRoomSwap = () => {
    if (!swapSource || !selectedRoom) {
      setFeedbackStatus("Bitte zuerst zwei Räume für den Tausch auswählen.");
      return;
    }
    if (swapSource.floor !== selectedRoom.floor) {
      setFeedbackStatus("Räume können nur innerhalb desselben Geschosses getauscht werden.");
      return;
    }
    try {
      const edited = swapRoomPlacements(
        variant,
        selectedRoom.floor,
        swapSource.room.id,
        selectedRoom.room.id,
      );
      setEditedVariants((current) => ({ ...current, [variantKey]: edited }));
      setFeedbackStatus(`${swapSource.room.name} und ${selectedRoom.room.name} wurden im Arbeitsgrundriss getauscht.`);
      setSwapSource(null);
      setSelectedRoom(null);
    } catch (error) {
      setFeedbackStatus(error instanceof Error ? error.message : "Der Raumtausch ist fehlgeschlagen.");
    }
  };

  const resetWorkbenchVariant = () => {
    setEditedVariants((current) => {
      const next = { ...current };
      delete next[variantKey];
      return next;
    });
    setSwapSource(null);
    setSelectedRoom(null);
    setFeedbackStatus("Die Arbeitskopie wurde auf die annotierte Referenz zurückgesetzt.");
  };

  const saveWorkbenchVariant = () => {
    const stored = storedArray<SavedWorkbenchPlan>(window.localStorage, "born2thrill-floorplan-workbench");
    const saved: SavedWorkbenchPlan = {
      id: `${Date.now()}-${variant.id}`,
      savedAt: new Date().toISOString(),
      reviewStatus: "generated_candidate",
      trainingEligible: false,
      brief,
      variant,
    };
    const next = [saved, ...stored].slice(0, 200);
    window.localStorage.setItem("born2thrill-floorplan-workbench", JSON.stringify(next));
    setSavedPlanCount(next.length);
    setFeedbackStatus(`Arbeitsgrundriss gespeichert. Referenz: ${variant.metrics.referenceLayoutId}.`);
  };

  const downloadWorkbenchVariant = () => {
    const payload = JSON.stringify({
      schema: "born2thrill-floorplan-workbench-v1",
      saved_at: new Date().toISOString(),
      review_status: "generated_candidate",
      training_eligible: false,
      brief,
      variant,
    }, null, 2);
    const url = URL.createObjectURL(new Blob([payload], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${brief.projectName || "grundriss"}-${variant.metrics.referenceLayoutId || variant.id}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    setFeedbackStatus("Arbeitsgrundriss als JSON heruntergeladen.");
  };

  const saveFeedback = async () => {
    const reason = cleanFeedbackReason(feedbackReason);
    const effectiveRating = feedbackRating ?? (reason ? "down" : null);
    if (!effectiveRating) {
      setFeedbackStatus("Bitte Daumen wählen oder Kritiktext eingeben.");
      return false;
    }

    const raw = window.localStorage.getItem("born2thrill-test-feedback");
    const existing = raw ? storedArray<TestlaufFeedback>(window.localStorage, "born2thrill-test-feedback") : [];
    const item: TestlaufFeedback = {
      id: `${Date.now()}-${variant.id}`,
      createdAt: new Date().toISOString(),
      rating: effectiveRating,
      reason,
      variantId: variant.id,
      variantName: variant.name,
      score: variant.score,
      brief,
      metrics: variant.metrics,
      failedChecks: variant.checks.filter((check) => !check.passed).map((check) => check.label),
    };

    window.localStorage.setItem("born2thrill-test-feedback", JSON.stringify([item, ...existing].slice(0, 100)));
    let queuedDurably = false;
    try {
      const response = await fetch("/api/floorplan-workbench/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          schema: "born2thrill-floorplan-review-v1",
          review_status: effectiveRating === "up" ? "approved_for_next_stage" : "rejected",
          reason,
          brief,
          variant,
        }),
      });
      const payload = await response.json() as ReviewQueueResponse;
      if (!response.ok) throw new Error(payload.error || "Freigabe konnte nicht dauerhaft gespeichert werden.");
      setReviewQueueCount(payload.count);
      queuedDurably = true;
    } catch {
      // Browser storage remains the local fallback if the file queue is unavailable.
    }
    setFeedbackCount(existing.length + 1);
    setFeedbackReason("");
    setFeedbackStatus(queuedDurably
      ? `${feedbackLabel(effectiveRating)} dauerhaft in der lokalen Freigabe-Queue gespeichert.`
      : `${feedbackLabel(effectiveRating)} im Browser gespeichert; die Datei-Queue ist nicht erreichbar.`);
    return true;
  };

  const saveFeedbackAndTryNext = async () => {
    const rating = feedbackRating;
    const reason = cleanFeedbackReason(feedbackReason);
    const saved = await saveFeedback();
    if (!saved) return;

    if (rating === "down" || reason) {
      const nextAttempt = brief.generationAttempt + 1;
      const critiqueNotes = reason || brief.critiqueNotes;
      const nextEntries = upsertEntry(
        upsertEntry(entries, "generationAttempt", String(nextAttempt)),
        "critiqueNotes",
        critiqueNotes,
      );
      window.sessionStorage.setItem("born2thrill-test-brief", JSON.stringify(nextEntries));
      setEntries(nextEntries);
      setSelected(0);
      setFeedbackStatus(`Kritik gespeichert. Neuer Lauf ${nextAttempt + 1} wurde daraus generiert.`);
      window.setTimeout(() => planSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } else {
      setSelected((current) => (current + 1) % variants.length);
      window.setTimeout(() => planSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    }

    setFeedbackRating(null);
  };

  const correctionSentence = (action: LearningCorrection["action"], roomName: string) => {
    if (action === "room_to_circulation") return `${roomName} ist kein eigenes Zimmer, sondern ein Eingangsbereich bzw. eine offene Zirkulationsfläche.`;
    if (action === "increase_room_area") return `${roomName} ist zu klein und soll bei der nächsten Variante mehr Fläche bekommen.`;
    if (action === "decrease_room_area") return `${roomName} ist zu groß und soll bei der nächsten Variante kompakter werden.`;
    return `Tür oder Fenster bei ${roomName} ist falsch gesetzt und muss planerisch geprüft werden.`;
  };

  const structuredConstraintsFor = (action: LearningCorrection["action"], room: PlannedRoom) => {
    if (action === "room_to_circulation") return [
      { type: "room_to_circulation", target: room.name },
      { type: "remove_room_cell_behavior", target: room.name },
    ];
    if (action === "increase_room_area") return [{ type: "increase_room_area", target: room.name, area_m2: room.area }];
    if (action === "decrease_room_area") return [{ type: "decrease_room_area", target: room.name, area_m2: room.area }];
    return [{ type: "door_window_issue", target: room.name }];
  };

  const saveLearningCorrection = (action: LearningCorrection["action"], regenerate: boolean) => {
    if (!selectedRoom) {
      setFeedbackStatus("Bitte zuerst einen Raum im Grundriss anklicken.");
      return;
    }

    const reason = cleanFeedbackReason(feedbackReason);
    const sentence = correctionSentence(action, selectedRoom.room.name);
    const correction: LearningCorrection = {
      id: `${Date.now()}-${selectedRoom.room.id}`,
      createdAt: new Date().toISOString(),
      variantId: variant.id,
      variantName: variant.name,
      floor: selectedRoom.floor,
      floorName: selectedRoom.floorName,
      targetRoomId: selectedRoom.room.id,
      targetRoomName: selectedRoom.room.name,
      action,
      reason,
      before: {
        name: selectedRoom.room.name,
        kind: selectedRoom.room.kind,
        area: selectedRoom.room.area,
        x: Math.round(selectedRoom.room.x),
        y: Math.round(selectedRoom.room.y),
        width: Math.round(selectedRoom.room.width),
        height: Math.round(selectedRoom.room.height),
      },
      structuredConstraints: structuredConstraintsFor(action, selectedRoom.room),
    };

    const raw = window.localStorage.getItem("born2thrill-learning-corrections");
    const existing = raw ? storedArray<LearningCorrection>(window.localStorage, "born2thrill-learning-corrections") : [];
    window.localStorage.setItem("born2thrill-learning-corrections", JSON.stringify([correction, ...existing].slice(0, 200)));
    setLearningCount(existing.length + 1);

    const critiqueNotes = cleanFeedbackReason([sentence, reason].filter(Boolean).join(" "));
    setFeedbackReason("");
    setFeedbackStatus(`Lernkorrektur gespeichert: ${sentence}`);

    if (regenerate) {
      const nextAttempt = brief.generationAttempt + 1;
      const nextEntries = upsertEntry(
        upsertEntry(entries, "generationAttempt", String(nextAttempt)),
        "critiqueNotes",
        critiqueNotes,
      );
      window.sessionStorage.setItem("born2thrill-test-brief", JSON.stringify(nextEntries));
      setEntries(nextEntries);
      setSelected(0);
      setSelectedRoom(null);
      window.setTimeout(() => planSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    }
  };

  const startDictation = () => {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!Recognition) {
      setFeedbackStatus("Diktat wird von diesem Browser leider nicht unterstützt. Chrome oder Safari funktionieren meistens.");
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "de-DE";
    recognition.interimResults = false;
    recognition.continuous = false;
    setIsListening(true);
    setFeedbackStatus("Ich höre zu … sprechen Sie Ihre Kritikpunkte.");

    recognition.onresult = (event) => {
      let transcript = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        transcript += event.results[index][0].transcript;
      }
      if (transcript.trim()) {
        setFeedbackReason((current) => `${current}${current ? " " : ""}${transcript.trim()}`);
      }
    };

    recognition.onerror = () => {
      setIsListening(false);
      setFeedbackStatus("Diktat konnte nicht gestartet werden. Bitte Mikrofonberechtigung prüfen.");
    };
    recognition.onend = () => {
      setIsListening(false);
      setFeedbackStatus("Diktat beendet. Sie können jetzt neu generieren.");
    };
    recognition.start();
  };

  return (
    <main className="min-h-screen bg-[#f3f1eb] px-5 py-8 text-stone-900 sm:py-12">
      <div className="mx-auto max-w-7xl">
        <header className="flex items-center justify-between"><Link href="/" className="text-sm font-bold tracking-[0.18em] uppercase">Born2Thrill</Link><span className="text-xs text-amber-700">Generator MVP · Testmodus</span></header>
        <div className="mt-10 rounded-[2rem] bg-[#18392f] p-8 text-white sm:p-12">
          <p className="text-xs font-semibold tracking-[0.2em] text-emerald-200 uppercase">Generierung abgeschlossen</p>
          <div className="mt-4 flex flex-wrap items-end justify-between gap-5"><div><h1 className="text-4xl font-medium tracking-tight">{brief.projectName}</h1><p className="mt-3 text-emerald-100/70">{brief.area} m² · {brief.floors} Geschosse · {brief.bedrooms} Schlafzimmer</p></div><div className="rounded-full bg-emerald-200 px-5 py-2 text-sm font-bold text-emerald-950">Planungswert {variant.score}/100</div></div>
        </div>

        <div className="mt-8 flex gap-3 overflow-x-auto pb-2">
          {variants.map((item, index) => <button key={item.id} onClick={() => { setSelected(index); setSelectedRoom(null); setSwapSource(null); }} className={`whitespace-nowrap rounded-full px-5 py-3 text-sm font-semibold ${selected === index ? "bg-[#18392f] text-white" : "bg-white text-stone-600"}`}>{item.name}</button>)}
          <button type="button" onClick={() => { setSelected((current) => (current + 1) % variants.length); setSelectedRoom(null); setSwapSource(null); }} className="whitespace-nowrap rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-semibold text-stone-700">
            Andere Variante anzeigen
          </button>
        </div>

        <section ref={planSectionRef} className="mt-6 rounded-[2rem] bg-white p-6 shadow-[0_20px_60px_rgba(41,37,36,.08)] sm:p-10">
          <div className="flex flex-wrap items-start justify-between gap-5"><div><h2 className="text-3xl font-medium">{variant.name}</h2><p className="mt-3 max-w-2xl leading-7 text-stone-600">{variant.description}</p><div className="mt-5 inline-flex rounded-full bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-900">Referenz: {variant.metrics.referenceProfile}</div></div><div className="text-right text-sm text-stone-500"><p>{variant.metrics.footprintWidthM} × {variant.metrics.footprintDepthM} m</p><p>{variant.metrics.plannedAreaM2} m² Wohnfläche</p>{variant.metrics.upperFloorAreaM2 > 0 && <p>EG ca. {variant.metrics.groundFloorAreaM2} m² · OG ca. {variant.metrics.upperFloorAreaM2} m²</p>}</div></div>
          {brief.generationAttempt > 0 && <div className="mt-5 rounded-2xl bg-amber-50 p-4 text-sm leading-6 text-amber-900">Neuer Generierungslauf {brief.generationAttempt + 1}. Berücksichtigt: {compactCritique(brief.critiqueNotes)}</div>}
          {hasLocalEdits && <div className="mt-5 rounded-2xl bg-blue-50 p-4 text-sm leading-6 text-blue-900">Arbeitskopie aktiv: Die annotierte Referenz bleibt unverändert. Speichern oder herunterladen sichert diese Variante separat.</div>}
          {hasLocalEdits && <div className="mt-3 rounded-2xl bg-amber-100 p-4 text-sm font-semibold leading-6 text-amber-950">Ungeprüfter Kandidat: Türen, Fenster, Erschließung und Flächen müssen nach dem Raumtausch fachlich geprüft werden. Dieser Entwurf ist nicht trainingsfähig.</div>}
          <div className="mt-8 grid gap-8 xl:grid-cols-2">{variant.floors.map((floor) => <article key={floor.floor}><h3 className="mb-3 text-sm font-semibold">{floor.name}</h3><FloorSvg plan={floor} selectedRoomId={selectedRoom?.room.id} onSelectRoom={selectRoom} /></article>)}</div>
        </section>

        <section className="mt-8 rounded-[2rem] bg-[#18392f] p-6 text-white shadow-[0_20px_60px_rgba(41,37,36,.12)] sm:p-10">
          <div className="grid gap-8 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-emerald-200 uppercase">Montags-Demo</p>
              <h2 className="mt-3 text-2xl font-medium">Grundriss-Arbeitsplatz</h2>
              <p className="mt-3 leading-7 text-emerald-50/80">
                Tausche zwei Raumpositionen direkt, ohne die annotierte Originalreferenz zu verändern. Das Ergebnis kann im Browser gespeichert oder als JSON für die nächste Bearbeitung heruntergeladen werden.
              </p>
              <p className="mt-4 text-xs text-emerald-100/60">Gespeicherte Arbeitsgrundrisse in diesem Browser: {savedPlanCount}</p>
            </div>
            <div className="rounded-3xl bg-white/10 p-5">
              <p className="text-sm font-semibold">
                {swapSource
                  ? `Tauschquelle: ${swapSource.room.name} · ${swapSource.floorName}`
                  : selectedRoom
                    ? `Ausgewählt: ${selectedRoom.room.name} · ${selectedRoom.floorName}`
                    : "1. Einen Raum im Grundriss anklicken"}
              </p>
              <p className="mt-2 text-sm leading-6 text-emerald-50/70">
                {swapSource
                  ? "2. Den Zielraum im selben Geschoss anklicken und den Tausch bestätigen."
                  : "Danach als Tauschquelle merken, den zweiten Raum anklicken und bestätigen."}
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                {!swapSource ? (
                  <button type="button" onClick={startRoomSwap} className="rounded-full bg-emerald-200 px-5 py-3 text-sm font-bold text-emerald-950">
                    Ausgewählten Raum merken
                  </button>
                ) : (
                  <>
                    <button type="button" onClick={completeRoomSwap} className="rounded-full bg-emerald-200 px-5 py-3 text-sm font-bold text-emerald-950">
                      Räume jetzt tauschen
                    </button>
                    <button type="button" onClick={() => setSwapSource(null)} className="rounded-full border border-white/30 px-5 py-3 text-sm font-semibold">
                      Tausch abbrechen
                    </button>
                  </>
                )}
                <button type="button" onClick={saveWorkbenchVariant} className="rounded-full border border-white/30 px-5 py-3 text-sm font-semibold">
                  Arbeitsgrundriss speichern
                </button>
                <button type="button" onClick={downloadWorkbenchVariant} className="rounded-full border border-white/30 px-5 py-3 text-sm font-semibold">
                  JSON herunterladen
                </button>
                {hasLocalEdits && <button type="button" onClick={resetWorkbenchVariant} className="rounded-full border border-red-200/50 px-5 py-3 text-sm font-semibold text-red-100">
                  Änderungen zurücksetzen
                </button>}
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-[2rem] bg-white p-6 shadow-[0_20px_60px_rgba(41,37,36,.08)] sm:p-10">
          <div className="grid gap-8 lg:grid-cols-[.85fr_1.15fr]">
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Korrektur erfassen</p>
              <h2 className="mt-3 text-2xl font-medium">Click-to-teach</h2>
              <p className="mt-3 leading-7 text-stone-600">
                Klicke einen Raum im Grundriss an, wähle die Korrektur und diktiere kurz warum. Das speichern wir als strukturiertes Lernbeispiel.
              </p>
              <p className="mt-4 text-xs text-stone-500">Gespeicherte Lernkorrekturen in diesem Browser: {learningCount}</p>
            </div>
            <div className="rounded-3xl border border-stone-200 bg-stone-50 p-5">
              {selectedRoom ? (
                <>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold tracking-[0.18em] text-stone-500 uppercase">Ausgewählt</p>
                      <h3 className="mt-1 text-xl font-semibold">{selectedRoom.room.name}</h3>
                      <p className="mt-1 text-sm text-stone-500">{selectedRoom.floorName} · {selectedRoom.room.kind} · ca. {selectedRoom.room.area} m²</p>
                    </div>
                    <button type="button" onClick={() => setSelectedRoom(null)} className="rounded-full border border-stone-300 bg-white px-4 py-2 text-xs font-semibold text-stone-600">Auswahl löschen</button>
                  </div>
                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    <button type="button" onClick={() => saveLearningCorrection("room_to_circulation", true)} className="rounded-2xl bg-[#18392f] px-4 py-3 text-left text-sm font-semibold text-white">
                      Als Eingangsbereich / Flur lernen & neu generieren
                    </button>
                    <button type="button" onClick={() => saveLearningCorrection("increase_room_area", true)} className="rounded-2xl border border-stone-300 bg-white px-4 py-3 text-left text-sm font-semibold text-stone-700">
                      Raum größer lernen & neu generieren
                    </button>
                    <button type="button" onClick={() => saveLearningCorrection("decrease_room_area", true)} className="rounded-2xl border border-stone-300 bg-white px-4 py-3 text-left text-sm font-semibold text-stone-700">
                      Raum kleiner lernen & neu generieren
                    </button>
                    <button type="button" onClick={() => saveLearningCorrection("door_window_issue", false)} className="rounded-2xl border border-stone-300 bg-white px-4 py-3 text-left text-sm font-semibold text-stone-700">
                      Tür/Fenster-Problem nur speichern
                    </button>
                  </div>
                  <p className="mt-4 text-xs leading-5 text-stone-500">
                    Tipp: Nutze unten das Diktatfeld für die Begründung, z. B. „Diele ist kein eigenes Zimmer, sondern ein offener Eingangsbereich.“
                  </p>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-stone-300 bg-white p-6 text-sm leading-6 text-stone-500">
                  Noch nichts ausgewählt. Klicke direkt im Grundriss auf einen Raum.
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-8 lg:grid-cols-[1.35fr_.65fr]">
          <div className="rounded-[2rem] bg-white p-6 sm:p-10"><p className="mb-5 text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Konzeptvisualisierung</p><HouseRendering brief={brief} /><p className="mt-4 text-xs leading-5 text-stone-500">Stilistische Konzeptansicht. Kubatur, Öffnungen und Dachform werden in späteren Stufen aus dem freigegebenen Grundrissmodell abgeleitet.</p></div>
          <div className="rounded-[2rem] bg-white p-6 sm:p-8"><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Regelprüfung</p><div className="mt-6 space-y-4">{variant.checks.map((check) => <div key={check.label} className="flex gap-3 text-sm leading-6"><span className={`mt-1 flex size-5 shrink-0 items-center justify-center rounded-full text-xs ${check.passed ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-700"}`}>{check.passed ? "✓" : "!"}</span><span>{check.label}</span></div>)}</div>{variant.floors[0]?.stair && <div className="mt-7 rounded-2xl bg-stone-100 p-4 text-xs leading-5 text-stone-600"><p className="font-semibold text-stone-800">Treppengeometrie · Konzeptziel</p><p className="mt-2">Geschosshöhe {variant.floors[0].stair.floorToFloorHeightM.toFixed(2)} m · {variant.floors[0].stair.risers} Steigungen · Auftritt {variant.floors[0].stair.treadDepthCm} cm · Laufbreite {variant.floors[0].stair.usableFlightWidthM.toFixed(2)} m · Podest {variant.floors[0].stair.landingDepthM.toFixed(2)} m</p></div>}<div className="mt-8 border-t border-stone-200 pt-6 text-xs leading-5 text-stone-500">Konservative Konzeptziele für frühe Varianten. Die Treppe muss in der Fachplanung nach DIN 18065, Landesbauordnung, Statik und Brandschutz geprüft werden; dies ist keine Genehmigungs- oder Ausführungsplanung.</div></div>
        </section>

        <section className="mt-8 rounded-[2rem] bg-white p-6 shadow-[0_20px_60px_rgba(41,37,36,.08)] sm:p-10">
          <div className="grid gap-8 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Learning by doing</p>
              <h2 className="mt-3 text-2xl font-medium">Ist dieser Grundriss brauchbar?</h2>
              <p className="mt-3 leading-7 text-stone-600">
                Bewerte jede Variante kurz. Gute Varianten werden später verstärkt, schlechte Varianten geben uns konkrete Regeln, was der Generator vermeiden soll.
              </p>
              <p className="mt-4 text-xs text-stone-500">Gespeicherte Testbewertungen in diesem Browser: {feedbackCount}</p>
              <p className="mt-2 text-xs font-semibold text-emerald-800">Dauerhafte lokale Freigaben: {reviewQueueCount}</p>
            </div>
            <div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => setFeedbackRating("up")}
                  className={`rounded-full px-5 py-3 text-sm font-bold ${feedbackRating === "up" ? "bg-emerald-700 text-white" : "bg-emerald-50 text-emerald-900"}`}
                >
                  👍 Gut / weiter so
                </button>
                <button
                  type="button"
                  onClick={() => setFeedbackRating("down")}
                  className={`rounded-full px-5 py-3 text-sm font-bold ${feedbackRating === "down" ? "bg-red-700 text-white" : "bg-red-50 text-red-900"}`}
                >
                  👎 Nicht gut
                </button>
              </div>
              <label className="mt-5 block text-sm font-semibold text-stone-700" htmlFor="feedback-reason">
                Warum? Was soll besser werden?
              </label>
              <button type="button" onClick={startDictation} className={`mt-3 rounded-full px-5 py-3 text-sm font-bold ${isListening ? "bg-red-700 text-white" : "bg-stone-900 text-white"}`}>
                {isListening ? "🎙️ Höre zu …" : "🎙️ Kritik diktieren"}
              </button>
              <textarea
                id="feedback-reason"
                value={feedbackReason}
                onChange={(event) => setFeedbackReason(event.target.value)}
                rows={4}
                placeholder="z. B. Treppe falsch platziert, Küche zu klein, Flur zu groß, Bad nicht am Installationskern, Fenster fehlen..."
                className="mt-2 w-full rounded-2xl border border-stone-200 bg-stone-50 p-4 text-sm outline-none transition focus:border-emerald-700 focus:bg-white"
              />
              {feedbackStatus && <p className="mt-3 text-sm text-emerald-800">{feedbackStatus}</p>}
              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" onClick={saveFeedback} className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white">
                  Feedback speichern
                </button>
                <button type="button" onClick={saveFeedbackAndTryNext} className="rounded-full border border-stone-300 bg-white px-6 py-3 text-sm font-semibold text-stone-700">
                  Kritik speichern & neu generieren
                </button>
              </div>
            </div>
          </div>
        </section>

        <div className="mt-8 flex flex-wrap gap-3"><Link href="/questionnaire?test=1" className="rounded-full border border-stone-300 bg-white px-6 py-3 text-sm font-semibold">Angaben ändern</Link><button onClick={() => window.print()} className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white">Konzept drucken</button></div>
      </div>
      <div className="fixed inset-x-3 bottom-3 z-40 rounded-3xl border border-stone-200 bg-white/95 p-3 shadow-[0_20px_70px_rgba(41,37,36,.22)] backdrop-blur md:left-auto md:right-5 md:w-[560px]">
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <button type="button" onClick={startDictation} className={`shrink-0 rounded-full px-4 py-3 text-sm font-bold ${isListening ? "bg-red-700 text-white" : "bg-stone-900 text-white"}`}>
            {isListening ? "🎙️ Höre zu …" : "🎙️ Diktieren"}
          </button>
          <textarea
            aria-label="Kritikpunkte diktieren oder eingeben"
            value={feedbackReason}
            onChange={(event) => setFeedbackReason(event.target.value)}
            rows={1}
            placeholder="Kritik sprechen oder tippen …"
            className="min-h-12 flex-1 resize-none rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm outline-none focus:border-emerald-700"
          />
          <button type="button" onClick={saveFeedbackAndTryNext} className="shrink-0 rounded-full bg-[#18392f] px-4 py-3 text-sm font-bold text-white">
            Neu generieren
          </button>
        </div>
      </div>
    </main>
  );
}
