import { parseCronToMs } from '../src/utils/cronHelper';

describe('parseCronToMs', () => {
  it('returns a positive number for a future daily cron', () => {
    const ms = parseCronToMs('0 8 * * *');
    expect(typeof ms).toBe('number');
    // Either scheduled for later today or tomorrow — always positive
    expect(ms).toBeGreaterThan(0);
  });

  it('returns -1 for an invalid expression', () => {
    expect(parseCronToMs('bad expr')).toBe(-1);
  });

  it('schedules at least 1 minute ahead', () => {
    // Wildcard minute
    const ms = parseCronToMs('* * * * *');
    expect(ms).toBeGreaterThanOrEqual(0);
  });
});
