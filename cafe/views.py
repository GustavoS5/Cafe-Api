from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from cafe.models import Cafe
from cafe.serializers import CafePriceSerializer, CafeSerializer


def require_api_key(request):
    api_key = request.headers.get("X-API-KEY")

    if api_key != settings.API_KEY:
        return Response({"error": "Invalid or missing API key."}, status=status.HTTP_401_UNAUTHORIZED)

    return None


@api_view(["GET"])
def get_random_cafe(request):
    cafe = Cafe.objects.order_by("?").first()

    if cafe is None:
        return Response({"error": "No cafes found."}, status=404)

    serializer = CafeSerializer(cafe)
    return Response(serializer.data)


@api_view(["GET"])
def get_all_cafes(request):
    cafes = Cafe.objects.all()

    if not cafes.exists():
        return Response({"error": "No cafes found."}, status=404)

    serializer = CafeSerializer(cafes, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def search_cafe(request):
    loc = request.GET.get("loc")

    if not loc:
        return Response({"error": "Please provide a location."}, status=400)

    cafes = Cafe.objects.filter(location__icontains=loc)

    if not cafes.exists():
        return Response({"error": "No cafes found in that location."}, status=404)

    serializer = CafeSerializer(cafes, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def add_cafe(request):
    auth_error = require_api_key(request)
    if auth_error is not None:
        return auth_error

    serializer = CafeSerializer(data=request.data)

    if serializer.is_valid():
        cafe = serializer.save()
        return Response({"success": f"{cafe.name} added successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
def update_cafe_price(request, pk):
    auth_error = require_api_key(request)
    if auth_error is not None:
        return auth_error

    try:
        cafe = Cafe.objects.get(pk=pk)
    except Cafe.DoesNotExist:
        return Response({"error": "Cafe not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = CafePriceSerializer(cafe, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({"success": "Cafe price updated successfully."}, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_cafe(request, pk):
    auth_error = require_api_key(request)
    if auth_error is not None:
        return auth_error

    try:
        cafe = Cafe.objects.get(pk=pk)
    except Cafe.DoesNotExist:
        return Response({"error": "Cafe not found."}, status=status.HTTP_404_NOT_FOUND)

    cafe.delete()

    return Response({"success": "Cafe deleted successfully."}, status=status.HTTP_200_OK)
