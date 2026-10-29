TRANSIENT_NETWORK_ERRORS = ["ConnectionError", "Timeout", "RetryError"]

# Measured on 2026-10-28 for Elspotprices (since discontinued): the EDS API answered one query per window of about 300 s
# (per client). A different query, or the same one after its ~44 s cache lifetime, got 429 with `Retry-After` for the rest
# of the window (the repeat at +14 s took 36 ms from cache, the one at +89 s got 429). CO2Emis has no such limit.
# The limit of DayAheadPrices is not measured, so a test run still sends exactly one query to it, shared by every live test
# that needs its data (`dayaheadprices_latest`). Two runs less than five minutes apart could collide; the client then
# fails fast (RetryAfterTooLongError) instead of waiting.
DAYAHEADPRICES_LIVE_QUERY = {"limit": 5, "sort": "DayAheadPriceDKK desc"}
