from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models import Q
from django.conf import settings

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
        constraints = [
            models.UniqueConstraint(fields=["product", "serial_number"], name="unique_product_serial_number",),
        ]
    def clean(self):
        errors = {}
        if (self.product_id and self.product.tracking_type not in (Product.TrackingType.SERIAL, Product.TrackingType.BATCH_SERIAL,)):
            errors["product"] = "This product is not configured for serial tracking."
        if (self.batch_id and self.product_id and self.batch.product_id != self.product_id):
            errors["batch"] = "Batch must belong to the same product."
        if errors:
            return ValidationError(errors)
    def __str__(self):
        return f"{self.product.code} - {self.serial_number}"
class StockBalance(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_balances",)
    batch = models.ForeignKey(ProductBatch, on_delete=models.PROTECT, related_name="stock_balance", null=True, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"))
    average_cost = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product"], condition=Q(batch__isnull=True), name="unique_product_aggregate_stock_balance"),
            models.UniqueConstraint(
                fields=["product", "batch"],
                condition=Q(batch__isnull=False),
                name="unique_product_batch_stock_balance",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="stock_balance_quantity_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(average_cost__gte=0),
                name="stock_balance_average_cost_nonnegative",
            ),
        ]
    @property
    def stock_value(self):
        return self.quantity * self.average_cost
    def clean(self):
        if self.batch_id and self.product_id:
            if self.batch.product_id != self.product_id:
                raise ValidationError({ "batch":"Batch must belong to the same product." })
    def __str__(self):
        return f"{self.product.code}: {self.quantity}"
class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        RECEIPT = "RECEIPT", "Purchase Receipt"
        SALE = "SALE", "Sale"
        CUSTOMER_RETURN = "CUSTOMER_RETURN", "Customer Return"
        SUPPLIER_RETURN = "SUPPLIER_RETURN", "Supplier Return"
        ISSUE = "ISSUE", "Stock Issue"
        ADJUSTMENT_IN = "ADJUSTMENT_IN", "Positive Adjustment"
        ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Negative Adjustment"
        REVERSAL = "REVERSAL", "Reversal"
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
    movement_type = models.CharField(max_length=25, choices=MovementType.choices)
    transaction_quantity = models.DecimalField(max_digits=18, decimal_places=6, validators=[MinValueValidator(Decimal("0"))])
    transaction_unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="stock_movements")
    conversion_factor = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("1"), validators=[MinValueValidator(Decimal("0.000001"))])
    base_quantity = models.DecimalField(max_digits=18, decimal_places=6, validators=[MinValueValidator(Decimal("0.000001"))])
    batch = models.ForeignKey(ProductBatch, on_delete=models.PROTECT, related_name="stock_movements", null=True, blank=True)
    serial_number = models.ForeignKey(ProductSerialNumber, on_delete=models.PROTECT, related_name="stock_movements", null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"), validators=[MinValueValidator(Decimal("0"))])
    total_cost = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"), validators=[Decimal("0")])
    movement_date = models.DateTimeField()
    source_type = models.CharField(max_length=50, blank=True)
    source_id = models.PositiveBigIntegerField(null=True, blank=True)
    source_line_id = models.PositiveBigIntegerField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    reversal_of = models.ForeignKey("self", on_delete=models.PROTECT, related_name="stock_movements", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_movements", null=True, blank=True)
    class Meta:
        ordering = ["-movement_date", "-id"]
        indexes = [
            models.indexes(fields=["product", "movement_date"]),
            models.indexes(fields=["movement_type", "movement_date"]),
            models.indexes(fields=["source_type", "source_id"]),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(transaction_quantity__gt=0), name="stock_movement_transaction_qty_positive"),
            models.CheckConstraint(condition=Q(base_quantity__gt=0), name="stock_movement_base_qty_positive",),
            models.CheckConstraint(condition=Q(conversion_factor__gt=0), name="stock_movement_conversion_positive",),
            models.CheckConstraint(condition=Q(unit_cost__gte=0), name="stock_movement_unit_cost_nonnegative",),
            models.CheckConstraint(condition=Q(total_cost__gte=0), name="stock_movement_total_cost_nonnegative",),
        ]
    def clean(self):
        errors = {}
        if self.product_id and not self.product.is_stock_tracked:
            errors["product"] = "Cannot move stock for a non-stock product."
        if (self.product_id and self.transaction_unit_id and self.transaction_unit_id != self.product.base_unit_id):
            conversion_exists = ProductUnitConverson.objects.filter(
                product_id=self.product_id, unit_id=self.transaction_unit_id,
            ).exists()
            if not conversion_exists:
                errors["transaction_unit"] = ("No conversion is configured for this product and unit.")
        if (self.batch_id and self.product_id and self.batch.product_id != self.product_id):
            errors["batch"] = "Batch must belong to the same product."
        if (self.serial_number_id and self.product_id and self.serial_number.product_id != self.product_id):
            errors["serial_number"]=("Serial number must belong to the same product.")
        if errors:
            raise ValidationError(errors)
    def __str__(self):
        return (
            f"{self.product.code} - {self.movement_type} "
            f"- {self.base_quantity}"
        )
class StockTake(models.Model):
    class StatusChoices(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        CANCELLED = "CANCELLED", "Cancelled"
    reference = models.CharField(max_length=50, unique=True)
    stock_take_date = models.DateField()
    status = models.CharField(max_length=15, choices=StatusChoices.choices, default=StatusChoices.DRAFT)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stock_take_created", null=True, blank=True)
    class Meta:
        ordering = ["-stock_take_date", "-id"]
    def __str__(self):
        return self.reference
class StockTakeLine(models.Model):
    stock_take = models.ForeignKey(StockTake, on_delete=models.CASCADE, related_name="lines",)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_take_lines",)
    batch = models.ForeignKey(ProductBatch, on_delete=models.PROTECT, related_name="stock_take_lines", null=True, blank=True,)
    expected_quantity = models.DecimalField(max_digits=18, decimal_places=6, validators=[MinValueValidator(Decimal("0"))],)
    counted_quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(Decimal("0"))],)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stock_take", "product"], condition=Q(batch__isnull=True), name="unique_stock_take_product",),
            models.UniqueConstraint(fields=["stock_take", "product", "batch"], condition=Q(batch__isnull=False), name="unique_stock_take_product_batch",),
        ]

    @property
    def variance(self):
        if self.counted_quantity is None:
            return None

        return self.counted_quantity - self.expected_quantity

    def clean(self):
        errors = {}

        if (self.batch_id and self.product_id and self.batch.product_id != self.product_id):
            errors["batch"] = "Batch must belong to the same product."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.stock_take.reference} - {self.product.code}"
        




