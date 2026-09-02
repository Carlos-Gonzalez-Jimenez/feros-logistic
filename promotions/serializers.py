from rest_framework import serializers
from promotions import models
from user.serializers import UserSerializer
from core import models as core_models
from core import serializers as core_serializers


class CouponSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Returns:
        _type_: _description_
    """

    is_valid = serializers.SerializerMethodField()
    validity_message = serializers.SerializerMethodField()

    # applicable_categories = core_serializers.CategorySerializer(many=True, read_only=True)
    # applicable_categories_ids = serializers.PrimaryKeyRelatedField(
    #     required=False,
    #     queryset=core_models.Category.objects.filter(active=True),
    #     source="applicable_categories",
    # )
    # applicable_products = core_serializers.ProductReadMinimalSerializer(many=True, read_only=True)
    # applicable_products_ids = serializers.PrimaryKeyRelatedField(
    #     required=False,
    #     queryset=core_models.Product.objects.filter(active=True),
    #     source="applicable_products",
    # )

    class Meta:
        model = models.Coupon
        exclude = ["users_used"]
        read_only_fields = [
            "uses_count",
            "created_at",
            "updated_at",
            "applicable_products",
            "applicable_categories",
        ]

    def get_is_valid(self, obj) -> bool:
        is_valid, _ = obj.is_valid()
        return is_valid

    def get_validity_message(self, obj) -> str:
        _, message = obj.is_valid()
        return message

class CouponUsageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    order = core_serializers.OrderMinimalSerializer(read_only=True)

    class Meta:
        model = models.CouponUsage
        fields = ["id", "coupon", "user", "order", "discount_amount", "used_at"]


class CouponAssignmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=models.User.objects.all(),
        source="user",
    )

    class Meta:
        model = models.CouponAssignment
        fields = [
            "id",
            "user_id",
            "user",
            "assigned_at",
            "assigned_type",
            "used",
            "used_at",
            "notes",
        ]


class ClientCouponAssignmentSerializer(serializers.ModelSerializer):
    coupon = CouponSerializer(read_only=True)

    class Meta:
        model = models.CouponAssignment
        fields = [
            "id",
            "coupon",
            "assigned_at",
            "assigned_type",
            "used",
            "used_at",
            "notes",
        ]
