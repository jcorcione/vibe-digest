import { parseCronToMs } from '../src/utils/cronHelper';

const MS_MINUTE = 60 * 1000;
const MS_HOUR   = 60 * MS_MINUTE;
const MS_DAY    = 24 * MS_HOUR;
const MS_WEEK   = 7  * MS_DAY;
const MS_MONTH  = 30 * MS_DAY;

describe('parseCronToMs', () => {
  describe('every-minute pattern', () => {
    it('"* * * * *" → 60 000 ms', () => {
      expect(parseCronToMs('* * * * *')).toBe(MS_MINUTE);
    });
  });

  describe('every-hour pattern', () => {
    it('"0 * * * *" → 3 600 000 ms', () => {
      expect(parseCronToMs('0 * * * *')).toBe(MS_HOUR);
    });

    it('"30 * * * *" (any fixed minute) → 3 600 000 ms', () => {
      expect(parseCronToMs('30 * * * *')).toBe(MS_HOUR);
    });
  });

  describe('every-day pattern', () => {
    it('"0 8 * * *" → 86 400 000 ms', () => {
      expect(parseCronToMs('0 8 * * *')).toBe(MS_DAY);
    });

    it('"0 0 * * *" → 86 400 000 ms', () => {
      expect(parseCronToMs('0 0 * * *')).toBe(MS_DAY);
    });

    it('"30 23 * * *" → 86 400 000 ms', () => {
      expect(parseCronToMs('30 23 * * *')).toBe(MS_DAY);
    });
  });

  describe('every-week pattern', () => {
    it('"0 8 * * 1" (Monday at 08:00) → 604 800 000 ms', () => {
      expect(parseCronToMs('0 8 * * 1')).toBe(MS_WEEK);
    });

    it('"0 9 * * 5" (Friday at 09:00) → 604 800 000 ms', () => {
      expect(parseCronToMs('0 9 * * 5')).toBe(MS_WEEK);
    });
  });

  describe('every-month pattern', () => {
    it('"0 8 1 * *" (1st of month at 08:00) → 2 592 000 000 ms', () => {
      expect(parseCronToMs('0 8 1 * *')).toBe(MS_MONTH);
    });

    it('"0 6 15 * *" (15th of month at 06:00) → 2 592 000 000 ms', () => {
      expect(parseCronToMs('0 6 15 * *')).toBe(MS_MONTH);
    });
  });

  describe('error handling', () => {
    it('throws on too few fields', () => {
      expect(() => parseCronToMs('0 8 * *')).toThrow(
        /Invalid cron expression/
      );
    });

    it('throws on too many fields', () => {
      expect(() => parseCronToMs('0 8 * * * *')).toThrow(
        /Invalid cron expression/
      );
    });

    it('throws on empty string', () => {
      expect(() => parseCronToMs('')).toThrow(/Invalid cron expression/);
    });
  });
});
