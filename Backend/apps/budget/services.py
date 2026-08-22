"""
budget — services. Owner: Dev A.

WRITE layer + **the single cost formula**.

`trip_cost_summary(trip)` and `bulk_trip_cost_summary(trip_ids)` live here
and nowhere else. The trip list, trip detail, itinerary totals and the
dashboard all import them. Re-deriving the arithmetic anywhere else is how
the four screens start disagreeing about the same trip.
"""
