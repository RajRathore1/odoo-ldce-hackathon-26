export type TripStatus = "ongoing" | "upcoming" | "completed";

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
  image: string;
};

export type Region = {
  id: string;
  name: string;
  country: string;
  blurb: string;
  tripCount: number;
  fromPrice: number;
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

export type ItineraryActivity = {
  id: string;
  activity: string;
  expense: number;
};

export type ItineraryDay = {
  day: number;
  activities: ItineraryActivity[];
};
