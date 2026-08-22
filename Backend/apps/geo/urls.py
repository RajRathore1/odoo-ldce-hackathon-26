"""
User-facing routes for geo. Mounted by `config/api_urls.py`.

`/cities/popular/` is listed before `/cities/<int:pk>/` for readability only —
`<int:pk>` could not have matched `popular` in the first place.
"""

from django.urls import path

from apps.geo.views import (
    CityDetailView,
    CityListView,
    CountryListView,
    PopularCityListView,
    SavedDestinationDestroyView,
    SavedDestinationListCreateView,
)

urlpatterns = [
    path("countries/", CountryListView.as_view(), name="country-list"),
    path("cities/", CityListView.as_view(), name="city-list"),
    path("cities/popular/", PopularCityListView.as_view(), name="city-popular"),
    path("cities/<int:pk>/", CityDetailView.as_view(), name="city-detail"),
    # Owned by `geo`, served under `/users/me/` — see MODELS.md §4 for why.
    path(
        "users/me/saved-destinations/",
        SavedDestinationListCreateView.as_view(),
        name="saved-destination-list",
    ),
    path(
        "users/me/saved-destinations/<int:pk>/",
        SavedDestinationDestroyView.as_view(),
        name="saved-destination-detail",
    ),
]
