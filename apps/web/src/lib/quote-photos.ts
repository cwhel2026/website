/** Compress driveway photographs on the device before they are uploaded. */

import { resolveApiUrl } from "@/lib/api";

export const PHOTO_TARGET_MAX_BYTES = 500 * 1024;

const EDGES = [1600, 1400, 1280];
const QUALITIES = [0.78, 0.7, 0.62];

export function newPhotoToken(): string {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  let binary = "";
  for (const value of bytes) binary += String.fromCharCode(value);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export async function compressDrivewayPhoto(file: File): Promise<Blob> {
  const bitmap = await createImageBitmap(file);
  try {
    let best: Blob | null = null;
    for (const edge of EDGES) {
      const scale = Math.min(1, edge / Math.max(bitmap.width, bitmap.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(bitmap.width * scale));
      canvas.height = Math.max(1, Math.round(bitmap.height * scale));
      const context = canvas.getContext("2d");
      if (!context) break;
      context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
      for (const quality of QUALITIES) {
        const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
        if (!blob) continue;
        best = blob;
        if (blob.size <= PHOTO_TARGET_MAX_BYTES) return blob;
      }
    }
    if (!best) throw new Error("Could not prepare the photograph");
    return best;
  } finally {
    bitmap.close();
  }
}

export function postDrivewayPhoto(options: {
  blob: Blob;
  token: string;
  note?: string;
  replaceId?: string;
  onProgress: (percent: number) => void;
}): { promise: Promise<string | undefined>; abort: () => void } {
  const form = new FormData();
  form.append("token", options.token);
  if (options.note) form.append("note", options.note);
  if (options.replaceId) form.append("replace_id", options.replaceId);
  form.append("files", options.blob, "driveway.jpg");
  const xhr = new XMLHttpRequest();
  const promise = new Promise<string | undefined>((resolve, reject) => {
    xhr.open("POST", `${resolveApiUrl()}/api/v1/quotation-photos`);
    xhr.responseType = "json";
    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      options.onProgress(Math.min(99, Math.round((event.loaded / event.total) * 100)));
    };
    xhr.onerror = () => reject(new Error("network"));
    xhr.onabort = () => reject(new Error("aborted"));
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const body = xhr.response as { uploaded_id?: string; photos?: { id: string }[] } | null;
          options.onProgress(100);
          resolve(body?.uploaded_id ?? body?.photos?.[body.photos.length - 1]?.id);
          return;
        }
      const error = new Error("upload") as Error & { status?: number };
      error.status = xhr.status;
      reject(error);
    };
    xhr.send(form);
  });
  return { promise, abort: () => xhr.abort() };
}
