import { NextResponse } from "next/server";

/** Instant liveness — Next.js only; does not wait on FastAPI (for Railway / smoke tests). */
export async function GET() {
  return NextResponse.json(
    {
      status: "ok",
      layer: "web",
      image_kind: process.env.RMD_IMAGE_KIND ?? "unknown",
    },
    { status: 200 },
  );
}