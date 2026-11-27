"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { resolveApiUrl } from "@/lib/api";

type Photo = { id: string };

export default function LaterPhotographsPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [note, setNote] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    fetch(`/api/v1/quotation-photos/${token}`)
      .then(async (res) => {
        if (!res.ok) throw new Error("This photograph link was not recognised");
        return res.json() as Promise<{ photos: Photo[]; note: string | null }>;
      })
      .then((data) => {
        setPhotos(data.photos);
        setNote(data.note ?? "");
      })
      .catch((err: Error) => setError(err.message));
  }, [token]);

  async function upload(files: FileList | null) {
    if (!files || files.length === 0 || !token) return;
    setError(null);
    setMessage(null);
    const form = new FormData();
    form.append("token", token);
    if (note.trim()) form.append("note", note.trim());
    for (const file of Array.from(files)) form.append("files", file);
    const res = await fetch(`${resolveApiUrl()}/api/v1/quotation-photos`, {
      method: "POST",
      body: form,
      credentials: "same-origin",
    });
    if (!res.ok) {
      setError("Could not upload the photograph");
      return;
    }
    const data = (await res.json()) as { photos: Photo[] };
    setPhotos(data.photos);
    setMessage("Saved with your quotation. This does not change your estimate.");
  }

  return (
    <div className="site-container py-10 text-[#1a1a1a]">
      <h1 className="font-display text-3xl font-semibold">Add driveway photographs</h1>
      <p className="mt-3 max-w-xl text-sm leading-relaxed">
        If you have any cracks or areas that may need repairing, please include a close-up photograph. Minor wear
        around edges is perfectly normal.
      </p>
      <div className="mt-6 flex max-w-xl flex-col gap-3 sm:flex-row">
        <label className="w-full rounded-md border border-[#1a1a1a] px-4 py-3 text-center text-sm font-semibold">
          Take a photo
          <input
            type="file"
            accept="image/*"
            capture="environment"
            className="sr-only"
            onChange={(event) => void upload(event.target.files)}
          />
        </label>
        <label className="w-full rounded-md border border-[#1a1a1a] px-4 py-3 text-center text-sm font-semibold">
          Choose from gallery
          <input
            type="file"
            accept="image/*"
            multiple
            className="sr-only"
            data-testid="later-gallery"
            onChange={(event) => void upload(event.target.files)}
          />
        </label>
      </div>
      <label className="mt-4 block max-w-xl text-sm font-medium">
        Notes (optional)
        <textarea
          value={note}
          onChange={(event) => setNote(event.target.value)}
          rows={3}
          className="mt-1 w-full rounded-md border border-stone-line px-4 py-3"
        />
      </label>
      {photos.length > 0 && (
        <ul className="mt-6 grid max-w-xl grid-cols-2 gap-3">
          {photos.map((photo) => (
            <li key={photo.id}>
              <img
                src={`/api/v1/quotation-photos/${token}/${photo.id}`}
                alt="Driveway photograph"
                className="h-32 w-full rounded object-cover"
              />
            </li>
          ))}
        </ul>
      )}
      {message && <p className="mt-4 text-sm">{message}</p>}
      {error && <p className="mt-4 text-sm text-red-700">{error}</p>}
    </div>
  );
}
