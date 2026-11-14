import { analyzeFacades } from "./facade-analysis.mjs";
import { validateCorrectionDocument } from "./correction-editor.mjs";

const BLENDER_RENDER_VIEWS = new Set(["garden", "street", "east", "west"]);

export function buildBlenderSceneManifest(canonical, options = {}) {
  const renderView = options.renderView || "garden";
  if (!BLENDER_RENDER_VIEWS.has(renderView)) throw new Error(`Unsupported Blender render view: ${renderView}`);
  if (!canonical?.geometry_hash) throw new Error("Canonical geometry hash missing.");
  if (options.validate !== false) {
    const validation = validateCorrectionDocument(canonical);
    if (!validation.valid) throw new Error(`Hard-invalid canonical geometry cannot render: ${validation.errors.join(", ")}`);
    if (validation.geometry_hash !== canonical.geometry_hash) throw new Error("Canonical geometry hash mismatch.");
  }

  const facadeAnalysis = analyzeFacades(canonical, {
    preferredView: renderView,
    cameraAngleDeg: Number(options.cameraAngleDeg ?? 35),
  });
  const height = Number(canonical.building?.floor_height_mm || 2800);
  const floors = (canonical.floors || []).map((floor, index) => ({
    id: floor.id,
    elevation_mm: index * height,
    slab: {
      polygon_mm: floor.footprint,
      thickness_mm: 200,
      base_z_mm: index * height,
    },
    walls: (floor.walls || []).map((wall) => ({
      id: wall.id,
      start_mm: wall.start,
      end_mm: wall.end,
      thickness_mm: wall.thickness,
      wall_type: wall.wall_type || "partition",
      connects: structuredClone(wall.connects || []),
      height_mm: height,
      base_z_mm: index * height,
      length_mm: Math.hypot(wall.end[0] - wall.start[0], wall.end[1] - wall.start[1]),
    })),
    openings: (floor.openings || []).map((opening) => {
      if (!(floor.walls || []).some((wall) => wall.id === opening.wall_id)) throw new Error(`Opening ${opening.id} is not linked to a wall.`);
      return {
        id: opening.id,
        wall_id: opening.wall_id,
        opening_type: opening.opening_type,
        role: opening.role || "standard",
        glazed: opening.glazed === true,
        traversable: opening.traversable === true,
        connects: structuredClone(opening.connects || []),
        position: opening.position,
        width_mm: opening.width,
        height_mm: Number(opening.height_mm ?? (opening.opening_type === "door" ? 2100 : 1350)),
        sill_height_mm: Number(opening.sill_height_mm ?? (opening.opening_type === "door" ? 0 : 900)),
        base_z_mm: index * height,
      };
    }),
  }));

  const footprintWidth = Number(canonical.building?.footprint_width_mm);
  const footprintDepth = Number(canonical.building?.footprint_depth_mm);
  const pitchDeg = Number(canonical.building?.roof_pitch_deg || 35);
  const ridgeAxis = footprintWidth >= footprintDepth ? "x" : "y";

  return {
    schema: "dmh-blender-scene-manifest-v1",
    schema_version: 1,
    source_geometry_hash: canonical.geometry_hash,
    presentation_hash: facadeAnalysis.presentation_hash,
    coordinate_unit: "mm",
    render_view: renderView,
    facade_analysis: facadeAnalysis,
    camera: {
      angle_deg: facadeAnalysis.selection.camera_angle_deg,
      selected_facade_id: facadeAnalysis.selection.selected_facade_id,
      adjacent_facade_id: facadeAnalysis.selection.adjacent_facade_id,
      outward_normal: facadeAnalysis.selection.outward_normal,
      adjacent_normal: facadeAnalysis.selection.adjacent_normal,
      focal_length_mm: 40,
    },
    wordpress_eligible: false,
    external_delivery: "blocked",
    floor_height_mm: height,
    floors,
    shared_stair_core: canonical.shared_stair_core ? structuredClone(canonical.shared_stair_core) : null,
    roof: {
      form: canonical.building?.roof_form || "gable",
      representation: "deterministic_gable",
      base_z_mm: floors.length * height,
      footprint_width_mm: footprintWidth,
      footprint_depth_mm: footprintDepth,
      pitch_deg: pitchDeg,
      ridge_axis: ridgeAxis,
      overhang_mm: 300,
      thickness_mm: 200,
    },
  };
}

export function assertManifestMatchesCanonical(manifest, canonical) {
  if (manifest?.source_geometry_hash !== canonical?.geometry_hash) throw new Error("Blender manifest/canonical hash mismatch.");
  return true;
}
