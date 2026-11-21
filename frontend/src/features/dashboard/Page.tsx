import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader } from "@/components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { StatusBadge, UrgencyBadge } from "@/components/StatusBadges";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { daysSince, referenceToday } from "@/features/calendar/derive";
import { t } from "@/features/dashboard/i18n";
import {
  formatShortDate,
  relativeDays,
  URGENCY_LABEL,
  type Urgency,
} from "@/lib/format";
import { useCases } from "@/lib/hooks";
import type { Case } from "@/lib/types";

const CLOSED_WINDOW_DAYS = 30;

const URGENCY_CHART: { urgency: Urgency; color: string }[] = [
  { urgency: "overdue", color: "#dc2626" },
  { urgency: "today", color: "#ea580c" },
  { urgency: "tomorrow", color: "#d97706" },
  { urgency: "soon", color: "#ca8a04" },
  { urgency: "normal", color: "#059669" },
  { urgency: "closed", color: "#64748b" },
];

type ClosedCase = { item: Case; days: number };

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useCases({
    sort: "deadline_asc",
  });

  const cases = useMemo(() => data ?? [], [data]);
  const referenceDate = useMemo(() => referenceToday(cases), [cases]);

  if (isLoading) return <LoadingState rows={4} variant="cards" />;
  if (isError) return <ErrorState error={error} onRetry={() => void refetch()} />;

  const overdue = cases.filter((item) => item.urgency === "overdue");
  const today = cases.filter((item) => item.urgency === "today");
  const soon = cases.filter(
    (item) => item.urgency === "tomorrow" || item.urgency === "soon",
  );
  const closed = cases.filter((item) => item.urgency === "closed");

  const stats = [
    {
      label: t.stats.overdue,
      value: overdue.length,
      icon: AlertTriangle,
      tone: "text-red-600 dark:text-red-400",
    },
    {
      label: t.stats.today,
      value: today.length,
      icon: Clock,
      tone: "text-orange-600 dark:text-orange-400",
    },
    {
      label: t.stats.soon,
      value: soon.length,
      icon: CalendarClock,
      tone: "text-amber-600 dark:text-amber-400",
    },
    {
      label: t.stats.closed,
      value: closed.length,
      icon: CheckCircle2,
      tone: "text-emerald-600 dark:text-emerald-400",
    },
  ];

  const chartData = URGENCY_CHART.map(({ urgency, color }) => ({
    label: URGENCY_LABEL[urgency],
    count: cases.filter((item) => item.urgency === urgency).length,
    color,
  }));

  const closedRecently: ClosedCase[] = cases
    .filter(
      (item): item is Case & { response_date: string } =>
        item.status === "odpowiedz_wyslana" && item.response_date !== null,
    )
    .map((item) => ({ item, days: daysSince(referenceDate, item.response_date) }))
    .filter((entry) => entry.days >= 0 && entry.days <= CLOSED_WINDOW_DAYS)
    .sort((a, b) => a.days - b.days);

  const urgent = cases
    .filter((item) => item.urgency !== "closed")
    .slice(0, 6);

  return (
    <div>
      <PageHeader
        title={t.page.title}
        description={t.page.description}
        actions={
          <Button asChild>
            <Link to="/kalendarz">{t.page.openCalendar}</Link>
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <Icon className={`h-4 w-4 ${stat.tone}`} />
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold tabular-nums">{stat.value}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t.chart.title}</CardTitle>
            <CardDescription>{t.chart.description}</CardDescription>
          </CardHeader>
          <CardContent>
            {cases.length === 0 ? (
              <EmptyState title={t.chart.empty} />
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="label"
                      tick={{ fontSize: 11 }}
                      interval={0}
                      tickLine={false}
                    />
                    <YAxis allowDecimals={false} width={32} tick={{ fontSize: 11 }} />
                    <Tooltip
                      formatter={(value) => [String(value), t.chart.series]}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry) => (
                        <Cell key={entry.label} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t.closed.title}</CardTitle>
            <CardDescription>{t.closed.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {closedRecently.length === 0 ? (
              <EmptyState title={t.closed.empty} />
            ) : (
              closedRecently.map(({ item, days }) => (
                <Link
                  key={item.id}
                  to={`/kalendarz?case=${item.id}`}
                  className="flex flex-col gap-1 rounded-lg border p-3 transition-colors hover:bg-accent"
                >
                  <span className="truncate text-sm font-medium">
                    {item.subject}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {item.case_number} · {t.closed.responseDate}{" "}
                    {formatShortDate(item.response_date)} ·{" "}
                    {relativeDays(-days)}
                  </span>
                </Link>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{t.upcoming.title}</CardTitle>
          <CardDescription>{t.upcoming.description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {urgent.length === 0 ? (
            <EmptyState title={t.upcoming.empty} />
          ) : (
            urgent.map((item) => (
              <Link
                key={item.id}
                to={`/kalendarz?case=${item.id}`}
                className="flex flex-col gap-2 rounded-lg border p-3 transition-colors hover:bg-accent sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0 space-y-1">
                  <p className="truncate text-sm font-medium">{item.subject}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.case_number} · wpływ {formatShortDate(item.inflow_date)} ·
                    termin {formatShortDate(item.deadline)}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <StatusBadge status={item.status} />
                  <UrgencyBadge
                    urgency={item.urgency}
                    days={item.days_remaining}
                  />
                </div>
              </Link>
            ))
          )}
        </CardContent>
      </Card>

      <p className="mt-4 text-xs text-muted-foreground">
        {t.footer.nextDeadline}:{" "}
        {urgent[0] ? relativeDays(urgent[0].days_remaining) : "—"}
      </p>
    </div>
  );
}
