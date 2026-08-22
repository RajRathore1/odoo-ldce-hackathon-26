"""
accounts — selectors. Owner: Dev A.

READ layer: querysets, `annotate`, `aggregate`, `select_related` /
`prefetch_related`. Never mutates anything.

Every list selector needs its prefetches — an N+1 in a list endpoint is
the one performance bug that shows up live in a demo.
"""
