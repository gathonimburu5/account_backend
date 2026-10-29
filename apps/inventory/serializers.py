from rest_framework import serializers
from .models import (
    Category,
    UnitOfMeasure,
    Product,
    ProductUnitConverson,
    ProductBatch,
    ProductSerialNumber,
    StockBalance,
    StockMovement,
    StockTake,
    StockTakeLine,
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    base_unit_name = serializers.CharField(source="base_unit.name", read_only=True)
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None),)
        base_unit = attrs.get("base_unit", getattr(self.instance, "base_unit", None),)
        if category and not category.is_active:
            raise serializers.ValidationError({ "category":"Select an active category." })
        if base_unit and not base_unit.is_active:
            raise serializers.ValidationError({ "base_unit":"Select an active unit of measure." })
        return attrs
    
class ProductUnitConversionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True,)
    unit_name = serializers.CharField(source="unit.name", read_only=True)
    base_unit_name = serializers.CharField(source="product.base_unit.name", read_only=True)
    class Meta:
        model = ProductUnitConverson
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")
    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None),)
        unit = attrs.get("unit", getattr(self.instance, "unit", None),)
        if product and not product.is_active:
            raise serializers.ValidationError({ "product":"Select an active product." })
        if unit and not unit.is_active:
            raise serializers.ValidationError({ "unit":"Select an active unit of measure." })
        if product and unit and product.base_unit_id == unit.id:
            raise serializers.ValidationError({ "unit":"The base unit does not need a conversion record." })
        return attrs

class ProductBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True,)
    class Meta:
        model = ProductBatch
        fields = "__all__"
        read_only_fields = ("id",)

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None),)
        if product and product.tracking_type not in (Product.TrackingType.BATCH, Product.TrackingType.BATCH_SERIAL,):
            raise serializers.ValidationError({ "product": "This product does not support batch tracking." })
        return attrs

class ProductSerialNumberSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True,)
    batch_number = serializers.CharField(source="batch.batch_number", read_only=True, allow_null=True,)
    class Meta:
        model = ProductSerialNumber
        fields = "__all__"
        read_only_fields = ("id",)

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None),)
        batch = attrs.get("batch", getattr(self.instance, "batch", None),)
        if product and product.tracking_type not in (Product.TrackingType.SERIAL, Product.TrackingType.BATCH_SERIAL,):
            raise serializers.ValidationError({ "product": "This product does not support serial tracking." })
        if batch and product and batch.product_id != product.id:
            raise serializers.ValidationError({ "batch": "The batch must belong to the selected product." })
        if (product and product.tracking_type == Product.TrackingType.BATCH_SERIAL and not batch):
            raise serializers.ValidationError({ "batch": "A batch is required for this product." })
        return attrs

class StockBalanceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True,)
    base_unit_symbol = serializers.CharField(source="product.base_unit.symbol", read_only=True,)
    stock_value = serializers.DecimalField(max_digits=24, decimal_places=6, read_only=True,)

    class Meta:
        model = StockBalance
        fields = "__all__"
        read_only_fields = fields

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True,)
    unit_name = serializers.CharField(source="unit.name", read_only=True,)
    batch_number = serializers.CharField(source="batch.batch_number", read_only=True, allow_null=True,)
    serial_number_value = serializers.CharField(source="serial.serial_number", read_only=True, allow_null=True,)
    class Meta:
        model = StockMovement
        fields = "__all__"
        read_only_fields = fields

class StockTakeLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True,)
    variance = serializers.DecimalField(max_digits=24, decimal_places=6, read_only=True,)
    class Meta:
        model = StockTakeLine
        fields = "__all__"
        read_only_fields = ("id", "expected_quantity")

class StockTakeSerializer(serializers.ModelSerializer):
    lines = StockTakeLineSerializer(many=True, read_only=True)
    class Meta:
        model = StockTake
        fields = "__all__"
        read_only_fields = ("id", "status", "created_by",)