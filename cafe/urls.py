from django.urls import path
from . import views

urlpatterns = [
    path("random/", views.get_random_cafe, name="random-cafe"),
    path("all/", views.get_all_cafes, name="all-cafes"),
    path("search/", views.search_cafe, name="search-cafe"),
    path("add/", views.add_cafe, name="add-cafe"),
    path("update-price/<int:pk>/", views.update_cafe_price, name="update-cafe-price"),
    path("delete/<int:pk>/", views.delete_cafe, name="delete-cafe"),
]
