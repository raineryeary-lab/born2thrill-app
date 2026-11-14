export const dynamic = "force-dynamic";

export function GET() {
  return Response.json({
    status: "ok",
    service: "floorplan-workbench-local",
    bind: "127.0.0.1:3020",
    rights: "internal_reference_only",
    delivery: "blocked",
  }, {
    headers: {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
