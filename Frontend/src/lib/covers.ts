import type { CoverTone } from "@/lib/types";

// Stand-ins for photography until we have real imagery.
export const coverGradients: Record<CoverTone, string> = {
  sunset: "from-accent to-danger",
  ocean: "from-info to-primary",
  forest: "from-success to-info",
  dusk: "from-primary to-danger",
};
