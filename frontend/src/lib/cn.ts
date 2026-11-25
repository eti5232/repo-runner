import { clsx, type ClassValue } from "clsx";

/** מאחד שמות של class ל-CSS, ומתעלם מערכים ריקים. */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
