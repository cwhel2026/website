"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { compressDrivewayPhoto, postDrivewayPhoto } from "@/lib/quote-photos";

type Photo = { id: string };
type Pending = { id: string; progress: number; status: "uploading" | "failed"; blob?: Blob; file?: File };

export default function LaterPhotographsPage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [pending, setPending] = useState<Pending[]>([]);
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

  async function sendOne(itemId: string, blob: Blob) {
    if (!token) return;
    for (let attempt = 0; attempt < 3; attempt += 1) {
      const upload = postDrivewayPhoto({
        blob,
        token,
        note: note.trim() || undefined,
        onProgress: (progress) =>
          setPending((current) => current.map((item) => (item.id === itemId ? { ...item, progress, status: "uploading" } : item))),
      });
      try {
        const serverId = await upload.promise;
        setPending((current) => current.filter((item) => item.id !== itemId));
        if (serverId) setPhotos((current) => [...current, { id: serverId }]);
        setMessage("Saved with your quotation. This does not change your estimate.");
        return;
      } catch (err) {
        const status = (err as { status?: number }).status;
        if ((status && status < 500) || attempt === 2) {
          setPending((current) => current.map((item) => (item.id === itemId ? { ...item, status: "failed", blob } : item)));
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)));
      }
    }
  }

  async function upload(files: FileList | null) {
    if (!files || files.length === 0 || !token) return;
    setError(null);
    setMessage(null);
    for (const file of Array.from(files)) {
      const itemId = crypto.randomUUID();
      try {
        const blob = await compressDrivewayPhoto(file);
        setPending((current) => [...current, { id: itemId, progress: 0, status: "uploading", blob }]);
        void sendOne(itemId, blob);
      } catch {
        setPending((current) => [...current, { id: itemId, progress: 0, status: "failed", file }]);
      }
    }
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
      {pending.length > 0 && (
        <ul className="mt-4 max-w-xl space-y-2 text-sm">
          {pending.map((item) => (
            <li key={item.id}>
              <p>{item.status === "failed" ? "Upload paused" : `Uploading ${item.progress}%`}</p>
              <div className="mt-1 h-1.5 overflow-hidden rounded bg-stone-line" role="progressbar" aria-valuenow={item.progress} aria-valuemin={0} aria-valuemax={100}>
                <div className="h-full bg-[#e0b323]" style={{ width: `${item.progress}%` }} />
              </div>
              {item.status === "failed" && item.blob && (
                <button type="button" className="mt-1 underline" onClick={() => void sendOne(item.id, item.blob!)}>
                  Retry upload
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
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
