"use client";

import { useState } from "react";

export default function ImageCarousel({ images, alt }: { images: string[]; alt: string }) {
  const [index, setIndex] = useState(0);
  const [failed, setFailed] = useState<Record<number, boolean>>({});

  const usable = images.filter((_, i) => !failed[i]);

  if (images.length === 0 || usable.length === 0) {
    return (
      <div className="aspect-[4/3] w-full rounded-lg bg-gray-100 flex items-center justify-center text-gray-400">
        <span className="text-3xl">🏠</span>
      </div>
    );
  }

  const safeIndex = Math.min(index, images.length - 1);

  function go(delta: number, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setIndex((prev) => (prev + delta + images.length) % images.length);
  }

  return (
    <div className="relative aspect-[4/3] w-full rounded-lg overflow-hidden bg-gray-100 group">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={images[safeIndex]}
        alt={alt}
        loading="lazy"
        className="w-full h-full object-cover"
        onError={() => setFailed((f) => ({ ...f, [safeIndex]: true }))}
      />

      {images.length > 1 && (
        <>
          <button
            onClick={(e) => go(-1, e)}
            aria-label="Previous photo"
            className="absolute left-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-black/50 text-white text-sm opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
          >
            ‹
          </button>
          <button
            onClick={(e) => go(1, e)}
            aria-label="Next photo"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-black/50 text-white text-sm opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
          >
            ›
          </button>
          <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
            {images.map((_, i) => (
              <span
                key={i}
                className={`w-1.5 h-1.5 rounded-full ${i === safeIndex ? "bg-white" : "bg-white/50"}`}
              />
            ))}
          </div>
          <span className="absolute bottom-2 right-2 text-[10px] font-medium text-white bg-black/50 rounded px-1.5 py-0.5">
            {safeIndex + 1}/{images.length}
          </span>
        </>
      )}
    </div>
  );
}
