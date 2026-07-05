import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import pg from "pg";

const { Client } = pg;

const databaseUrl = process.env.DATABASE_URL;
const migrationPath = process.argv[2] ?? "railway/migrations/001_initial_schema.sql";

if (!databaseUrl) {
  console.error("Missing DATABASE_URL.");
  console.error(
    'Usage: DATABASE_URL="postgresql://..." node scripts/run-migration.mjs',
  );
  process.exit(1);
}

const resolvedMigrationPath = resolve(process.cwd(), migrationPath);
const sql = await readFile(resolvedMigrationPath, "utf8");

const client = new Client({
  connectionString: databaseUrl,
  ssl: databaseUrl.includes("rlwy.net")
    ? { rejectUnauthorized: false }
    : undefined,
});

try {
  console.log(`Running migration: ${resolvedMigrationPath}`);
  await client.connect();
  await client.query(sql);
  console.log("Migration completed successfully.");
} finally {
  await client.end();
}
