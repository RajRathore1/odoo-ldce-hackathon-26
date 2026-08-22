export type AdminUser = {
  id: string;
  name: string;
  email: string;
  city: string;
  trips: number;
  joined: string;
  status: "active" | "suspended";
};

export const users: AdminUser[] = [
  {
    id: "u1",
    name: "Meera Nair",
    email: "meera.nair@example.com",
    city: "Kochi",
    trips: 5,
    joined: "2026-01-14",
    status: "active",
  },
  {
    id: "u2",
    name: "Kabir Shah",
    email: "kabir.shah@example.com",
    city: "Mumbai",
    trips: 3,
    joined: "2026-02-02",
    status: "active",
  },
  {
    id: "u3",
    name: "Priya Menon",
    email: "priya.menon@example.com",
    city: "Bengaluru",
    trips: 8,
    joined: "2025-11-20",
    status: "active",
  },
  {
    id: "u4",
    name: "Daichi Sato",
    email: "daichi.sato@example.com",
    city: "Tokyo",
    trips: 2,
    joined: "2026-03-11",
    status: "active",
  },
  {
    id: "u5",
    name: "Tenzin Dolma",
    email: "tenzin.dolma@example.com",
    city: "Leh",
    trips: 6,
    joined: "2025-09-30",
    status: "suspended",
  },
  {
    id: "u6",
    name: "Arjun Verma",
    email: "arjun.verma@example.com",
    city: "Jaipur",
    trips: 4,
    joined: "2026-04-05",
    status: "active",
  },
  {
    id: "u7",
    name: "Ananya Rao",
    email: "ananya.rao@example.com",
    city: "Delhi",
    trips: 1,
    joined: "2026-06-18",
    status: "active",
  },
];

export const staticStats = {
  totalUsers: 4820,
  activeUsers: 4310,
  suspendedUsers: 62,
};

export type Period = "7d" | "30d" | "90d" | "12m";

export const periods: { value: Period; label: string }[] = [
  { value: "7d", label: "7 days" },
  { value: "30d", label: "30 days" },
  { value: "90d", label: "90 days" },
  { value: "12m", label: "12 months" },
];

type PeriodData = {
  kpis: {
    tripsPlanned: number;
    revenue: number;
    avgBudget: number;
    newSignups: number;
    communityPosts: number;
  };
  signups: { label: string; users: number }[];
  cities: { city: string; country: string; trips: number }[];
  activities: { activity: string; bookings: number }[];
};

export const activityCategory: Record<
  string,
  "culture" | "nature" | "adventure"
> = {
  "Heritage fort and palace tours": "culture",
  "Houseboat and backwater stays": "nature",
  "Desert safaris and camel rides": "adventure",
  "Temple and culture walks": "culture",
  "Trekking and high-altitude passes": "adventure",
  "Rice terrace and rural cycling": "nature",
};

export const dashboardByPeriod: Record<Period, PeriodData> = {
  "7d": {
    kpis: {
      tripsPlanned: 62,
      revenue: 820000,
      avgBudget: 84200,
      newSignups: 58,
      communityPosts: 42,
    },
    signups: [
      { label: "Mon", users: 6 },
      { label: "Tue", users: 9 },
      { label: "Wed", users: 7 },
      { label: "Thu", users: 12 },
      { label: "Fri", users: 10 },
      { label: "Sat", users: 8 },
      { label: "Sun", users: 6 },
    ],
    cities: [
      { city: "Bali & Nusa Islands", country: "Indonesia", trips: 5 },
      { city: "Kerala Backwaters", country: "India", trips: 4 },
      { city: "Rajasthan", country: "India", trips: 4 },
      { city: "Japan", country: "Japan", trips: 3 },
      { city: "Himalayan North", country: "India", trips: 2 },
      { city: "Swiss Alps", country: "Switzerland", trips: 1 },
    ],
    activities: [
      { activity: "Houseboat and backwater stays", bookings: 7 },
      { activity: "Desert safaris and camel rides", bookings: 5 },
      { activity: "Heritage fort and palace tours", bookings: 4 },
      { activity: "Rice terrace and rural cycling", bookings: 3 },
      { activity: "Trekking and high-altitude passes", bookings: 3 },
      { activity: "Temple and culture walks", bookings: 2 },
    ],
  },
  "30d": {
    kpis: {
      tripsPlanned: 240,
      revenue: 3100000,
      avgBudget: 85100,
      newSignups: 310,
      communityPosts: 180,
    },
    signups: [
      { label: "Week 1", users: 62 },
      { label: "Week 2", users: 71 },
      { label: "Week 3", users: 84 },
      { label: "Week 4", users: 93 },
    ],
    cities: [
      { city: "Rajasthan", country: "India", trips: 13 },
      { city: "Kerala Backwaters", country: "India", trips: 12 },
      { city: "Himalayan North", country: "India", trips: 11 },
      { city: "Bali & Nusa Islands", country: "Indonesia", trips: 9 },
      { city: "Japan", country: "Japan", trips: 6 },
      { city: "Swiss Alps", country: "Switzerland", trips: 5 },
    ],
    activities: [
      { activity: "Houseboat and backwater stays", bookings: 26 },
      { activity: "Heritage fort and palace tours", bookings: 24 },
      { activity: "Desert safaris and camel rides", bookings: 18 },
      { activity: "Trekking and high-altitude passes", bookings: 16 },
      { activity: "Temple and culture walks", bookings: 15 },
      { activity: "Rice terrace and rural cycling", bookings: 11 },
    ],
  },
  "90d": {
    kpis: {
      tripsPlanned: 640,
      revenue: 8400000,
      avgBudget: 86000,
      newSignups: 780,
      communityPosts: 480,
    },
    signups: [
      { label: "Jun", users: 180 },
      { label: "Jul", users: 260 },
      { label: "Aug", users: 310 },
    ],
    cities: [
      { city: "Rajasthan", country: "India", trips: 40 },
      { city: "Himalayan North", country: "India", trips: 36 },
      { city: "Kerala Backwaters", country: "India", trips: 27 },
      { city: "Bali & Nusa Islands", country: "Indonesia", trips: 25 },
      { city: "Japan", country: "Japan", trips: 20 },
      { city: "Swiss Alps", country: "Switzerland", trips: 15 },
    ],
    activities: [
      { activity: "Heritage fort and palace tours", bookings: 78 },
      { activity: "Houseboat and backwater stays", bookings: 70 },
      { activity: "Desert safaris and camel rides", bookings: 55 },
      { activity: "Temple and culture walks", bookings: 48 },
      { activity: "Trekking and high-altitude passes", bookings: 44 },
      { activity: "Rice terrace and rural cycling", bookings: 35 },
    ],
  },
  "12m": {
    kpis: {
      tripsPlanned: 2150,
      revenue: 18600000,
      avgBudget: 86400,
      newSignups: 1850,
      communityPosts: 1284,
    },
    signups: [
      { label: "Sep", users: 60 },
      { label: "Oct", users: 75 },
      { label: "Nov", users: 90 },
      { label: "Dec", users: 110 },
      { label: "Jan", users: 95 },
      { label: "Feb", users: 130 },
      { label: "Mar", users: 120 },
      { label: "Apr", users: 150 },
      { label: "May", users: 210 },
      { label: "Jun", users: 180 },
      { label: "Jul", users: 260 },
      { label: "Aug", users: 310 },
    ],
    cities: [
      { city: "Rajasthan", country: "India", trips: 143 },
      { city: "Himalayan North", country: "India", trips: 128 },
      { city: "Kerala Backwaters", country: "India", trips: 96 },
      { city: "Bali & Nusa Islands", country: "Indonesia", trips: 88 },
      { city: "Japan", country: "Japan", trips: 71 },
      { city: "Swiss Alps", country: "Switzerland", trips: 54 },
    ],
    activities: [
      { activity: "Heritage fort and palace tours", bookings: 312 },
      { activity: "Houseboat and backwater stays", bookings: 268 },
      { activity: "Desert safaris and camel rides", bookings: 221 },
      { activity: "Temple and culture walks", bookings: 194 },
      { activity: "Trekking and high-altitude passes", bookings: 176 },
      { activity: "Rice terrace and rural cycling", bookings: 142 },
    ],
  },
};
