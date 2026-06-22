export default function SupabaseTestPage() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  return (
    <main style={{ padding: 40, fontFamily: "sans-serif" }}>
      <h1>Supabase Test</h1>
      <p>URL configured: {url ? "yes" : "no"}</p>
      <p>Anon key configured: {anonKey ? "yes" : "no"}</p>
    </main>
  );
}