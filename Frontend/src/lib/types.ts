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

export type Region = {
  id: string;
  name: string;
  country: string;
  blurb: string;
  tripCount: number;
  fromPrice: number;
  cover: CoverTone;
  image: string;
};

export type SelectOption = {
  label: string;
  value: string;
};

export type Suggestion = {
  id: string;
  label: string;
  kind: "place" | "activity";
};
