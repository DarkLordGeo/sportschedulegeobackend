import {
  ArrowUpRight,
  CalendarDays,
  ChevronRight,
  CircleDot,
  Filter,
  Globe2,
  LayoutDashboard,
  ListFilter,
  MapPin,
  Search,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { mockEvents, mockSports, type EventRecord, type Status } from "@/mock/schedule";

type Page = "home" | "events" | "event" | "sport" | "organization";

const events = mockEvents;

const ui = {
  allSports: "ყველა სპორტი",
  allOrganizations: "ყველა ორგანიზაცია",
  allCountries: "ყველა ქვეყანა",
  allStatuses: "ყველა სტატუსი",
};

const sportLabels: Record<string, string> = {
  "All sports": ui.allSports,
  Judo: "ძიუდო",
  Wrestling: "ჭიდაობა",
  Boxing: "კრივი",
  Taekwondo: "ტაეკვონდო",
};

const organizationLabels: Record<string, string> = {
  "All organizations": ui.allOrganizations,
  "International Judo Federation": "ძიუდოს საერთაშორისო ფედერაცია",
  "European Judo Union": "ევროპის ძიუდოს კავშირი",
  "Judo Union of Asia": "აზიის ძიუდოს კავშირი",
  "Panamerican Judo Confederation": "პანამერიკის ძიუდოს კონფედერაცია",
};

const countryLabels: Record<string, string> = {
  "All countries": ui.allCountries,
  Georgia: "საქართველო",
  Turkiye: "თურქეთი",
  Czechia: "ჩეხეთი",
  Azerbaijan: "აზერბაიჯანი",
  France: "საფრანგეთი",
  Mongolia: "მონღოლეთი",
  Japan: "იაპონია",
  Peru: "პერუ",
};

const cityLabels: Record<string, string> = {
  Tbilisi: "თბილისი",
  Antalya: "ანტალია",
  Prague: "პრაღა",
  Baku: "ბაქო",
  Paris: "პარიზი",
  Ulaanbaatar: "ულან-ბატორი",
  Tokyo: "ტოკიო",
  Lima: "ლიმა",
};

const eventTitleLabels: Record<string, string> = {
  "Tbilisi Grand Slam 2026": "თბილისის გრანდ სლემი 2026",
  "Antalya Grand Slam 2026": "ანტალიის გრანდ სლემი 2026",
  "European Judo Championships": "ევროპის ძიუდოს ჩემპიონატი",
  "World Judo Championships": "მსოფლიო ძიუდოს ჩემპიონატი",
  "Paris Grand Slam 2025": "პარიზის გრანდ სლემი 2025",
  "Asia-Oceania Judo Championships": "აზია-ოკეანიის ძიუდოს ჩემპიონატი",
  "Tokyo Grand Slam 2026": "ტოკიოს გრანდ სლემი 2026",
  "Panamerican-Oceania Championships": "პანამერიკა-ოკეანიის ჩემპიონატი",
};

const statusLabelKa: Record<Status, string> = {
  upcoming: "მომავალი",
  live: "მიმდინარე",
  completed: "დასრულებული",
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ka-GE", {
    month: "short",
    day: "2-digit",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function dateRange(event: EventRecord) {
  if (event.startDate === event.endDate) return formatDate(event.startDate);
  return `${formatDate(event.startDate)} - ${formatDate(event.endDate)}`;
}

function eventTitle(event: EventRecord) {
  return eventTitleLabels[event.title] ?? event.title;
}

function eventLocation(event: EventRecord) {
  return `${cityLabels[event.city] ?? event.city}, ${countryLabels[event.country] ?? event.country}`;
}

function optionLabel(option: string) {
  if (option === "All statuses") return ui.allStatuses;
  if (option in statusLabelKa) return statusLabelKa[option as Status];
  return sportLabels[option] ?? organizationLabels[option] ?? countryLabels[option] ?? option;
}

function countLabel(count: number, noun: string) {
  return `${count} ${noun}`;
}

export function App() {
  const [page, setPage] = useState<Page>("events");
  const [selectedEventId, setSelectedEventId] = useState(1);
  const [filters, setFilters] = useState({
    sport: "All sports",
    organization: "All organizations",
    country: "All countries",
    status: "All statuses",
    from: "",
    to: "",
    query: "",
  });

  const selectedEvent = events.find((event) => event.id === selectedEventId) ?? events[0];
  const sports = ["All sports", ...Array.from(new Set(events.map((event) => event.sport)))];
  const organizations = [
    "All organizations",
    ...Array.from(new Set(events.map((event) => event.organization))),
  ];
  const countries = ["All countries", ...Array.from(new Set(events.map((event) => event.country)))];
  const statuses = ["All statuses", "upcoming", "live", "completed"];

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      const matchesSport = filters.sport === "All sports" || event.sport === filters.sport;
      const matchesOrganization =
        filters.organization === "All organizations" || event.organization === filters.organization;
      const matchesCountry =
        filters.country === "All countries" || event.country === filters.country;
      const matchesStatus =
        filters.status === "All statuses" || event.status === filters.status;
      const matchesFrom = !filters.from || event.startDate >= filters.from;
      const matchesTo = !filters.to || event.startDate <= filters.to;
      const query = filters.query.trim().toLowerCase();
      const matchesQuery =
        !query ||
        [event.title, event.organization, event.country, event.city]
          .join(" ")
          .toLowerCase()
          .includes(query);

      return (
        matchesSport &&
        matchesOrganization &&
        matchesCountry &&
        matchesStatus &&
        matchesFrom &&
        matchesTo &&
        matchesQuery
      );
    });
  }, [filters]);

  const showEvent = (event: EventRecord) => {
    setSelectedEventId(event.id);
    setPage("event");
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="site-topbar">
          <div className="brand">
            <div className="brand-mark">
              <CircleDot size={19} />
            </div>
            <div>
              <strong>sportsgeorgia</strong>
              <span>ოფიციალური შეჯიბრებების ინდექსი</span>
            </div>
          </div>

          <div className="source-panel">
            <span>დაფარვა</span>
            <strong>4 წყაროს ჯგუფი</strong>
            <p>ფედერაციები, რეგიონები, ღონისძიებები</p>
          </div>
        </div>

        <nav className="global-nav" aria-label="მთავარი ნავიგაცია">
          <NavButton active={page === "home"} icon={<LayoutDashboard />} label="მთავარი" onClick={() => setPage("home")} />
          <NavButton active={page === "events"} icon={<CalendarDays />} label="ღონისძიებები" onClick={() => setPage("events")} />
          <NavButton active={page === "sport"} icon={<ShieldCheck />} label="ძიუდო" onClick={() => setPage("sport")} />
          <NavButton active={page === "organization"} icon={<Globe2 />} label="ორგანიზაციები" onClick={() => setPage("organization")} />
        </nav>
      </header>

      <main className="content">
        {page === "home" && (
          <HomePage events={events} setPage={setPage} showEvent={showEvent} />
        )}

        {page === "events" && (
          <EventsPage
            title="ღონისძიებები"
            subtitle="დაათვალიერე ოფიციალური სპორტული კალენდრები, შეადარე ორგანიზაციები და გაფილტრე თარიღით ან სტატუსით."
            events={filteredEvents}
            filters={filters}
            setFilters={setFilters}
            sports={sports}
            organizations={organizations}
            countries={countries}
            statuses={statuses}
            showEvent={showEvent}
          />
        )}

        {page === "event" && <EventDetails event={selectedEvent} setPage={setPage} />}

        {page === "sport" && (
          <EventsPage
            title="ძიუდო"
            subtitle="შეჯიბრებების განრიგი ძიუდოს ორგანიზაციებისა და ოფიციალური კალენდრების მიხედვით."
            events={events.filter((event) => event.sportSlug === "judo")}
            filters={filters}
            setFilters={setFilters}
            sports={sports}
            organizations={organizations}
            countries={countries}
            statuses={statuses}
            showEvent={showEvent}
          />
        )}

        {page === "organization" && (
          <OrganizationPage events={events} showEvent={showEvent} setPage={setPage} />
        )}
      </main>
    </div>
  );
}

function NavButton({
  active,
  icon,
  label,
  onClick,
}: {
  active: boolean;
  icon: ReactNode;
  label: string;
  onClick: () => void;
}) {
  return (
    <button className={`nav-button ${active ? "active" : ""}`} onClick={onClick}>
      {icon}
      <span>{label}</span>
    </button>
  );
}

function HomePage({
  events,
  setPage,
  showEvent,
}: {
  events: EventRecord[];
  setPage: (page: Page) => void;
  showEvent: (event: EventRecord) => void;
}) {
  const upcoming = events.filter((event) => event.status !== "completed").slice(0, 4);

  return (
    <div className="page-stack">
      <section className="hero">
        <div>
          <span className="eyebrow">ოფიციალური განრიგების აგრეგატორი</span>
          <h1>შეადარე სპორტული კალენდრები ერთ სივრცეში</h1>
          <p>
            ნახე ფედერაციები, ქვეყნები, სტატუსები და ოფიციალური წყაროები სუფთა შეჯიბრებების ინდექსში.
          </p>
        </div>
        <Button className="primary-button" onClick={() => setPage("events")}>
          ღონისძიებების ნახვა
          <ChevronRight size={17} />
        </Button>
      </section>

      <section className="category-row" aria-label="სპორტის კატეგორიები">
        {mockSports.map((sport) => (
          <button className={`category-tile ${sport.available ? "ready" : ""}`} key={sport.slug}>
            <span>{sportLabels[sport.name] ?? sport.name}</span>
            <small>{sport.available ? countLabel(sport.eventCount, "ღონისძიება") : "მალე დაემატება"}</small>
          </button>
        ))}
      </section>

      <section className="panel">
        <SectionHeader title="მომავალი ღონისძიებები" meta={countLabel(upcoming.length, "რჩეული")} />
        <EventTable events={upcoming} showEvent={showEvent} compact />
      </section>
    </div>
  );
}

function EventsPage({
  title,
  subtitle,
  events,
  filters,
  setFilters,
  sports,
  organizations,
  countries,
  statuses,
  showEvent,
}: {
  title: string;
  subtitle: string;
  events: EventRecord[];
  filters: {
    sport: string;
    organization: string;
    country: string;
    status: string;
    from: string;
    to: string;
    query: string;
  };
  setFilters: React.Dispatch<React.SetStateAction<{
    sport: string;
    organization: string;
    country: string;
    status: string;
    from: string;
    to: string;
    query: string;
  }>>;
  sports: string[];
  organizations: string[];
  countries: string[];
  statuses: string[];
  showEvent: (event: EventRecord) => void;
}) {
  return (
    <div className="events-layout">
      <aside className="filters">
        <div className="filters-title">
          <Filter size={18} />
          <div>
            <strong>ფილტრები</strong>
            <span>{countLabel(events.length, "შედეგი")}</span>
          </div>
        </div>
        <FilterSelect label="სპორტი" value={filters.sport} options={sports} onChange={(sport) => setFilters((current) => ({ ...current, sport }))} />
        <FilterSelect label="ორგანიზაცია" value={filters.organization} options={organizations} onChange={(organization) => setFilters((current) => ({ ...current, organization }))} />
        <FilterSelect label="ქვეყანა" value={filters.country} options={countries} onChange={(country) => setFilters((current) => ({ ...current, country }))} />
        <FilterSelect label="სტატუსი" value={filters.status} options={statuses} onChange={(status) => setFilters((current) => ({ ...current, status }))} />
        <label className="field">
          <span>დან</span>
          <Input type="date" value={filters.from} onChange={(event) => setFilters((current) => ({ ...current, from: event.target.value }))} />
        </label>
        <label className="field">
          <span>მდე</span>
          <Input type="date" value={filters.to} onChange={(event) => setFilters((current) => ({ ...current, to: event.target.value }))} />
        </label>
        <Button
          className="secondary-button"
          variant="secondary"
          onClick={() =>
            setFilters({
              sport: "All sports",
              organization: "All organizations",
              country: "All countries",
              status: "All statuses",
              from: "",
              to: "",
              query: "",
            })
          }
        >
          გასუფთავება
        </Button>
      </aside>

      <section className="list-panel">
        <div className="page-header">
          <div>
            <span className="eyebrow">განრიგის ბრაუზერი</span>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div className="metric-strip">
            <Metric label="ღონისძიება" value={String(events.length)} />
            <Metric label="მიმდინარე" value={String(events.filter((event) => event.status === "live").length)} />
            <Metric label="ქვეყანა" value={String(new Set(events.map((event) => event.country)).size)} />
          </div>
        </div>

        <div className="toolbar">
          <label className="search-field">
            <Search size={18} />
            <Input
              placeholder="მოძებნე ღონისძიება, ქვეყანა, ორგანიზაცია"
              value={filters.query}
              onChange={(event) => setFilters((current) => ({ ...current, query: event.target.value }))}
            />
          </label>
          <Dialog>
            <DialogTrigger asChild>
              <Button className="icon-button" variant="outline" size="icon" title="სიის დაზუსტება">
                <ListFilter size={18} />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>აქტიური ფილტრები</DialogTitle>
                <DialogDescription>
                  სპორტი: {optionLabel(filters.sport)}. ორგანიზაცია: {optionLabel(filters.organization)}. ქვეყანა: {optionLabel(filters.country)}. სტატუსი: {optionLabel(filters.status)}.
                </DialogDescription>
              </DialogHeader>
            </DialogContent>
          </Dialog>
        </div>

        <EventTable events={events} showEvent={showEvent} />
      </section>
    </div>
  );
}

function EventDetails({ event, setPage }: { event: EventRecord; setPage: (page: Page) => void }) {
  return (
    <div className="page-stack">
      <Button className="text-button" variant="ghost" onClick={() => setPage("events")}>
        ღონისძიებებზე დაბრუნება
      </Button>
      <section className="detail-header">
        <div>
          <StatusBadge status={event.status} />
          <h1>{eventTitle(event)}</h1>
          <p>{organizationLabels[event.organization] ?? event.organization} / {eventLocation(event)} / {dateRange(event)}</p>
        </div>
        <Button className="primary-button" asChild>
          <a href={event.sourceUrl} target="_blank" rel="noreferrer">
          ოფიციალურ წყაროზე გადასვლა
          <ArrowUpRight size={17} />
          </a>
        </Button>
      </section>

      <section className="metadata-grid">
        <MetaCard label="სპორტი" value={sportLabels[event.sport] ?? event.sport} />
        <MetaCard label="ორგანიზაცია" value={organizationLabels[event.organization] ?? event.organization} />
        <MetaCard label="ლოკაცია" value={eventLocation(event)} />
        <MetaCard label="თარიღები" value={dateRange(event)} />
        <MetaCard label="სტატუსი" value={statusLabelKa[event.status]} />
        <MetaCard label="წყარო" value="ოფიციალური კალენდარი" />
      </section>

      <section className="panel">
        <SectionHeader title="ღონისძიების ეტაპები" meta="განრიგის მეტამონაცემები" />
        <div className="timeline">
          <TimelineItem title="წყარო მოძებნილია" text="სკრაპერმა იპოვა ოფიციალური ღონისძიების გვერდი ან კალენდრის ჩანაწერი." />
          <TimelineItem title="მონაცემები დალაგებულია" text="ლოკაცია, თარიღები, ორგანიზაცია და სტატუსი გადაყვანილია backend ველებში." />
          <TimelineItem title="გამოქვეყნებულია" text="ღონისძიება ხელმისაწვდომია საჯარო API-სა და სიის ხედებში." />
        </div>
      </section>
    </div>
  );
}

function OrganizationPage({
  events,
  showEvent,
  setPage,
}: {
  events: EventRecord[];
  showEvent: (event: EventRecord) => void;
  setPage: (page: Page) => void;
}) {
  const ijfEvents = events.filter((event) => event.organizationSlug === "ijf");

  return (
    <div className="page-stack">
      <section className="page-header organization-header">
        <div>
          <span className="eyebrow">ორგანიზაცია</span>
          <h1>ძიუდოს საერთაშორისო ფედერაცია</h1>
          <p>ძიუდოს ოფიციალური შეჯიბრებების კალენდრის წყარო მომავალი და დასრულებული ღონისძიებებით.</p>
        </div>
        <Button className="primary-button" onClick={() => setPage("events")}>
          ყველა ღონისძიება
          <ChevronRight size={17} />
        </Button>
      </section>
      <section className="panel">
        <SectionHeader title="ორგანიზაციის ღონისძიებები" meta={countLabel(ijfEvents.length, "ჩანაწერი")} />
        <EventTable events={ijfEvents} showEvent={showEvent} />
      </section>
    </div>
  );
}

function EventTable({
  events,
  showEvent,
  compact = false,
}: {
  events: EventRecord[];
  showEvent: (event: EventRecord) => void;
  compact?: boolean;
}) {
  return (
    <div className="table-wrap">
      <Table className={compact ? "compact-table" : ""}>
        <TableHeader>
          <TableRow>
            <TableHead>ღონისძიება</TableHead>
            <TableHead>სპორტი</TableHead>
            <TableHead>ორგანიზაცია</TableHead>
            <TableHead>ლოკაცია</TableHead>
            <TableHead>თარიღი</TableHead>
            <TableHead>სტატუსი</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id} onClick={() => showEvent(event)}>
              <TableCell data-label="ღონისძიება">
                <strong>{eventTitle(event)}</strong>
                <span className="row-subtitle">{event.sourceUrl.replace("https://", "")}</span>
              </TableCell>
              <TableCell data-label="სპორტი">{sportLabels[event.sport] ?? event.sport}</TableCell>
              <TableCell data-label="ორგანიზაცია">{organizationLabels[event.organization] ?? event.organization}</TableCell>
              <TableCell data-label="ლოკაცია">
                <span className="location-cell">
                  <MapPin size={15} />
                  {eventLocation(event)}
                </span>
              </TableCell>
              <TableCell data-label="თარიღი">{dateRange(event)}</TableCell>
              <TableCell data-label="სტატუსი">
                <StatusBadge status={event.status} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {events.length === 0 && <div className="empty-state">არჩეულ ფილტრებს არცერთი ღონისძიება არ ემთხვევა.</div>}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem value={option} key={option}>
              {optionLabel(option)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}

function StatusBadge({ status }: { status: Status }) {
  return <Badge className={`status-badge ${status}`}>{statusLabelKa[status]}</Badge>;
}

function SectionHeader({ title, meta }: { title: string; meta: string }) {
  return (
    <div className="section-header">
      <h2>{title}</h2>
      <span>{meta}</span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function MetaCard({ label, value }: { label: string; value: string }) {
  return (
    <Card className="meta-card">
      <CardContent>
        <span>{label}</span>
        <strong>{value}</strong>
      </CardContent>
    </Card>
  );
}

function TimelineItem({ title, text }: { title: string; text: string }) {
  return (
    <div className="timeline-item">
      <span />
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>
    </div>
  );
}
