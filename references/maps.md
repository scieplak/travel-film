# Route maps

1. Outline: `python3 scripts/fetch_outline.py "<island or region>" --out work/outline.json` (Nominatim, sends only
   the place name). Natural Earth is too coarse for one island.
2. Waypoints: real stops from phone GPS clusters (cluster per day, 1.5 km radius) **plus road bends** so routes
   follow roads (coastal motorways, passes). Accommodation = where the night's photos cluster.
3. Config: see `examples/route_config.example.json`. Labels: `[text, side]` or `[text, waypoint, side]`.
4. Verify: `python3 scripts/verify_map.py config.json --inventory work/inventory.json --out work/verify_map.jpg` —
   photos coloured by day over the outline, waypoints, raw routes. Fix: waypoint off its photo cluster; a day's
   photo cluster with no stop; a straight line over mountains; a return route via the wrong valley (check the
   photos taken on the way).
5. Build: `python3 scripts/route_maps.py config.json --out film/compositions --durations '[…]'` (duration = slot
   + dissolve). Zoom adapts to each day's route; previous days stay faint.

Ask the person when GPS is ambiguous ("you slept in X but the night photos are in Y — caption Y, map ends in X?").
