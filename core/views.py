from decimal import Decimal
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Harvest, IoTReading, Approval, Payment, AuditLog, Profile
from .abac import (
    can_submit_harvest,
    can_approve_harvest,
    can_reject_harvest,
    can_release_payment,
)


def home(request):
    return JsonResponse({"message": "SmartFarmChain API is running"})


@api_view(['GET'])
def dashboard_summary(request):
    total_harvests = Harvest.objects.count()
    approved_harvests = Harvest.objects.filter(approval_status='APPROVED').count()
    flagged_records = Harvest.objects.filter(suspicious_flag=True).count()
    payments_released = Payment.objects.filter(payment_status='RELEASED').count()

    return Response({
        "total_harvests": total_harvests,
        "approved_harvests": approved_harvests,
        "flagged_records": flagged_records,
        "payments_released": payments_released,
    })


@api_view(['GET', 'POST'])
def harvest_list_create(request):
    if request.method == 'GET':
        harvests = Harvest.objects.all().order_by('-id').values()
        return Response(list(harvests))

    if not can_submit_harvest(request.user):
        return Response({"error": "RBAC/ABAC denied harvest submission"}, status=403)

    data = request.data

    harvest = Harvest.objects.create(
        farmer=request.user if request.user.is_authenticated else None,
        batch_id=data.get('batch_id'),
        farm_name=data.get('farm_name'),
        crop_type=data.get('crop_type'),
        harvest_weight_kg=Decimal(str(data.get('harvest_weight_kg', 0))),
        harvest_date=data.get('harvest_date'),
        field_location=data.get('field_location'),
        approval_status='PENDING',
        payment_status='PENDING',
        suspicious_flag=False,
    )

    IoTReading.objects.create(
        harvest=harvest,
        temperature=data.get('temperature') or None,
        humidity=data.get('humidity') or None,
        soil_moisture=data.get('soil_moisture') or None,
        ndvi=data.get('ndvi') or None,
        anomaly_flag=False,
    )

    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action='CREATE_HARVEST',
        entity_type='Harvest',
        entity_id=str(harvest.id),
        result='SUCCESS',
        details={"batch_id": harvest.batch_id},
    )

    return Response({"message": "Harvest created", "id": harvest.id}, status=201)


@api_view(['POST'])
def approve_harvest(request, id):
    try:
        harvest = Harvest.objects.get(id=id)
    except Harvest.DoesNotExist:
        return Response({"error": "Harvest not found"}, status=404)

    if not can_approve_harvest(request.user, harvest):
        return Response({"error": "RBAC/ABAC denied approval"}, status=403)

    harvest.approval_status = 'APPROVED'
    harvest.payment_status = 'READY'
    harvest.save()

    Approval.objects.create(
        harvest=harvest,
        approved_by=request.user if request.user.is_authenticated else None,
        approval_action='APPROVED',
        notes=request.data.get('notes', '')
    )

    Payment.objects.get_or_create(
        harvest=harvest,
        defaults={
            "amount": Decimal("250.00"),
            "payment_status": "READY",
            "wallet_address": request.data.get("wallet_address", "")
        }
    )

    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action='APPROVE_HARVEST',
        entity_type='Harvest',
        entity_id=str(harvest.id),
        result='SUCCESS',
        details={"batch_id": harvest.batch_id},
    )

    return Response({"message": "Harvest approved"})


@api_view(['POST'])
def reject_harvest(request, id):
    try:
        harvest = Harvest.objects.get(id=id)
    except Harvest.DoesNotExist:
        return Response({"error": "Harvest not found"}, status=404)

    if not can_reject_harvest(request.user, harvest):
        return Response({"error": "RBAC/ABAC denied rejection"}, status=403)

    harvest.approval_status = 'REJECTED'
    harvest.payment_status = 'BLOCKED'
    harvest.save()

    Approval.objects.create(
        harvest=harvest,
        approved_by=request.user if request.user.is_authenticated else None,
        approval_action='REJECTED',
        notes=request.data.get('notes', '')
    )

    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action='REJECT_HARVEST',
        entity_type='Harvest',
        entity_id=str(harvest.id),
        result='SUCCESS',
        details={"batch_id": harvest.batch_id},
    )

    return Response({"message": "Harvest rejected"})


@api_view(['POST'])
def release_payment(request, id):
    try:
        harvest = Harvest.objects.get(id=id)
    except Harvest.DoesNotExist:
        return Response({"error": "Harvest not found"}, status=404)

    if not can_release_payment(request.user, harvest):
        return Response({"error": "RBAC/ABAC denied payment release"}, status=403)

    payment, _ = Payment.objects.get_or_create(
        harvest=harvest,
        defaults={
            "amount": Decimal("250.00"),
            "payment_status": "PENDING",
            "wallet_address": request.data.get("wallet_address", "")
        }
    )

    payment.payment_status = "RELEASED"
    payment.transaction_hash = request.data.get("transaction_hash", "mock_tx_hash")
    payment.released_at = timezone.now()
    payment.save()

    harvest.payment_status = "RELEASED"
    harvest.save()

    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action='RELEASE_PAYMENT',
        entity_type='Payment',
        entity_id=str(payment.id),
        result='SUCCESS',
        details={"harvest_id": harvest.id},
    )

    return Response({"message": "Payment released"})


@api_view(['GET'])
def iot_list(request):
    readings = IoTReading.objects.all().order_by('-id').values()
    return Response(list(readings))


@api_view(['GET'])
def ai_risk_list(request):
    flagged = Harvest.objects.all().order_by('-id').values(
        'id', 'batch_id', 'approval_status', 'payment_status', 'suspicious_flag'
    )
    return Response(list(flagged))


@api_view(['GET'])
def payments_list(request):
    payments = Payment.objects.all().order_by('-id').values()
    return Response(list(payments))


@api_view(['GET'])
def audit_logs_list(request):
    logs = AuditLog.objects.all().order_by('-id').values()
    return Response(list(logs))


@api_view(['POST'])
def save_wallet(request):
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=401)

    wallet_address = request.data.get("wallet_address")
    if not wallet_address:
        return Response({"error": "wallet_address is required"}, status=400)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.wallet_address = wallet_address
    profile.save()

    return Response({"message": "Wallet saved", "wallet_address": wallet_address})