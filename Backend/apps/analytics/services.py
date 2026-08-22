"""
analytics — services. Owner: Dev B.

WRITE layer.

Note that `ActivityLog` rows are written by `middleware.py`, not from here —
middleware sees every request, so no other app needs a logging call site.
"""
