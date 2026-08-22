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

export const popularCities: { city: string; country: string; trips: number }[] =
  [
    { city: "Rajasthan", country: "India", trips: 143 },
    { city: "Himalayan North", country: "India", trips: 128 },
    { city: "Kerala Backwaters", country: "India", trips: 96 },
    { city: "Bali & Nusa Islands", country: "Indonesia", trips: 88 },
    { city: "Japan", country: "Japan", trips: 71 },
    { city: "Swiss Alps", country: "Switzerland", trips: 54 },
  ];

export const popularActivities: { activity: string; bookings: number }[] = [
  { activity: "Heritage fort and palace tours", bookings: 312 },
  { activity: "Houseboat and backwater stays", bookings: 268 },
  { activity: "Desert safaris and camel rides", bookings: 221 },
  { activity: "Temple and culture walks", bookings: 194 },
  { activity: "Trekking and high-altitude passes", bookings: 176 },
  { activity: "Rice terrace and rural cycling", bookings: 142 },
];

export const platformStats = {
  totalUsers: 4820,
  tripsPlanned: 2150,
  citiesCovered: 46,
  avgBudget: 86400,
};

export const monthlySignups: { month: string; users: number }[] = [
  { month: "Mar", users: 120 },
  { month: "Apr", users: 150 },
  { month: "May", users: 210 },
  { month: "Jun", users: 180 },
  { month: "Jul", users: 260 },
  { month: "Aug", users: 310 },
];
