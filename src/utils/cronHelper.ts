/**
 * Given a cron expression (5 fields), compute milliseconds until the next occurrence.
 * Supports only basic patterns: exact values and "*" for each field.
 * For production use, consider a library like `cron-parser`.
 */
export function parseCronToMs(expr: string): number {
  const parts = expr.trim().split(/\s+/);
  if (parts.length !== 5) return -1;

  const [minStr, hourStr] = parts;
  const now = new Date();
  const next = new Date();

  const minute = minStr === '*' ? 0 : parseInt(minStr, 10);
  const hour = hourStr === '*' ? now.getHours() : parseInt(hourStr, 10);

  next.setHours(hour, minute, 0, 0);

  // If time already passed today, schedule for tomorrow
  if (next.getTime() <= now.getTime()) {
    next.setDate(next.getDate() + 1);
  }

  return next.getTime() - now.getTime();
}
