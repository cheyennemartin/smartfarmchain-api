from django.urls import path
from .views import (
    dashboard_summary,
    harvest_list_create,
    approve_harvest,
    reject_harvest,
    release_payment,
    iot_list,
    ai_risk_list,
    payments_list,
    audit_logs_list,
    save_wallet,
)

urlpatterns = [
    path('dashboard/summary/', dashboard_summary, name='dashboard-summary'),
    path('harvests/', harvest_list_create, name='harvest-list-create'),
    path('harvests/<int:id>/approve/', approve_harvest, name='approve-harvest'),
    path('harvests/<int:id>/reject/', reject_harvest, name='reject-harvest'),
    path('harvests/<int:id>/release-payment/', release_payment, name='release-payment'),
    path('iot/', iot_list, name='iot-list'),
    path('ai-risk/', ai_risk_list, name='ai-risk-list'),
    path('payments/', payments_list, name='payments-list'),
    path('audit-logs/', audit_logs_list, name='audit-logs-list'),
    path('profile/wallet/', save_wallet, name='save-wallet'),
]