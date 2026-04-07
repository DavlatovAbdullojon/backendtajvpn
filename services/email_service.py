from email.message import EmailMessage
from pathlib import Path
import smtplib

from config import settings
from models import EmailDeliveryStatus, Receipt, UserDevice


def send_receipt_email(
    *,
    device: UserDevice,
    receipt: Receipt,
    summary_lines: list[str],
) -> tuple[EmailDeliveryStatus, str]:
    if not settings.smtp_host or not settings.admin_email:
        return EmailDeliveryStatus.SKIPPED, "SMTP is not configured"

    message = EmailMessage()
    message["Subject"] = f"[{settings.app_name}] New receipt #{receipt.id} from {device.device_id}"
    message["From"] = settings.mail_from
    message["To"] = settings.admin_email
    message.set_content("\n".join(summary_lines))

    attachment_path = Path(receipt.file_path)
    with attachment_path.open("rb") as file_handle:
        message.add_attachment(
            file_handle.read(),
            maintype="application",
            subtype="octet-stream",
            filename=receipt.original_file_name,
        )

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
    except Exception as exc:
        return EmailDeliveryStatus.FAILED, str(exc)

    return EmailDeliveryStatus.SENT, "Notification email sent"
