TRANSIENT_NETWORK_ERRORS = ["ConnectionError", "Timeout", "RetryError"]

# Measured on 2026-10-28: the EDS API answers one query to Elspotprices per window of about 300 s (per client). A different
# query, or the same one after its ~44 s cache lifetime, gets 429 with `Retry-After` for the rest of the window (the
# repeat at +14 s took 36 ms from cache, the one at +89 s got 429). CO2Emis has no such limit. So a test run sends exactly
# one query to Elspotprices, and every live test that needs its data shares it (`elspotprices_latest`). Two runs less than
# five minutes apart can still collide; the client then fails fast (RetryAfterTooLongError) instead of waiting.
ELSPOTPRICES_LIVE_QUERY = {"limit": 5, "sort": "SpotPriceDKK desc"}
