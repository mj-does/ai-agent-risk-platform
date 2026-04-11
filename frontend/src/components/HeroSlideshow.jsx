import { useEffect, useState } from "react";

const SLIDE_MS = 5500;

export const HERO_SLIDES = [
  { src: "/2151883554.jpg.jpeg", alt: "Risk governance visual 1" },
  { src: "/146641652_bac6c069-04b1-4107-8027-8dddc55869c0.jpg.jpeg", alt: "Risk governance visual 2" },
];

/**
 * Full-bleed background slideshow (~85vh). Renders `children` centered on top (title, CTAs).
 */
export default function HeroSlideshow({ children }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const t = window.setInterval(() => {
      setIndex((i) => (i + 1) % HERO_SLIDES.length);
    }, SLIDE_MS);
    return () => window.clearInterval(t);
  }, []);

  return (
    <div
      className="heroSlideshow heroSlideshow--backdrop"
      role="region"
      aria-roledescription="carousel"
      aria-label="Product highlights"
    >
      <div className="heroSlideshowBackdrop">
        {HERO_SLIDES.map((slide, i) => (
          <div
            key={slide.src}
            className={`heroSlideshowSlide ${i === index ? "heroSlideshowSlide--active" : ""}`}
            aria-hidden={i !== index}
          >
            <img
              className="heroSlideshowImg"
              src={slide.src}
              alt=""
              decoding="async"
              fetchPriority={i === 0 ? "high" : "low"}
            />
          </div>
        ))}
        <div className="heroSlideshowScrim heroSlideshowScrim--backdrop" aria-hidden />
      </div>

      <div className="heroSlideshowOverlay">
        <div className="heroSlideshowOverlayStack">{children}</div>
      </div>

      <div className="heroSlideshowDots heroSlideshowDots--backdrop" role="tablist" aria-label="Slide">
        {HERO_SLIDES.map((_, i) => (
          <button
            key={String(i)}
            type="button"
            role="tab"
            aria-selected={i === index}
            aria-label={`Slide ${i + 1}`}
            className={`heroSlideshowDot ${i === index ? "heroSlideshowDot--active" : ""}`}
            onClick={() => setIndex(i)}
          />
        ))}
      </div>
    </div>
  );
}
