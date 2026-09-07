import type { CollectionEntry } from 'astro:content';

export type WeeklyIssue = CollectionEntry<'docs'>;

const ISSUE_SLUG = /^(\d{4})年\/(\d{1,2})月\/(\d{1,2})期$/;

export function isWeeklyIssue(entry: WeeklyIssue): boolean {
  return ISSUE_SLUG.test(entry.slug);
}

/**
 * Prefer an explicit content date, then fall back to the existing
 * `YYYY年/M月/D期` directory convention used by older issues.
 */
export function issueDate(entry: WeeklyIssue): Date {
  if (entry.data.lastUpdated instanceof Date && !Number.isNaN(entry.data.lastUpdated.valueOf())) {
    return entry.data.lastUpdated;
  }

  const match = entry.slug.match(ISSUE_SLUG);
  if (!match) return new Date(0);

  const [, year, month, day] = match;
  // Midday UTC avoids a date moving to the prior day in readers' time zones.
  return new Date(Date.UTC(Number(year), Number(month) - 1, Number(day), 12));
}

export function sortWeeklyIssues(entries: WeeklyIssue[]): WeeklyIssue[] {
  return entries
    .filter(isWeeklyIssue)
    .sort((a, b) => issueDate(b).valueOf() - issueDate(a).valueOf());
}
