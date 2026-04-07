from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from models import AccessStatus, PaymentStatus


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DeviceInitRequest(ApiModel):
    device_id: str = Field(..., alias="deviceId", min_length=8, max_length=128)
    platform: str = "android"
    app_version: str | None = Field(default=None, alias="appVersion")
    device_model: str | None = Field(default=None, alias="deviceModel")


class DeviceInitResponse(ApiModel):
    device_id: str = Field(..., alias="deviceId")
    access_status: AccessStatus = Field(..., alias="accessStatus")
    vpn_allowed: bool = Field(..., alias="vpnAllowed")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")


class TariffPlanResponse(ApiModel):
    id: str
    title: str
    description: str
    amount_rub: int = Field(..., alias="amountRub")
    duration_days: int = Field(..., alias="durationDays")
    is_featured: bool = Field(..., alias="isFeatured")


class PaymentCreateRequest(ApiModel):
    device_id: str = Field(..., alias="deviceId", min_length=8, max_length=128)
    plan_id: str = Field(..., alias="planId")


class PaymentCreateResponse(ApiModel):
    payment_id: str = Field(..., alias="paymentId")
    device_id: str = Field(..., alias="deviceId")
    plan_id: str = Field(..., alias="planId")
    amount_rub: int = Field(..., alias="amountRub")
    status: PaymentStatus
    payment_url: str | None = Field(default=None, alias="paymentUrl")
    provider_invoice_id: str | None = Field(default=None, alias="providerInvoiceId")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")


class PaymentStatusResponse(ApiModel):
    payment_id: str = Field(..., alias="paymentId")
    device_id: str = Field(..., alias="deviceId")
    plan_id: str = Field(..., alias="planId")
    amount_rub: int = Field(..., alias="amountRub")
    status: PaymentStatus
    payment_url: str | None = Field(default=None, alias="paymentUrl")
    provider_invoice_id: str | None = Field(default=None, alias="providerInvoiceId")
    paid_at: datetime | None = Field(default=None, alias="paidAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    access_status: AccessStatus = Field(..., alias="accessStatus")
    vpn_allowed: bool = Field(..., alias="vpnAllowed")
    message: str


class ENOTWebhookPayload(ApiModel):
    invoice_id: str = Field(..., alias="invoice_id")
    order_id: str = Field(..., alias="order_id")
    amount: float
    currency: str
    status: str
    credited: str | float | int | None = None
    shop_id: str = Field(..., alias="shop_id")
    hook_id: str | None = Field(default=None, alias="hook_id")
    type: int | None = None
    custom_fields: dict[str, Any] | None = Field(default=None, alias="custom_fields")


class SubscriptionStatusResponse(ApiModel):
    device_id: str = Field(..., alias="deviceId")
    access_status: AccessStatus = Field(..., alias="accessStatus")
    vpn_allowed: bool = Field(..., alias="vpnAllowed")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    tariff_plan_id: str | None = Field(default=None, alias="tariffPlanId")
    tariff_plan_title: str | None = Field(default=None, alias="tariffPlanTitle")
    message: str


class ServerResponse(ApiModel):
    id: str
    country: str
    country_code: str = Field(..., alias="countryCode")
    city: str
    host: str
    is_online: bool = Field(..., alias="isOnline")
    load_percent: int = Field(..., alias="loadPercent")


class VpnSessionRequest(ApiModel):
    device_id: str = Field(..., alias="deviceId")
    server_id: str = Field(..., alias="serverId")


class VpnSessionResponse(ApiModel):
    session_id: str = Field(..., alias="sessionId")
    server_id: str = Field(..., alias="serverId")
    server_host: str = Field(..., alias="serverHost")
    server_country: str = Field(..., alias="serverCountry")
    server_city: str = Field(..., alias="serverCity")
    auth_token: str = Field(..., alias="authToken")
    dns_servers: list[str] = Field(..., alias="dnsServers")
    mtu: int
