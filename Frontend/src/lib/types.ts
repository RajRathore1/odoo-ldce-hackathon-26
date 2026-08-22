export type TripStatus = "ongoing" | "upcoming" | "completed";

export type CoverTone = "sunset" | "ocean" | "forest" | "dusk";

export type Trip = {
  id: string;
  title: string;
  city: string;
  country: string;
  startDate: string;
  endDate: string;
  budget: number;
  stops: number;
  status: TripStatus;
  cover: CoverTone;
};

export type SelectOption = {
  label: string;
  value: string;
};
