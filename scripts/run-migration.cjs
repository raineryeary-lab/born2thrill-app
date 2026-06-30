const { readFileSync } = require("fs");
const { resolve } = require("path");
const pg = require("pg");

const Client = pg.Client;

async function main() {
  const databaseUrl = process.env.DATABASE_URL;
  const migrationPath =
    process.argv[2] || "railway/migrations/001_initial_schema.sql";

  if (!databaseUrl) {
    console.error("Missing DATABASE_URL.");
    console.error(
      'Usage: DATABASE_URL="postgresql://..." node scripts/run-migration.cjs',
    );
    process.exit(1);
  }

  const resolvedMigrationPath = resolve(process.cwd(), migrationPath);
  const sql = readFileSync(resolvedMigrationPath, "utf8");

  const client = new Client({
    connectionString: databaseUrl,
    ssl: databaseUrl.indexOf("rlwy.net") >= 0
      ? { rejectUnauthorized: false }
      : undefined,
  });

  try {
    console.log("Running migration: " + resolvedMigrationPath);
    await client.connect();
    await client.query(sql);
    console.log("Migration completed successfully.");
  } finally {
    await client.end();
  }
}

main().catch(function (error) {
  console.error(error);
  process.exit(1);
});
