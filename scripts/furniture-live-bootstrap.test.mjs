import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { furnitureViewDocument } from '../src/lib/generator/furniture-live-bootstrap.mjs';
test('live furniture view retains exact geometry and floor namespaces without approval', () => {
  const floor = {floor_level:'groundfloor', geometry_identity:'abc', rooms:[{id:'r', polygon_mm:[[0,0],[100,0],[0,100]]}], walls:[], openings:[]};
  const doc = furnitureViewDocument('twostorey_053', {project_id:'twostorey_053', floors:[floor, {...floor, floor_level:'upperfloor'}]});
  assert.deepEqual(doc.floors.map(f=>f.id), ['floor-0','floor-1']);
  assert.deepEqual(doc.floors[0].rooms[0].polygon, floor.rooms[0].polygon_mm);
  assert.equal(doc.floors[0].geometry_identity, 'abc');
  assert.equal(doc.status, 'draft');
  assert.equal(doc.usage_scope, 'internal_reference_only');
  assert.notEqual(doc.schema, 'dmh-floorplan-correction-v2');
});
test('rejects absent or wrong-house geometry', () => {
  assert.throws(()=>furnitureViewDocument('a', {project_id:'b', floors:[{}]}));
  assert.throws(()=>furnitureViewDocument('a', {project_id:'a', floors:[]}));
});
test('furniture embed excludes correction-only consumers and persistence buttons', () => {
  const page = readFileSync(new URL('../src/app/floorplan-workbench/page.tsx', import.meta.url), 'utf8');
  const start = page.indexOf('{!embed && <><section');
  const end = page.indexOf('</>}', start);
  assert.ok(start > 0 && end > start);
  for (const consumer of ['<Massing document=', 'document.rights.source_status', 'action("save_draft")', 'action("approve")', 'action("export")']) {
    assert.ok(page.slice(start, end).includes(consumer), consumer + ' must be excluded in embed');
  }
});
