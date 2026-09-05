import os

# Defaults let the backend run with zero external services for local
# development (sqlite file + in-process state store). docker-compose.yml
# overrides these with real Postgres/Redis URLs for the full stack.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./signal_monitor.db")
REDIS_URL = os.getenv("REDIS_URL")  # None -> fall back to in-memory store

SIMULATOR_TICK_SECONDS = float(os.getenv("SIMULATOR_TICK_SECONDS", "1.0"))

# --- Media stream thresholds (TR 101 290 inspired: Priority 1 = breaks
# decodability, Priority 2 = impairs quality, Priority 3 = informational) ---
MEDIA_P1_PACKET_LOSS_PCT = 5.0
MEDIA_P1_SEQ_DISCONTINUITY_COUNT = 3
MEDIA_P2_PACKET_LOSS_PCT = 1.0
MEDIA_P2_JITTER_MS = 5.0
MEDIA_P3_JITTER_MS = 2.0

# --- PTP thresholds (ST 2059 / IEEE 1588 inspired) ---
PTP_P1_OFFSET_US = 1000.0       # sync effectively lost
PTP_P2_OFFSET_US = 100.0        # drifting, still locked
PTP_P3_OFFSET_US = 50.0
PTP_MEAN_PATH_DELAY_WARN_US = 500.0
