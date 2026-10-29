from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.apps import apps
from django.db.models import Q
from apps.inventory.models import (
    Category,
    UnitOfMeasure,
    Product,
    ProductUnitConverson,
    StockBalance,
    StockMovement,
    ProductBatch,
    ProductSerialNumber,
    StockTake,
    StockTakeLine,
)

class InventoryService:
    INBOUND = {
        StockMovement.MovementType.RECEIPT,
        StockMovement.MovementType.CUSTOMER_RETURN,
        StockMovement.MovementType.ADJUSTMENT_IN,
    }
    OUTBOUND = {
        StockMovement.MovementType.SALE,
        StockMovement.MovementType.SUPPLIER_RETURN,
        StockMovement.MovementType.ISSUE,
        StockMovement.MovementType.ADJUSTMENT_OUT,
    }
    BATCH_TRACKED = {
        Product.TrackingType.BATCH,
        Product.TrackingType.BATCH_SERIAL,
    }
    SERIAL_TRACKED = {
        Product.TrackingType.SERIAL,
        Product.TrackingType.BATCH_SERIAL,
    }

    @staticmethod
    def _decimal(value, field="quantity"):
        try:
            result = Decimal(str(value))
        except Exception:
            raise ValidationError({field: "Enter a valid number."})
        if not result.is_finite():
            raise ValidationError({field: "Enter a finite number."})
        return result

    @staticmethod
    def _validate_model(instance):
        instance.full_clean()
        return instance

    @staticmethod
    def _validate_period(movement_date):
        period_model = next(
            (model for model in apps.get_models() if model.__name__ == "FinancialPeriod"), None,
        )
        if period_model is None:
            raise ValidationError("FinancialPeriod model could not be found.")
        movement_day = (
            movement_date.date()
            if hasattr(movement_date, "date") else movement_date
        )
        period = period_model.objects.filter(
            status="ACTIVE",
            start_date__lte=movement_day,
            end_date__lte=movement_day,
        ).first()
        if not period:
            raise ValidationError("No active financial period covers this transaction date.")
        return period

    @staticmethod
    def _validate_accounting_callback(callback, movement):
        if callable is not None:
            callable(movement)

    @staticmethod
    def _get_conversion(product, unit, movement_type):
        if unit.pk == product.base_unit_id:
            return Decimal("1")
        conversion = ProductUnitConverson.objects.filter(product=product, unit=unit, is_active=True).first()
        if not conversion:
            raise ValidationError(f"No active unit conversion exists for {product.name}")
        if (movement_type == StockMovement.MovementType.RECEIPT and not conversion.can_purchase):
            raise ValidationError("Purchases are not allowed in this unit.")
        if (movement_type == StockMovement.MovementType.SALE and not conversion.can_sell):
            raise ValidationError("Sales are not allowed in this unit.")
        return conversion.conversion_factor

    @staticmethod
    def _get_balance(product, batch=None):
        balance, _ = StockBalance.objects.get_or_create(
            product=product,
            batch=batch,
            defaults={
                "quantity": Decimal("0"),
                "averange_cost": Decimal("0")
            }
        )
        return StockBalance.objects.select_for_update().get(pk=balance.pk)

    @staticmethod
    def _validate_tracking(product, batch, serial):
        if product.tracking_type in InventoryService.BATCH_TRACKED:
            if batch is None:
                raise ValidationError("A batch is required for this product.")
        if batch and batch.product_id != product.pk:
            raise ValidationError(" The selected batch belongs to another product. ")
        if product.tracking_type in InventoryService.SERIAL_TRACKED:
            if serial is None:
                raise ValidationError(" A serial number is required for this product. ")
        if serial and serial.product_id != product.pk:
            raise ValidationError(" The selected serial number belongs to another product. ")
        if serial and batch and serial.batch_id != batch.pk:
            raise ValidationError("The serial number does not belong to this batch.")

    @staticmethod
    def get_categories():
        return Category.objects.filter(is_active=True).order_by("code")
    
    @staticmethod
    def get_category(category_id):
        try:
            return Category.objects.filter(pk=category_id, is_active=True)
        except Exception:
            raise ValidationError({ "details":"Category details not found." })

    @staticmethod
    @transaction.atomic
    def create_category(**data):
        category = Category(**data)
        InventoryService._validate_model(category)
        category.save()
        return category

    @staticmethod
    @transaction.atomic
    def update_category(category_id, **data):
        category = Category.objects.select_for_update().get(pk=category_id)
        for field, value in data.items():
            if field not in { "code", "name", "is_active" }:
                raise ValidationError({ field: "This category field cannot be updated here." })
            setattr(category, field, value)
        InventoryService._validate_model(category)
        category.save()
        return category

    @staticmethod
    def get_unit_measures():
        return UnitOfMeasure.objects.filter(is_active=True).order_by("code")
    
    @staticmethod
    def get_unit_measure(unit_id):
        try:
            return UnitOfMeasure.objects.filter(pk=unit_id, is_active=True)
        except Exception:
            raise ValidationError({ "details":"Unit Measure details not found." })

    @staticmethod
    @transaction.atomic
    def create_unit(**data):
        unit = UnitOfMeasure(**data)
        InventoryService._validate_model(unit)
        unit.save()
        return unit

    @staticmethod
    @transaction.atomic
    def update_unit(unit_id, **data):
        unit = UnitOfMeasure.objects.select_for_update().get(pk=unit_id)
        for field, value in data.items():
            if field not in { "code", "name", "symbol", "decimal_places", "is_active" }:
                raise ValidationError({ field: "This unit measure field cannot be updated here." })
            setattr(unit, field, value)
        InventoryService._validate_model(unit)
        unit.save()
        return unit      

    @staticmethod
    def get_products():
        return Product.objects.filter(is_active=True).order_by("code")
    
    @staticmethod
    def get_product(product_id):
        try:
            return Product.objects.filter(pk=product_id, is_active=True)
        except Exception:
            raise ValidationError({ "details":"Product details is not found." })

    @staticmethod
    @transaction.atomic
    def create_product(**data):
        product = Product(**data)
        InventoryService._validate_model(product)
        product.save()
        return product

    @staticmethod
    @transaction.atomic
    def update_product(product_id, **data):
        product = Product.objects.select_for_update().get(pk=product_id)
        if "base_unit" in data:
            if data["base_unit"].pk != product.base_unit_id:
                if StockMovement.objects.filter(product=product).exists():
                    raise ValidationError({ "base_unit":("The base unit cannot change after stock movement exist.") })
        allowed = {
            "code", "name", "description", "category", "base_unit", "is_active", "is_stock_tracked", "reorder_level", "tracking_type",
            "purchase_price", "selling_price", "product_image", "lead_time_days",
        }
        for field, value in data.items():
            if field not in allowed:
                raise ValidationError({ field: "This product field cannot be updated here." })
            setattr(product, field, value)
        InventoryService._validate_model(product)
        product.save()
        return product

    @staticmethod
    @transaction.atomic
    def create_conversion(**data):
        product = data["product"]
        unit = data["unit"]
        if not product.is_active or not unit.is_active:
            raise ValidationError("The product and unit must both be active.")
        if product.base_unit_id == unit.pk:
            raise ValidationError("The base unit does not need a conversion record.")
        conversion = ProductUnitConverson(**data)
        InventoryService._validate_model(conversion)
        conversion.save()
        return conversion

    @staticmethod
    @transaction.atomic
    def update_conversion(conversion_id, **data):
        conversion = ProductUnitConverson.objects.select_for_update().get(pk=conversion_id)
        if StockMovement.objects.filter(product=conversion.product, unit=conversion.unit).exists():
            if ("conversion_factor" in data and 
                InventoryService._decimal(data["conversion_factor"], "conversion_factor") != conversion.conversion_factor):
                raise ValidationError({ "conversion_factor":("htis conversion has historical movements. Create a new unit or use a controlled migration.") })
        allowed = { "conversion_factor", "can_purchase", "can_sell", "is_active" }
        for field, value in data.items():
            if field not in allowed:
                raise ValidationError({ field: "This conversion field cannot be updated here." })
            setattr(conversion, field, value)
        InventoryService._validate_model(conversion)
        conversion.save()
        return conversion

    @staticmethod
    @transaction.atomic
    def create_batch(**data):
        batch = ProductBatch(**data)
        InventoryService._validate_model(batch)
        batch.save()
        return batch

    @staticmethod
    @transaction.atomic
    def update_serial(**data):
        serial = ProductSerialNumber(**data)
        InventoryService._validate_model(serial)
        serial.save()
        return serial

    @staticmethod
    @transaction.atomic
    def _post_movement(*, product_id, movement_type, quantity, unit_id, unit_cost=None, batch_id=None, 
                      serial_id=None, movement_date=None, reference="", notes="", source_type="", source_id=None, 
                      source_line_id=None, created_by=None, reversal_of=None, accounting_callback=None,):
        if movement_type not in (InventoryService.INBOUND | InventoryService.OUTBOUND) and movement_type != "REVERSAL":
            raise ValidationError("Unsupported stock movement type.")
        quantity = InventoryService._decimal(quantity)
        if quantity <= 0:
            raise ValidationError({ "quantity":"Quantity must be greater than zero." })
        movement_date = movement_date or timezone.now()
        InventoryService._validate_period(movement_date)
        product = Product.objects.select_for_update().get(pk=product_id, is_active=True,)
        if not product.is_stock_tracked:
            raise ValidationError("Cannot post stock movements for a non-stock product.")
        if source_type and source_id is not None:
            duplicate = StockMovement.objects.filter(
                source_type=source_type,
                source_id=source_id,
                source_line_id=source_line_id,
                movement_type=movement_type,
            ).exists()
            if duplicate:
                raise ValidationError("This source transaction has already been posted.")

        if reversal_of and StockMovement.objects.filter(reversal_of=reversal_of).exists():
            raise ValidationError("This movement has already been reversed.")
        unit = UnitOfMeasure.objects.get(pk=unit_id, is_active=True)
        batch = (ProductBatch.objects.get(pk=batch_id, product=product) if batch_id else None)
        serial = ( ProductSerialNumber.objects.select_for_update().get(pk=serial_id, product=product) if serial_id else None)
        InventoryService._validate_tracking(product, batch, serial)
        if serial:
            latest = StockMovement.objects.filter(serial=serial).order_by("-movement_date", "-pk").first()
            if movement_type in InventoryService.INBOUND:
                if latest and latest.movement_type not in (InventoryService.OUTBOUND):
                    raise ValidationError("This serial number has already been received.")
            elif movement_type in InventoryService.OUTBOUND:
                if not latest or latest.movement_type not in (InventoryService.INBOUND):
                    raise ValidationError("This serial number is not available in stock.")

        conversion_factor = InventoryService._get_conversion(
            product,
            unit,
            movement_type
        ) if movement_type != "REVERSAL" else Decimal("1")

        base_quantity = quantity * conversion_factor
        balance = InventoryService._get_balance(product)
        batch_balance = (
            InventoryService._get_balance(product, batch) if batch else None
        )
        inbound = movement_type in InventoryService.INBOUND
        outbound = movement_type in InventoryService.OUTBOUND

        if movement_type == "REVERSAL":
            if reversal_of is None:
                raise ValidationError("The original movement is required for a reversal.")
            inbound=reversal_of.movement_type in InventoryService.OUTBOUND
            outbound=reversal_of.movement_type in InventoryService.OUTBOUND
            base_quantity=reversal_of.base_quantity
            quantity=reversal_of.transaction_quantity
            unit=reversal_of.unit
            conversion_factor=reversal_of.conversion_factor
            batch=reversal_of.batch
            serial=reversal_of.serial

        if inbound:
            if unit_cost is None and reversal_of is None:
                raise ValidationError("Unit cost is required for inbound stock.")
            if reversal_of:
                cost_per_base_unit = reversal_of.unit_cost
                total_cost=reversal_of.total_cost
            else:
                unit_cost=InventoryService._decimal(unit_cost, "unit_cost")
                if unit_cost < 0:
                    raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
                cost_per_base_unit = unit_cost / conversion_factor
                total_cost = base_quantity * cost_per_base_unit
            old_value = balance.quantity * balance.average_cost
            new_quantity = balance.quantity + base_quantity

            balance.quantity = new_quantity
            balance.average_cost = (
                (old_value + total_cost) / new_quantity if new_quantity > 0 else Decimal("0")
            )

            if batch_balance:
                old_batch_value = (
                    batch_balance.quantity * batch_balance.average_cost
                )
                batch_balance.quantity += base_quantity
                batch_balance.average_cost = (
                    (old_batch_value + total_cost) / batch_balance.quantity if batch_balance.quantity > 0 else Decimal("0")
                )
        elif outbound:
            if balance.quantity < base_quantity:
                raise ValidationError("Insufficient stock available.")
            if batch_balance and batch_balance.quantity < base_quantity:
                raise ValidationError("Insufficient stock in the selected batch.")
            cost_per_base_unit = (
                reversal_of.unit_cost if reversal_of else balance.average_cost
            )
            total_cost = base_quantity * cost_per_base_unit
            old_value = balance.quantity * balance.average_cost
            balance.quantity -= base_quantity
            new_value = old_value - total_cost
            if balance.quantity == 0:
                balance.average_cost = Decimal("0")
            else:
                balance.average_cost = new_value / balance.quantity

            if batch_balance:
                batch_balance.quantity -= base_quantity
                if batch_balance.quantity == 0:
                    batch_balance.average_cost = Decimal("0")
        else:
            raise ValidationError("Unable to determine movement direction.")

        if balance.quantity < 0:
            raise ValidationError("Stock quantity cannot be negative.")

        balance.save(update_fields=["quantity", "average_cost"])

        if batch_balance:
            batch_balance.save(update_fields=["quantity", "average_cost"])

        movement = StockMovement.objects.create(
            product=product,
            movement_type=movement_type,
            transaction_quantity=quantity,
            unit=unit,
            conversion_factor=conversion_factor,
            base_quantity=base_quantity,
            batch=batch,
            serial=serial,
            unit_cost=cost_per_base_unit,
            total_cost=total_cost,
            movement_date=movement_date,
            reference=reference,
            notes=notes,
            source_type=source_type,
            source_id=source_id,
            source_line_id=source_line_id,
            created_by=created_by,
            reversal_of=reversal_of,            
        )

        if serial:
            serial.status(
                "IN_STOCK" if inbound else
                "SOLD" if movement_type == "SALE" else
                "ISSUED"
            )
            serial.save(update_fields=["satuts"])

        InventoryService._validate_accounting_callback(accounting_callback, movement)

        return movement

    @staticmethod
    def receive_stock(**kwargs):
        return InventoryService._post_movement(movement_type="RECEIPT", **kwargs)
    @staticmethod
    def sell_stock(**kwargs):
        return InventoryService._post_movement(movement_type="SALE", **kwargs)
    @staticmethod
    def return_from_customer(**kwargs):
        return InventoryService._post_movement(movement_type="CUSTOMER_RETURN", **kwargs)
    @staticmethod
    def return_to_supplier(**kwargs):
        return InventoryService._post_movement(movement_type="SUPPLIER_RETURN", **kwargs)
    @staticmethod
    def issue_stock(**kwargs):
        return InventoryService._post_movement(movement_type="ISSUE", **kwargs)
    @staticmethod
    def adjust_stock(*, quantity, **kwargs):
        quantity = InventoryService._decimal(quantity)
        if quantity == 0:
            raise ValidationError("Adjustment quantity cannot be zero.")
        movement_type = ( "ADJUSTMENT_IN" if quantity > 0 else "ADJUSTMENT_OUT" )
        kwargs["quantity"] = abs(quantity)
        return InventoryService._post_movement(movement_type=movement_type, **kwargs)

    @staticmethod
    @transaction.atomic
    def reverse_movement(movement_id, *, reason, created_by=None, accounting_callback=None):
        original = StockMovement.objects.select_for_update().get(pk=movement_id)
        if original.movement_type == "REVERSAL":
            raise ValidationError("A reversal movement cannot itself be reversed.")
        if StockMovement.objects.filter(reversal_of=original).exists():
            raise ValidationError("This movement has already been reversed.")
        return InventoryService._post_movement(
            product_id=original.product_id,
            movement_type="REVERSAL",
            quantity=original.transaction_quantity,
            unit_id=original.unit_id,
            movement_date=timezone.now(),
            reference=original.reference,
            notes=f"Reversal: {reason}",
            created_by=created_by,
            reversal_of=original,
            accounting_callback=accounting_callback
        )

    @staticmethod
    @transaction.atomic
    def create_stock_take(*, reference, lines, notes="", created_by=None,):
        stock_take = StockTake(reference=reference, notes=notes, created_by=created_by,)
        InventoryService._validate_model(stock_take)
        stock_take.save()

        for item in lines:
            product = Product.objects.get(pk=item["product_id"], is_active=True, is_stock_tracked=True,)

            batch = None
            if item.get("batch_id"):
                batch = ProductBatch.objects.get(pk=item["batch_id"], product=product,)

            InventoryService._validate_tracking(product, batch, None)

            balance = InventoryService._get_balance(product, batch)

            line = StockTakeLine(
                stock_take=stock_take,
                product=product,
                batch=batch,
                expected_quantity=balance.quantity,
                counted_quantity=InventoryService._decimal(item["counted_quantity"], "counted_quantity"),
                notes=item.get("notes", ""),
            )

            if line.counted_quantity < 0:
                raise ValidationError("Counted quantity cannot be negative.")

            InventoryService._validate_model(line)
            line.save()

        return stock_take

    @staticmethod
    @transaction.atomic
    def approve_stock_take(stock_take_id, *, created_by=None, accounting_callback=None,):
        stock_take = StockTake.objects.select_for_update().get(pk=stock_take_id)

        if stock_take.status != "DRAFT":
            raise ValidationError("Only draft stock takes can be approved.")

        movements = []

        for line in StockTakeLine.objects.filter(
            stock_take=stock_take
        ).select_related("product", "batch"):
            difference = (line.counted_quantity - line.expected_quantity)
            if difference == 0:
                continue
            product = line.product
            balance = InventoryService._get_balance(product, line.batch)
            movements.append(
                InventoryService.adjust_stock(
                    product_id=product.pk,
                    quantity=difference,
                    unit_id=product.base_unit_id,
                    batch_id=line.batch_id,
                    unit_cost=balance.average_cost,
                    reference=stock_take.reference,
                    notes=f"Stock take variance: {stock_take.reference}",
                    source_type="STOCK_TAKE",
                    source_id=stock_take.pk,
                    source_line_id=line.pk,
                    created_by=created_by,
                    accounting_callback=accounting_callback,
                )
            )

        stock_take.status = "APPROVED"
        stock_take.save(update_fields=["status"])

        return {
            "stock_take": stock_take,
            "movements": movements,
        }
            
        
