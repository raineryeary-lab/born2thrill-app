import React from "react";
import { ImageResponse } from "next/og";
import type { PlanVariant } from "./floorplan";
import {
  assertValidPlanGuidePng,
  planGeometryGuideModel,
} from "./zuhausefinder-visualization.mjs";

const ROOM_COLORS: Record<string, string> = {
  living: "#d9f4e4",
  sleeping: "#eef1f4",
  wet: "#dcecff",
  service: "#fff0bd",
  flex: "#eadff7",
  circulation: "#f1eee7",
};

type PlanGuideRoom = {
  id: string;
  kind: string;
  x: number;
  y: number;
  width: number;
  height: number;
};

type PlanGuideFloor = {
  floor: number;
  rooms: PlanGuideRoom[];
};

type PlanGuideModel = {
  width: number;
  height: number;
  footprint_aspect_ratio: number;
  floors: PlanGuideFloor[];
};

function roomElement(
  room: PlanGuideRoom,
  panelWidth: number,
  panelHeight: number,
) {
  return React.createElement("div", {
    key: room.id,
    style: {
      position: "absolute",
      left: Math.round(room.x * panelWidth),
      top: Math.round(room.y * panelHeight),
      width: Math.max(2, Math.round(room.width * panelWidth)),
      height: Math.max(2, Math.round(room.height * panelHeight)),
      display: "flex",
      backgroundColor: ROOM_COLORS[room.kind] ?? ROOM_COLORS.flex,
      border: "2px solid #776f66",
      boxSizing: "border-box",
    },
  });
}

export async function renderPlanGeometryGuidePng(variant: PlanVariant) {
  const model = planGeometryGuideModel(variant) as PlanGuideModel;
  const floors = model.floors.slice(0, 2);
  if (!floors.length) {
    throw new Error("Der Geometrieleitfaden hat keine Etage.");
  }

  const isMultiFloor = floors.length > 1;
  const panelWidth = isMultiFloor ? 408 : 720;
  const rawPanelHeight = panelWidth / Math.max(0.55, model.footprint_aspect_ratio);
  const panelHeight = Math.round(
    Math.max(isMultiFloor ? 330 : 420, Math.min(isMultiFloor ? 690 : 760, rawPanelHeight)),
  );
  const gap = isMultiFloor ? 64 : 0;
  const totalWidth = panelWidth * floors.length + gap * Math.max(0, floors.length - 1);
  const startX = Math.round((model.width - totalWidth) / 2);
  const startY = Math.round((model.height - panelHeight) / 2);

  const floorElements = floors.map((floor, index) =>
    React.createElement(
      "div",
      {
        key: `floor-${floor.floor}`,
        style: {
          position: "absolute",
          left: startX + index * (panelWidth + gap),
          top: startY,
          width: panelWidth,
          height: panelHeight,
          display: "flex",
          backgroundColor: "#fbfaf7",
          border: "14px solid #201f1c",
          boxSizing: "border-box",
          overflow: "hidden",
        },
      },
      floor.rooms.map((room) => roomElement(room, panelWidth - 28, panelHeight - 28)),
    ),
  );

  const response = new ImageResponse(
    React.createElement(
      "div",
      {
        style: {
          width: "100%",
          height: "100%",
          position: "relative",
          display: "flex",
          backgroundColor: "#f4f2ed",
        },
      },
      floorElements,
    ),
    {
      width: model.width,
      height: model.height,
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": "image/png",
      },
    },
  );
  const bytes = Buffer.from(await response.arrayBuffer());
  return assertValidPlanGuidePng(bytes);
}
