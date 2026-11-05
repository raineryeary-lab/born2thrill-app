// UI-only furniture context; never an approved correction.
export function furnitureViewDocument(reference, geometry) {
  if (geometry?.project_id !== reference || !geometry?.floors?.length) throw new Error('Live furniture geometry missing or wrong house.');
  return {
    schema: 'furniture-view-only-v1', source_reference_id: reference,
    status: 'draft', usage_scope: 'internal_reference_only', revision: 0,
    floors: geometry.floors.map((floor, index) => ({
      id: `floor-${index}`, name: floor.floor_level, geometry_identity: floor.geometry_identity,
      rooms: (floor.rooms || []).map(room => ({...room, polygon: room.polygon_mm})),
      walls: [], openings: [],
    })),
  };
}
