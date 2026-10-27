from rest_framework import serializers
from cafe.models import Cafe


class CafeSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        price = attrs.get("coffee_price", getattr(self.instance, "coffee_price", None))
        currency = attrs.get("currency", getattr(self.instance, "currency", ""))
        if price is not None and not currency:
            raise serializers.ValidationError({"currency": "A currency is required with a price."})
        if price is None and currency:
            raise serializers.ValidationError({"coffee_price": "A price is required with a currency."})
        return attrs

    class Meta:
        model = Cafe
        fields = "__all__"


class CafePriceSerializer(CafeSerializer):
    coffee_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=True,
        allow_null=False,
    )

    class Meta:
        model = Cafe
        fields = ["coffee_price", "currency"]
