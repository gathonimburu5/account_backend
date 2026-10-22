from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models import Q

class Category(models.Model):
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"
    def __str__(self):
        return f"{self.name} - {self.code}"
class UnitOfMeasure(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=30, blank=True)
    decimal_places = models.PositiveSmallIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["name"]
        constraints = [models.CheckConstraint(condition=Q(decimal_places__lte=6), name="unit_decimal_places_max_six")]
    def __str__(self):
        return f"{self.name} ({self.symbol})" if self.symbol else self.name
class Product(models.Model):
    class TrackingType(models.TextChoices):
        NONE = "NONE", "No Tracking"
        BATCH = "BATCH", "Batch / Lot Tracking"
        SERIAL = "SERIAL", "Serial Number Tracking"
        BATCH_SERIAL = "BATCH_SERIAL", "Batch and Serial Tracking"

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    base_unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="base_unit_products")
    is_active = models.BooleanField(default=True)
    is_stock_tracked = models.BooleanField(default=True)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])
    tracking_type = models.CharField(max_length=20, choices=TrackingType.choices, default=TrackingType.NONE)
    purchase_price = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])
    selling_price = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])
    product_image = models.ImageField(upload_to="products/", blank=True, null=True)
    lead_time_days = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=Q(reorder_level__gte=0), name="product_reorder_nonnegative",),
            models.CheckConstraint(condition=Q(purchase_price__gte=0), name="product_purchase_price_nonnegative",),
            models.CheckConstraint(condition=Q(selling_price__gte=0), name="product_selling_price_nonnegative",)
        ]
    def clean(self):
        errors = {}
        if (not self.is_stock_tracked and self.tracking_type != self.TrackingType.NONE):
            errors["tracking_type"]="Non-stock products cannot use inventory tracking."
        if self.category_id and not self.category.is_active:
            errors["category"]="Select an active category."
        if self.base_unit_id and not self.base_unit.is_active:
            errors["base_unit"] = "Select an active unit."
        if errors:
            raise ValidationError(errors)
    def __str__(self):
        return f"{self.code} - {self.name}"
class ProductUnitConverson(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="unit_conversions")
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="product_conversions")
    conversion_factor = models.DecimalField(max_digits=18, decimal_places=6, validators=[MinValueValidator(Decimal("0.000001"))])
    use_for_purchase = models.BooleanField(default=True)
    use_for_sale = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["product__name", "unit__name"]
        constraints = [
            models.UniqueConstraint(fields=["product", "unit"], name="unique_product_unit_conversion"),
            models.CheckConstraint(condition=Q(conversion_factor__gt=0), name="product_conversion_factor_positive",),
            models.CheckConstraint(condition=Q(use_for_purchase=True) | Q(use_for_sale=True), name="product_conversion_has_usage",),
        ]
    def clean(self):
        errors = {}
        if (self.product_id and self.unit_id and self.product.base_unit_id == self.unit_id):
            errors["unit"] = "The base unit does not require a conversion record."
        if self.product_id and not self.product.is_stock_tracked:
            errors["product"]=("Unit conversions are only required for stock-tracked products.")
        if self.unit_id and not self.unit.is_active:
            errors["unit"] = "Select an active unit."
        if not self.use_for_purchase and not self.use_for_sale:
            errors["use_for_purchase"]=("Enable purchasing, selling, or both.")
        if errors:
            raise ValidationError(errors)
    def __str__(self):
        if not self.product_id or not self.unit_id:
            return f"Conversion {self.pk or 'new'}"
        return (
            f"1 {self.unit.name} = {self.conversion_factor} "
            f"{self.product.base_unit.name} "
            f"({self.product.name})"
        )
class ProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="batches",)
    batch_number = models.CharField(max_length=100)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["product__name", "batch_number"]
        constraints = [
            models.UniqueConstraint(fields=["product", "batch_number"], name="unique_product_batch_number",),
        ]
    def clean(self):
        if (self.manufacture_date and self.expiry_date and self.expiry_date < self.manufacture_date):
            raise ValidationError({ "expiry_date":"Expiry date cannot precede manufacture date." })
        if (self.product_id and self.product.tracking_type not in (self.product.TrackingType.BATCH, self.product.TrackingType.BATCH_SERIAL)):
            raise ValidationError({ "product":"This product is not configured for batch tracking." })
    def __str__(self):
        return f"{self.product.code} - {self.batch_number}"
class ProductSerialNumber(models.Model):
    class StatusChoices(models.TextChoices):
        IN_STOCK = "IN_STOCK", "In Stock"
        SOLD = "SOLD", "Sold"
        ISSUED = "ISSUED", "Issued"
        RETURNED = "RETURNED", "Returned"
        DAMAGED = "DAMAGED", "Damaged"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="serial_numbers")
    batch = models.ForeignKey(ProductBatch, on_delete=models.PROTECT, related_name="serial_numbers")
    serial_number = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.IN_STOCK)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["product__name", "serial_number"]
        




