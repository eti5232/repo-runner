import type { SVGProps } from "react";

/** אייקונים בסגנון קו אחיד (24x24). כל אייקון הוא רשימת נתיבים. */
const PATHS = {
  check: ["M20 6 9 17l-5-5"],
  x: ["M18 6 6 18M6 6l12 12"],
  alert: ["M12 8v5M12 16.5h.01", "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z"],
  clock: ["M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z", "M12 7v5l3 2"],
  search: ["M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14Z", "m20 20-3.5-3.5"],
  download: ["M12 3v12m0 0 4-4m-4 4-4-4", "M5 21h14"],
  copy: ["M9 9h10v12H9z", "M5 15V3h10"],
  terminal: ["m4 17 6-6-6-6", "M12 19h8"],
  file: ["M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z", "M14 3v5h5"],
  play: ["M7 4v16l13-8z"],
  star: ["m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"],
  fork: ["M6 3v6a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3V3M12 12v9"],
  bolt: ["M13 2 4 14h7l-1 8 9-12h-7z"],
  shield: ["M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z", "m9 12 2 2 4-4"],
  refresh: ["M21 12a9 9 0 1 1-3-6.7L21 8", "M21 3v5h-5"],
  stop: ["M6 6h12v12H6z"],
  box: ["M21 8 12 3 3 8v8l9 5 9-5z", "m3 8 9 5 9-5M12 13v8"],
  link: ["M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1", "M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"],
  lock: ["M5 11h14v10H5z", "M8 11V7a4 4 0 0 1 8 0v4"],
  branch: ["M6 3v12", "M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z", "M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z", "M18 9a9 9 0 0 1-9 9"],
  arrow: ["M5 12h14m-6-6 6 6-6 6"],
  list: ["M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"],
  plus: ["M12 5v14M5 12h14"],
  chevron: ["m9 6 6 6-6 6"],
  dot: ["M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"],
} as const;

export type IconName = keyof typeof PATHS;

type IconProps = { name: IconName; size?: number } & Omit<SVGProps<SVGSVGElement>, "name">;

/** אייקון בגודל ובצבע של הטקסט שסביבו (currentColor). */
export function Icon({ name, size = 16, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {PATHS[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
