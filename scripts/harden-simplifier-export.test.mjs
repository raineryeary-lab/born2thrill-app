import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createHash } from "node:crypto";
import { hardenSimplifierExport } from "./harden-simplifier-export.mjs";

const hash = (text) => createHash("sha256").update(text).digest("hex");
test("hardened export promotes passed plans for internal use and preserves only unchanged explicit commercial approval", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "harden-export-"));
  const out = path.join(root, "out"); const projects = path.join(root, "projects");
  await mkdir(out); await mkdir(projects);
  const ids = ["new", "approved", "changed"];
  const contents = { new: "new", approved: "approved", changed: "changed-now" };
  for (const id of ids) { await mkdir(path.join(projects,id)); await writeFile(path.join(projects,id,"annotations.json"), contents[id]); }
  await writeFile(path.join(out,"dataset.json"), JSON.stringify({ projects: ids.map((id)=>({project_id:id,package_status:"reviewed",floors:[{floor_level:"groundfloor",rooms:[{polygon:[[0,0],[1,0],[1,1]]}],elements:[]}]})) }));
  await writeFile(path.join(out,"batch-audit.json"), JSON.stringify({ projects: ids.map((id)=>({project_id:id,included:true,quality_passed:true})) }));
  const prior = { projects: [
    {project_id:"approved",corpus_status:"approved_real",annotation_sha256:hash(contents.approved)},
    {project_id:"changed",corpus_status:"approved_real",annotation_sha256:hash("changed-before")}
  ]};
  const priorPath=path.join(root,"ledger.json"); await writeFile(priorPath,JSON.stringify(prior));
  const result=await hardenSimplifierExport({exportDir:out,projectsDir:projects,priorLedgerPath:priorPath});
  const data=JSON.parse(await readFile(path.join(out,"dataset.json"),"utf8"));
  assert.equal(result.projects,3); assert.equal(result.passed,3); assert.equal(result.commercial,1);
  assert.equal(data.projects.find((p)=>p.project_id==="new").package_status,"training_ready");
  assert.equal(data.projects.find((p)=>p.project_id==="new").usage_scope,"internal_reference_only");
  assert.equal(data.projects.find((p)=>p.project_id==="approved").usage_scope,"commercial_generator");
  assert.equal(data.projects.find((p)=>p.project_id==="changed").usage_scope,"internal_reference_only");
});