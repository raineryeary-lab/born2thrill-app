# Born2Thrill

Born2Thrill is a web application for collecting residential design requirements
and, later, generating floor-plan concepts and architectural renderings.

## Environment

Copy `.env.example` to `.env.local` and provide the environment-specific
values. Never commit `.env.local`, database passwords, connection strings, or
Supabase elevated keys.

The browser application may access only:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

`DATABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are reserved for trusted
server-side processes.

## Database

Versioned Supabase migrations live in `supabase/migrations`. Every public table
must have Row Level Security enabled before it is exposed through Supabase APIs.

## Floor-plan training data

The local floor-plan generator uses a small internal training schema before any
model training is introduced. Both our own manually annotated Floorplan
Simplifier packages and selected CubiCasa5K samples are normalized into:

- an image path
- room labels with polygons
- optional room area values or area ratios
- door, window and stair elements

Adapters live in `src/lib/training`:

- `import_our_simplifier_package(projectPath)` reads local packages with
  `original_preview.png`, `annotations.json`, `training-data.json` and
  `room_concept.png/svg`.
- `import_cubicasa_sample(samplePath)` reads CubiCasa-style folders with
  `F1_scaled.png`, `F1_original.png` and `model.svg`.

CubiCasa5K is currently only an additional reference dataset for floor-plan
semantics. The project is not redesigned around CubiCasa, and no LMDB or
PyTorch training pipeline is required at this stage.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
