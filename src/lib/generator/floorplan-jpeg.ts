import sharp from "sharp";
import type { PlanVariant } from "./floorplan";
import {
  assertSafeGeneratedSvg,
  renderFloorplanSvg,
} from "./floorplan-svg.mjs";

const JPEG_WIDTH = 1800;
const JPEG_QUALITY = 90;
const MAX_JPEG_BYTES = 3 * 1024 * 1024;

export const FLOORPLAN_JPEG_GENERATOR_VERSION = "annotated-reference-jpeg-v1";

export async function renderFloorplanJpeg(
  variant: PlanVariant,
  options: {
    requestId?: string;
    mandatoryLabel?: string;
  } = {},
) {
  const svg = assertSafeGeneratedSvg(renderFloorplanSvg(variant, options));
  const bytes = await sharp(Buffer.from(svg, "utf8"), {
    density: 192,
    limitInputPixels: 32_000_000,
  })
    .flatten({ background: "#ffffff" })
    .resize({
      width: JPEG_WIDTH,
      withoutEnlargement: false,
      fit: "inside",
    })
    .jpeg({
      quality: JPEG_QUALITY,
      chromaSubsampling: "4:4:4",
      progressive: true,
      mozjpeg: true,
    })
    .toBuffer();

  if (
    bytes.length < 100 ||
    bytes.length > MAX_JPEG_BYTES ||
    bytes[0] !== 0xff ||
    bytes[1] !== 0xd8 ||
    bytes[2] !== 0xff
  ) {
    throw new Error("Der Grundriss konnte nicht als sicheres JPEG gerendert werden.");
  }

  return bytes;
}
