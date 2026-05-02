export type Status = "upcoming" | "live" | "completed";

export type EventRecord = {
  id: number;
  title: string;
  sport: string;
  sportSlug: string;
  organization: string;
  organizationSlug: string;
  location: string;
  city: string;
  country: string;
  startDate: string;
  endDate: string;
  status: Status;
  sourceUrl: string;
};

export type SportCategory = {
  name: string;
  slug: string;
  eventCount: number;
  available: boolean;
};

export const statusLabels: Record<Status, string> = {
  upcoming: "Upcoming",
  live: "Live",
  completed: "Completed",
};

export const mockSports: SportCategory[] = [
  { name: "Judo", slug: "judo", eventCount: 8, available: true },
  { name: "Wrestling", slug: "wrestling", eventCount: 0, available: false },
  { name: "Boxing", slug: "boxing", eventCount: 0, available: false },
  { name: "Taekwondo", slug: "taekwondo", eventCount: 0, available: false },
];

export const mockEvents: EventRecord[] = [
  {
    id: 1,
    title: "Tbilisi Grand Slam 2026",
    sport: "Judo",
    sportSlug: "judo",
    organization: "International Judo Federation",
    organizationSlug: "ijf",
    location: "Tbilisi, Georgia",
    city: "Tbilisi",
    country: "Georgia",
    startDate: "2026-03-20",
    endDate: "2026-03-22",
    status: "upcoming",
    sourceUrl: "https://www.ijf.org/calendar",
  },
  {
    id: 2,
    title: "Antalya Grand Slam 2026",
    sport: "Judo",
    sportSlug: "judo",
    organization: "International Judo Federation",
    organizationSlug: "ijf",
    location: "Antalya, Turkiye",
    city: "Antalya",
    country: "Turkiye",
    startDate: "2026-04-03",
    endDate: "2026-04-05",
    status: "upcoming",
    sourceUrl: "https://www.ijf.org/calendar",
  },
  {
    id: 3,
    title: "European Judo Championships",
    sport: "Judo",
    sportSlug: "judo",
    organization: "European Judo Union",
    organizationSlug: "eju",
    location: "Prague, Czechia",
    city: "Prague",
    country: "Czechia",
    startDate: "2026-05-01",
    endDate: "2026-05-03",
    status: "live",
    sourceUrl: "https://www.eju.net/",
  },
  {
    id: 4,
    title: "World Judo Championships",
    sport: "Judo",
    sportSlug: "judo",
    organization: "International Judo Federation",
    organizationSlug: "ijf",
    location: "Baku, Azerbaijan",
    city: "Baku",
    country: "Azerbaijan",
    startDate: "2026-06-12",
    endDate: "2026-06-19",
    status: "upcoming",
    sourceUrl: "https://www.ijf.org/calendar",
  },
  {
    id: 5,
    title: "Paris Grand Slam 2025",
    sport: "Judo",
    sportSlug: "judo",
    organization: "International Judo Federation",
    organizationSlug: "ijf",
    location: "Paris, France",
    city: "Paris",
    country: "France",
    startDate: "2025-02-01",
    endDate: "2025-02-02",
    status: "completed",
    sourceUrl: "https://www.ijf.org/calendar",
  },
  {
    id: 6,
    title: "Asia-Oceania Judo Championships",
    sport: "Judo",
    sportSlug: "judo",
    organization: "Judo Union of Asia",
    organizationSlug: "jua",
    location: "Ulaanbaatar, Mongolia",
    city: "Ulaanbaatar",
    country: "Mongolia",
    startDate: "2026-07-16",
    endDate: "2026-07-19",
    status: "upcoming",
    sourceUrl: "https://www.onlinejua.org/",
  },
  {
    id: 7,
    title: "Tokyo Grand Slam 2026",
    sport: "Judo",
    sportSlug: "judo",
    organization: "International Judo Federation",
    organizationSlug: "ijf",
    location: "Tokyo, Japan",
    city: "Tokyo",
    country: "Japan",
    startDate: "2026-12-05",
    endDate: "2026-12-06",
    status: "upcoming",
    sourceUrl: "https://www.ijf.org/calendar",
  },
  {
    id: 8,
    title: "Panamerican-Oceania Championships",
    sport: "Judo",
    sportSlug: "judo",
    organization: "Panamerican Judo Confederation",
    organizationSlug: "pjc",
    location: "Lima, Peru",
    city: "Lima",
    country: "Peru",
    startDate: "2026-09-18",
    endDate: "2026-09-20",
    status: "upcoming",
    sourceUrl: "https://www.panamjudo.org/",
  },
];
