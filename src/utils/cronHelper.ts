/**
 * Parses a 5-part cron expression and returns the recurring interval in
 * milliseconds, suitable for use with setInterval.
 *
 * Supported patterns (fields: minute hour day month weekday):
 *   "* * * * *"   → every minute  (60 000 ms)
 *   "0 * * * *"   → every hour    (3 600 000 ms)
 *   "0 8 * * *"   → every day     (86 400 000 ms)
 *   "0 8 * * 1"   → every week    (604 800 000 ms)
 *   "0 8 1 * *"   → every month   (2 592 000 000 ms, 30-day approximation)
 *
 * Any expression that does not match a more specific pattern defaults to
 * a 24-hour interval.
 */
export function parseCronToMs(cron: string): number {
  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) {
    throw new Error(
      `Invalid cron expression "${cron}": expected 5 fields, got ${parts.length}`
    );
  }

  const [minute, hour, day, month, weekday] = parts;

  const MS_MINUTE = 60 * 1000;
  const MS_HOUR   = 60 * MS_MINUTE;
  const MS_DAY    = 24 * MS_HOUR;
  const MS_WEEK   = 7  * MS_DAY;
  const MS_MONTH  = 30 * MS_DAY;

  // Every minute: "* * * * *"
  if (isWild(minute) && isWild(hour) && isWild(day) && isWild(month) && isWild(weekday)) {
    return MS_MINUTE;
  }

  // Every hour: "<m> * * * *"  (minute is fixed, rest are wildcards)
  if (!isWild(minute) && isWild(hour) && isWild(day) && isWild(month) && isWild(weekday)) {
    return MS_HOUR;
  }

  // Every week: "<m> <h> * * <dow>"  (weekday is fixed)
  if (!isWild(minute) && !isWild(hour) && isWild(day) && isWild(month) && !isWild(weekday)) {
    return MS_WEEK;
  }

  // Every month: "<m> <h> <d> * *"
  if (!isWild(minute) && !isWild(hour) && !isWild(day) && isWild(month) && isWild(weekday)) {
    return MS_MONTH;
  }

  // Every day (default for "<m> <h> * * *"):
  return MS_DAY;
}

function isWild(field: string): boolean {
  return field === '*';
}
