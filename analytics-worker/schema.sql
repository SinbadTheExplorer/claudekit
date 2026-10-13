-- Aggregate counters only. No IPs, no user agents, no per-visitor rows kept
-- past the current UTC day.
CREATE TABLE IF NOT EXISTS agg (
  day  TEXT NOT NULL,      -- YYYY-MM-DD (UTC)
  kind TEXT NOT NULL,      -- 'visitor' | 'visit' | 'tab' | 'node' | 'shock'
  key  TEXT NOT NULL,      -- tab name / node id / scenario id / 'all'
  hits INTEGER NOT NULL DEFAULT 0,  -- times opened / clicked
  ms   INTEGER NOT NULL DEFAULT 0,  -- total visible time spent on it
  PRIMARY KEY (day, kind, key)
);

-- Today's salted visitor hashes, only so the same person isn't counted twice
-- in one day. Rows from earlier days are deleted on the next write, and the
-- salt changes every day, so hashes can't be linked across days.
CREATE TABLE IF NOT EXISTS seen (
  day TEXT NOT NULL,
  h   TEXT NOT NULL,
  PRIMARY KEY (day, h)
);
