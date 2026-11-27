type Props = {
  src?: string;
  poster?: string;
  title: string;
};

/** Plays only after a tap. Nothing is rendered until a real file is configured. */
export function RestorationVideo({ src, poster, title }: Props) {
  if (!src) return null;
  return (
    <figure>
      <video
        className="aspect-video w-full bg-brand-ink"
        controls
        playsInline
        preload="none"
        poster={poster}
        aria-label={title}
      >
        <source src={src} />
      </video>
      <figcaption className="mt-2 text-sm text-brand-ink/70">{title}</figcaption>
    </figure>
  );
}
