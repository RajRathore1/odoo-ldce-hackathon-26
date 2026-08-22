export type TripStatus = "ongoing" | "upcoming" | "completed" | "cancelled";

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

// A destination as the catalog returns it - one city, with what it costs and
// how much there is to do there.
export type Region = {
  id: string;
  name: string;
  country: string;
  blurb: string;
  activityCount: number;
  avgDailyCost: number;
  currency: string;
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

export type CommunityPost = {
  id: string;
  author: string;
  place: string;
  content: string;
  likes: number;
  postedAt: string;
  image?: string;
};
