/**
 * Behaviour behind the visual effects a component can request (`style.effects`).
 *
 * Effects are named tokens. Each hook implements one with a few lines of DOM
 * work and CSS variables; the look itself is in generative.css. All of them
 * stand down when the theme's motion is "none" or the user prefers reduced
 * motion.
 */
import { useEffect, useState, type RefObject } from "react";

function motionAllowed(element: Element | null): boolean {
  if (typeof window === "undefined" || !element) return false;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return false;
  return element.closest(".g-root")?.getAttribute("data-motion") !== "none";
}

/** Marks the element once it has scrolled into view (drives `reveal` and counters). */
export function useInView(ref: RefObject<Element | null>, enabled: boolean): boolean {
  const [seen, setSeen] = useState(false);
  // Without the observer (an old browser, a test) nothing is ever held back.
  const observable = typeof IntersectionObserver !== "undefined";
  useEffect(() => {
    const element = ref.current;
    if (!enabled || !observable || !element || seen) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setSeen(true);
          observer.disconnect();
        }
      },
      { threshold: 0.12 },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [ref, enabled, observable, seen]);
  return seen || !enabled || !observable;
}

/** Moves a soft light to the pointer by updating two CSS variables. */
export function useSpotlight(ref: RefObject<HTMLElement | null>, enabled: boolean): void {
  useEffect(() => {
    const element = ref.current;
    if (!enabled || !element || !motionAllowed(element)) return;
    const onMove = (event: PointerEvent) => {
      const box = element.getBoundingClientRect();
      element.style.setProperty("--spot-x", `${event.clientX - box.left}px`);
      element.style.setProperty("--spot-y", `${event.clientY - box.top}px`);
      element.style.setProperty("--spot-on", "1");
    };
    const onLeave = () => element.style.setProperty("--spot-on", "0.55");
    element.addEventListener("pointermove", onMove);
    element.addEventListener("pointerleave", onLeave);
    return () => {
      element.removeEventListener("pointermove", onMove);
      element.removeEventListener("pointerleave", onLeave);
    };
  }, [ref, enabled]);
}

/** Lets an image drift a little slower than the page as its section scrolls by. */
export function useParallax(ref: RefObject<HTMLElement | null>, enabled: boolean): void {
  useEffect(() => {
    const element = ref.current;
    if (!enabled || !element || !motionAllowed(element)) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      const box = element.getBoundingClientRect();
      const progress = (box.top + box.height / 2 - window.innerHeight / 2) / window.innerHeight;
      element.style.setProperty("--parallax", `${Math.max(-1, Math.min(1, progress)) * -28}px`);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    // Capture: the canvas scrolls inside its own container, not the window.
    window.addEventListener("scroll", onScroll, { capture: true, passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll, { capture: true });
      if (frame) cancelAnimationFrame(frame);
    };
  }, [ref, enabled]);
}

const COUNT_DURATION_MS = 900;

/**
 * A number counting up to `target` once `start` is true. Returns `target`
 * straight away when counting is off, so the real figure is never withheld.
 */
export function useCountUp(target: number | null, start: boolean, enabled: boolean): number | null {
  // How far the count has got, 0..1. The figure shown is always derived from the real target.
  const [progress, setProgress] = useState(0);
  const animated = enabled && target !== null && typeof requestAnimationFrame !== "undefined";
  useEffect(() => {
    if (!animated || !start) return;
    let frame = 0;
    const began = performance.now();
    const tick = (now: number) => {
      const elapsed = Math.min((now - began) / COUNT_DURATION_MS, 1);
      setProgress(1 - (1 - elapsed) ** 3);
      if (elapsed < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [animated, start]);
  if (!animated || target === null) return target;
  if (!start) return 0;
  return progress >= 1 ? target : target * progress;
}
