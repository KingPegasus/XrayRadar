from __future__ import annotations

from datetime import datetime


def _safe_logo_url(base_url: str) -> str | None:
    base = (base_url or "").strip().rstrip("/")
    if not (base.startswith("http://") or base.startswith("https://")):
        return None
    # Don't embed logo for localhost — recipients can't load it; avoids broken image in email
    lower = base.lower()
    if "localhost" in lower or "127.0.0.1" in lower:
        return None
    return f"{base}/logo.svg"


def _shell(*, title: str, body_html: str, cta_text: str, cta_href: str, base_url: str) -> str:
    logo_url = _safe_logo_url(base_url)
    logo_html = (
        f'<div style="margin-bottom:16px;"><img src="{logo_url}" alt="XrayRadar" width="160" '
        'style="display:block;border:0;outline:none;text-decoration:none;" /></div>'
        if logo_url
        else ""
    )
    return (
        '<div style="background:#0b1220;padding:24px;color:#e2e8f0;font-family:Inter,Arial,sans-serif;">'
        '<div style="max-width:620px;margin:0 auto;background:#111827;border:1px solid #1f2937;'
        'border-radius:14px;padding:24px;">'
        f"{logo_html}"
        f'<h2 style="margin:0 0 12px 0;font-size:20px;line-height:1.3;color:#f8fafc;">{title}</h2>'
        f'{body_html}'
        f'<div style="margin-top:18px;"><a href="{cta_href}" '
        'style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;'
        'padding:10px 14px;border-radius:10px;font-weight:600;">'
        f"{cta_text}</a></div>"
        "</div></div>"
    )


def render_error_digest_email(
    *,
    base_url: str,
    project_name: str,
    project_id: int,
    environment: str | None,
    window_start: datetime | None,
    window_end: datetime,
    issues: list[dict],
) -> tuple[str, str]:
    env = (environment or "").strip()
    env_subject = f" [{env}]" if env else ""
    subject = f"[XrayRadar]{env_subject} {project_name}: Error digest"
    issues_href = f"{base_url.rstrip('/')}/dashboard/projects/{project_id}/issues"
    if env:
        issues_href += f"?environment={env}"
    start_label = window_start.isoformat(sep=" ", timespec="seconds") if window_start else "first alert window"
    end_label = window_end.isoformat(sep=" ", timespec="seconds")
    rows = ""
    for item in issues:
        count = int(item.get("count") or 0)
        msg = str(item.get("latest_message") or "").strip() or "No message"
        latest_ts = item.get("latest_timestamp")
        if latest_ts is not None and isinstance(latest_ts, datetime):
            time_label = latest_ts.isoformat(sep=" ", timespec="seconds")
        else:
            time_label = "—"
        rows += (
            '<tr>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #243042;color:#bfdbfe;">{count}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #243042;color:#e2e8f0;">{time_label}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #243042;color:#cbd5e1;">{msg}</td>'
            "</tr>"
        )
    if not rows:
        rows = '<tr><td colspan="3" style="padding:10px;color:#94a3b8;">No issues found in this window.</td></tr>'

    body = (
        f'<p style="margin:0 0 10px;color:#cbd5e1;">Digest window: <b>{start_label}</b> to <b>{end_label}</b>.</p>'
        + (f'<p style="margin:0 0 14px;color:#cbd5e1;">Environment scope: <b>{env}</b>.</p>' if env else "")
        + '<table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;'
        'background:#0f172a;border-radius:10px;overflow:hidden;">'
        '<thead><tr><th style="text-align:left;padding:8px 10px;color:#93c5fd;">Count</th>'
        '<th style="text-align:left;padding:8px 10px;color:#93c5fd;">Latest at</th>'
        '<th style="text-align:left;padding:8px 10px;color:#93c5fd;">Latest message</th></tr></thead>'
        f"<tbody>{rows}</tbody></table>"
    )
    return subject, _shell(
        title=f"Error digest for {project_name}",
        body_html=body,
        cta_text="View issues",
        cta_href=issues_href,
        base_url=base_url,
    )


def render_verification_email(*, base_url: str, token: str) -> tuple[str, str]:
    link = f"{base_url.rstrip('/')}/verify-email?token={token}"
    subject = "[XrayRadar] Verify your email address"
    body = (
        '<p style="margin:0 0 12px;color:#cbd5e1;">Welcome to XrayRadar. Confirm your email to activate your account.</p>'
        '<p style="margin:0;color:#94a3b8;">This link expires in 24 hours.</p>'
    )
    return subject, _shell(
        title="Verify your email",
        body_html=body,
        cta_text="Verify email",
        cta_href=link,
        base_url=base_url,
    )


def render_post_verification_getting_started_email(*, base_url: str) -> tuple[str, str]:
    dashboard_url = f"{base_url.rstrip('/')}/dashboard"
    projects_url = f"{base_url.rstrip('/')}/dashboard/projects"
    tokens_url = f"{base_url.rstrip('/')}/dashboard/tokens"
    subject = "[XrayRadar] Getting started in 3 steps"
    body = (
        '<p style="margin:0 0 12px;color:#cbd5e1;">Your email is verified. You are ready to start tracking errors.</p>'
        '<ol style="margin:0 0 12px 18px;color:#cbd5e1;">'
        '<li style="margin-bottom:6px;">Create your first project.</li>'
        '<li style="margin-bottom:6px;">Request an API token from your admin.</li>'
        '<li style="margin-bottom:6px;">Grant token access to your project from the Tokens page.</li>'
        '</ol>'
        f'<p style="margin:0;color:#94a3b8;">Projects: <a href="{projects_url}" style="color:#93c5fd;">{projects_url}</a></p>'
        f'<p style="margin:6px 0 0;color:#94a3b8;">Tokens: <a href="{tokens_url}" style="color:#93c5fd;">{tokens_url}</a></p>'
    )
    return subject, _shell(
        title="Set up XrayRadar",
        body_html=body,
        cta_text="Open dashboard",
        cta_href=dashboard_url,
        base_url=base_url,
    )


def render_password_reset_email(*, base_url: str, token: str) -> tuple[str, str]:
    link = f"{base_url.rstrip('/')}/reset-password?token={token}"
    subject = "[XrayRadar] Reset your password"
    body = (
        '<p style="margin:0 0 12px;color:#cbd5e1;">A password reset was requested for your XrayRadar account.</p>'
        '<p style="margin:0;color:#94a3b8;">This link expires in 1 hour.</p>'
    )
    return subject, _shell(
        title="Reset your password",
        body_html=body,
        cta_text="Reset password",
        cta_href=link,
        base_url=base_url,
    )


def render_team_invite_email(*, base_url: str, invite_token: str, inviter_email: str) -> tuple[str, str]:
    link = f"{base_url.rstrip('/')}/accept-invite?token={invite_token}"
    subject = "You're invited to join a team on XrayRadar"
    body = (
        f'<p style="margin:0 0 12px;color:#cbd5e1;"><b>{inviter_email}</b> invited you to collaborate in XrayRadar.</p>'
        '<p style="margin:0;color:#94a3b8;">This invite expires in 7 days.</p>'
    )
    return subject, _shell(
        title="Team invite",
        body_html=body,
        cta_text="Accept invite",
        cta_href=link,
        base_url=base_url,
    )
