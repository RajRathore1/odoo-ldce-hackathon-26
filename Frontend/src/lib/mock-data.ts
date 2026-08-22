import type { ItineraryDay, Region, Suggestion, Trip } from "@/lib/types";

export const regions: Region[] = [
  {
    id: "himalayan-north",
    name: "Himalayan North",
    country: "India",
    blurb: "High passes, monasteries and very cold mornings",
    tripCount: 128,
    fromPrice: 32000,
    image:
      "https://images.unsplash.com/photo-1760835251791-1fda687de791?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "kerala",
    name: "Kerala Backwaters",
    country: "India",
    blurb: "Houseboats, coconut groves and slow afternoons",
    tripCount: 96,
    fromPrice: 28000,
    image:
      "https://images.unsplash.com/photo-1785932413547-cdd1159e1f1e?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "rajasthan",
    name: "Rajasthan",
    country: "India",
    blurb: "Forts, step wells and desert sunsets",
    tripCount: 143,
    fromPrice: 24000,
    image:
      "https://images.unsplash.com/photo-1599661046289-e31897846e41?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "japan",
    name: "Japan",
    country: "Japan",
    blurb: "Bullet trains, temple towns and autumn colour",
    tripCount: 71,
    fromPrice: 165000,
    image:
      "https://images.unsplash.com/photo-1558870832-c8db4b5b47d1?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "bali",
    name: "Bali & Nusa Islands",
    country: "Indonesia",
    blurb: "Rice terraces, reef dives and warm evenings",
    tripCount: 88,
    fromPrice: 74000,
    image:
      "https://images.unsplash.com/photo-1557093793-d149a38a1be8?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "swiss-alps",
    name: "Swiss Alps",
    country: "Switzerland",
    blurb: "Cable cars, lake towns and long ridge walks",
    tripCount: 54,
    fromPrice: 210000,
    image:
      "https://images.unsplash.com/photo-1755611532271-4ac09b51f2bc?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
];

export const trips: Trip[] = [
  {
    id: "kerala-backwaters",
    title: "Kerala Backwaters",
    city: "Alleppey",
    country: "India",
    startDate: "2026-08-18",
    endDate: "2026-08-26",
    budget: 64000,
    stops: 4,
    status: "ongoing",
    image:
      "https://images.unsplash.com/photo-1785932413547-cdd1159e1f1e?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "tokyo-autumn",
    title: "Tokyo in Autumn",
    city: "Tokyo",
    country: "Japan",
    startDate: "2026-10-04",
    endDate: "2026-10-14",
    budget: 210000,
    stops: 6,
    status: "upcoming",
    image:
      "https://images.unsplash.com/photo-1766133239036-e37f42a54869?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "rajasthan-loop",
    title: "Rajasthan Heritage Loop",
    city: "Jaipur",
    country: "India",
    startDate: "2026-12-20",
    endDate: "2026-12-30",
    budget: 88000,
    stops: 5,
    status: "upcoming",
    image:
      "https://images.unsplash.com/photo-1599661046289-e31897846e41?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "bali-reset",
    title: "Bali Reset",
    city: "Ubud",
    country: "Indonesia",
    startDate: "2026-03-02",
    endDate: "2026-03-11",
    budget: 132000,
    stops: 3,
    status: "completed",
    image:
      "https://images.unsplash.com/photo-1557093793-d149a38a1be8?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
  {
    id: "leh-ladakh",
    title: "Leh–Ladakh Ride",
    city: "Leh",
    country: "India",
    startDate: "2025-06-12",
    endDate: "2025-06-22",
    budget: 74000,
    stops: 7,
    status: "completed",
    image:
      "https://images.unsplash.com/photo-1760835251791-1fda687de791?fm=jpg&q=70&w=800&auto=format&fit=crop",
  },
];

export const suggestions: Suggestion[] = [
  { id: "old-town-walk", label: "Old town walking tour", kind: "activity" },
  { id: "sunset-viewpoint", label: "Sunset viewpoint", kind: "place" },
  { id: "local-food-market", label: "Local food market", kind: "place" },
  { id: "heritage-museum", label: "Heritage museum", kind: "activity" },
  { id: "evening-boat-ride", label: "Evening boat ride", kind: "activity" },
  { id: "nearby-hiking-trail", label: "Nearby hiking trail", kind: "place" },
  { id: "street-food-crawl", label: "Street food crawl", kind: "activity" },
  { id: "sunrise-viewpoint", label: "Sunrise viewpoint", kind: "place" },
];

export const tripsByStatus = {
  ongoing: trips.filter((trip) => trip.status === "ongoing"),
  upcoming: trips.filter((trip) => trip.status === "upcoming"),
  completed: trips.filter((trip) => trip.status === "completed"),
};

export const itineraries: Record<string, ItineraryDay[]> = {
  "kerala-backwaters": [
    {
      day: 1,
      activities: [
        { id: "kb-1-1", activity: "Houseboat check-in, Alleppey", expense: 8000 },
        { id: "kb-1-2", activity: "Sunset backwater cruise", expense: 1500 },
      ],
    },
    {
      day: 2,
      activities: [
        { id: "kb-2-1", activity: "Kumarakom bird sanctuary", expense: 800 },
        { id: "kb-2-2", activity: "Village walk and toddy tasting", expense: 600 },
      ],
    },
    {
      day: 3,
      activities: [
        { id: "kb-3-1", activity: "Ayurvedic spa session", expense: 2500 },
        { id: "kb-3-2", activity: "Coconut lagoon dinner", expense: 1200 },
      ],
    },
    {
      day: 4,
      activities: [
        { id: "kb-4-1", activity: "Vembanad lake kayaking", expense: 1000 },
        { id: "kb-4-2", activity: "Farewell houseboat lunch", expense: 1500 },
      ],
    },
  ],
  "tokyo-autumn": [
    {
      day: 1,
      activities: [
        { id: "tk-1-1", activity: "Airport transfer and check-in", expense: 6000 },
        { id: "tk-1-2", activity: "Shibuya crossing evening walk", expense: 500 },
      ],
    },
    {
      day: 2,
      activities: [
        { id: "tk-2-1", activity: "Senso-ji temple and Asakusa street food", expense: 2000 },
        { id: "tk-2-2", activity: "teamLab digital art museum", expense: 3500 },
      ],
    },
    {
      day: 3,
      activities: [
        { id: "tk-3-1", activity: "Mount Fuji day trip", expense: 9000 },
        { id: "tk-3-2", activity: "Kawaguchiko lake viewpoint", expense: 1000 },
      ],
    },
    {
      day: 4,
      activities: [
        { id: "tk-4-1", activity: "Meiji shrine and Harajuku", expense: 1500 },
        { id: "tk-4-2", activity: "Shinjuku Omoide Yokocho dinner", expense: 2800 },
      ],
    },
    {
      day: 5,
      activities: [
        { id: "tk-5-1", activity: "Tsukiji outer market breakfast", expense: 1200 },
        { id: "tk-5-2", activity: "Ginza shopping walk", expense: 4000 },
      ],
    },
  ],
  "rajasthan-loop": [
    {
      day: 1,
      activities: [
        { id: "rj-1-1", activity: "Jaipur arrival and Amber Fort", expense: 1200 },
      ],
    },
    {
      day: 2,
      activities: [
        { id: "rj-2-1", activity: "City Palace and Hawa Mahal", expense: 900 },
        { id: "rj-2-2", activity: "Chokhi Dhani cultural dinner", expense: 2000 },
      ],
    },
    {
      day: 3,
      activities: [
        { id: "rj-3-1", activity: "Drive to Jodhpur, Mehrangarh Fort", expense: 3500 },
      ],
    },
    {
      day: 4,
      activities: [
        { id: "rj-4-1", activity: "Jaisalmer desert safari and camel ride", expense: 4500 },
      ],
    },
    {
      day: 5,
      activities: [
        { id: "rj-5-1", activity: "Sam sand dunes sunset and cultural show", expense: 2500 },
      ],
    },
  ],
  "bali-reset": [
    {
      day: 1,
      activities: [
        { id: "bl-1-1", activity: "Ubud arrival and rice terrace walk", expense: 1000 },
      ],
    },
    {
      day: 2,
      activities: [
        { id: "bl-2-1", activity: "Monkey forest and traditional spa", expense: 3000 },
      ],
    },
    {
      day: 3,
      activities: [
        { id: "bl-3-1", activity: "Mount Batur sunrise trek", expense: 2800 },
      ],
    },
    {
      day: 4,
      activities: [
        { id: "bl-4-1", activity: "Uluwatu temple and Kecak dance", expense: 1500 },
      ],
    },
    {
      day: 5,
      activities: [
        { id: "bl-5-1", activity: "Nusa Penida day trip", expense: 4200 },
      ],
    },
  ],
  "leh-ladakh": [
    {
      day: 1,
      activities: [
        { id: "lh-1-1", activity: "Leh acclimatisation, local market walk", expense: 500 },
      ],
    },
    {
      day: 2,
      activities: [
        { id: "lh-2-1", activity: "Shanti Stupa and Leh Palace", expense: 700 },
      ],
    },
    {
      day: 3,
      activities: [
        { id: "lh-3-1", activity: "Pangong Lake ride, fuel and permits", expense: 6000 },
      ],
    },
    {
      day: 4,
      activities: [
        { id: "lh-4-1", activity: "Nubra Valley and Diskit monastery", expense: 5500 },
      ],
    },
    {
      day: 5,
      activities: [
        { id: "lh-5-1", activity: "Khardung La pass and return", expense: 3000 },
      ],
    },
  ],
};
