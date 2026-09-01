from rest_framework import serializers
from .models import NominalAccount, AccountType, Journal, JournalLine
from apps.settings_app.models import FinancialPeriod

class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = (
            "id",
            "code",
            "name",
            "description",
            "category",
            "normal_balance",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )
class AccountTypeCreateUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=AccountType.CategoryChoices)
    normal_balance = serializers.ChoiceField(choices=AccountType.NorminalBalanceChoices)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate_code(self, value):
        value = value.strip().upper()
        queryset = AccountType.objects.filter(code=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("An account type with this code already exists.")
        return value

    def validate_name(self, value):
        value = value.strip()
        queryset = AccountType.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("An account type with this name already exists.")
        return value

    def validate(self, attrs):
        category = attrs.get("category")
        normal_balance = attrs.get("normal_balance")
        debit_categories = { AccountType.CategoryChoices.ASSET, AccountType.CategoryChoices.EXPENSE }
        credit_categories = { AccountType.CategoryChoices.LIABILITY, AccountType.CategoryChoices.EQUITY, AccountType.CategoryChoices.REVENUE }
        if (category in debit_categories and normal_balance != AccountType.NorminalBalanceChoices.DEBIT):
            raise serializers.ValidationError({ "normal_balance":"Asset and Expense accounts must have a debit normal balance." })
        if (category in credit_categories and normal_balance != AccountType.NorminalBalanceChoices.CREDIT):
            raise serializers.ValidationError({ "normal_balance":"Liability, Equity and Revenue accounts must have a credit normal balance." })
        return attrs
class NominalAccountSerializer(serializers.ModelSerializer):
    account_type_name = serializers.CharField(source="account_type.name", read_only=True)
    account_type_category = serializers.CharField(source="account_type.category", read_only=True)
    normal_balance = serializers.CharField(source="account_type.normal_balance", read_only=True)
    parent_name = serializers.CharField(source="parent.name", read_only=True, allow_null=True)
    class Meta:
        model = NominalAccount
        fields = (
            "id",
            "code",
            "name",
            "description",
            "account_type",
            "account_type_name",
            "account_type_category",
            "normal_balance",
            "parent",
            "parent_name",
            "is_control_account",
            "is_posting_account",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "account_type_name",
            "account_type_category",
            "normal_balance",
            "parent_name",
            "created_at",
            "updated_at",
        )
class NominalAccountCreateUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(required=False, allow_blank=True)
    account_type = serializers.PrimaryKeyRelatedField(queryset=AccountType.objects.filter(is_active=True))
    parent = serializers.PrimaryKeyRelatedField(queryset=NominalAccount.objects.filter(is_active=True).all(), required=False, allow_null=True)
    is_control_account = serializers.BooleanField(required=False, default=False)
    is_posting_account = serializers.BooleanField(required=False, default=True)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        parent = attrs.get("parent")
        if (self.instance and parent and parent.pk == self.instance.pk):
            raise serializers.ValidationError({ "parent": "An account cannot be its own parent." })
        return attrs
class JournalLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalLine
        fields = (
            "id",
            "nominal_account",
            "description",
            "debit",
            "credit",
        )
        read_only_fields = (
            "id",
        )

    def validate(self, attrs):
        debit = attrs.get("debit", 0)
        credit = attrs.get("credit", 0)

        if debit > 0 and credit > 0:
            raise serializers.ValidationError({ "detail": ("A journal line cannot have both debit and credit.") })

        if debit == 0 and credit == 0:
            raise serializers.ValidationError({ "detail": ("A journal line must have either a debit or a credit amount.") })

        return attrs
class JournalSerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)

    class Meta:
        model = Journal
        fields = (
            "id",
            "journal_number",
            "transaction_date",
            "description",
            "reference",
            "status",
            "financial_period",
            "created_by",
            "posted_at",
            "posted_by",
            "reversed_journal",
            "lines",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "journal_number",
            "status",
            "created_by",
            "posted_at",
            "posted_by",
            "reversed_journal",
            "created_at",
            "updated_at",
            "lines",
        )
class JournalCreateSerializer(serializers.Serializer):
    transaction_date = serializers.DateField()
    description = serializers.CharField(max_length=255,)
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True,)
    financial_period = serializers.PrimaryKeyRelatedField(queryset=FinancialPeriod.objects.all(),)
    lines = JournalLineSerializer(many=True,)

    def validate_lines(self, lines):
        if len(lines) < 2:
            raise serializers.ValidationError("A journal must contain at least two lines.")

        total_debit = sum(line.get("debit", 0) for line in lines)
        total_credit = sum(line.get("credit", 0) for line in lines)

        if total_debit != total_credit:
            raise serializers.ValidationError("Total debit must equal total credit.")

        return lines

    def validate(self, attrs):
        transaction_date = attrs.get("transaction_date")
        financial_period = attrs.get("financial_period")

        if transaction_date < financial_period.start_date:
            raise serializers.ValidationError({ "transaction_date": ("Transaction date cannot be before the financial period start date.") })

        if transaction_date > financial_period.end_date:
            raise serializers.ValidationError({ "transaction_date": ("Transaction date cannot be after the financial period end date.") })

        return attrs


