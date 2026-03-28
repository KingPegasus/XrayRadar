from datetime import datetime, timezone

from xrayradar_server.email_templates import (
    render_admin_new_user_email,
    render_admin_token_request_email,
    render_error_digest_email,
    render_password_reset_email,
    render_post_verification_getting_started_email,
    render_team_invite_email,
    render_verification_email,
)


def test_render_error_digest_email_with_png_logo():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    subject, html = render_error_digest_email(
        base_url="https://xrayradar.com",
        project_name="Demo",
        project_id=12,
        environment="production",
        window_start=None,
        window_end=now,
        issues=[{"count": 3, "latest_timestamp": now, "latest_message": "Boom"}],
    )
    assert "Error digest" in subject
    assert "xray-logo.png" in html
    assert "logo.svg" not in html
    assert "Latest at" in html
    assert "Boom" in html
    assert now.isoformat(sep=" ", timespec="seconds") in html


def test_render_email_templates_text_logo_fallback():
    """When base_url is empty, emails use a text-based logo fallback (no external images)."""
    verify_subject, verify_html = render_verification_email(base_url="", token="abc")
    reset_subject, reset_html = render_password_reset_email(base_url="", token="abc")
    onboarding_subject, onboarding_html = render_post_verification_getting_started_email(base_url="")
    invite_subject, invite_html = render_team_invite_email(
        base_url="",
        invite_token="abc",
        inviter_email="owner@example.com",
    )
    assert "Verify" in verify_subject
    assert "Reset" in reset_subject
    assert "Getting started" in onboarding_subject
    assert "invited" in invite_subject
    for html in (verify_html, reset_html, onboarding_html, invite_html):
        assert "xray-logo.png" not in html
        assert "Xray" in html and "Radar" in html


def test_render_email_templates_no_image_for_localhost():
    """localhost / 127.0.0.1 base URLs use text logo (no external image)."""
    for base in ("http://localhost:8001", "https://localhost", "http://127.0.0.1:8000"):
        _, verify_html = render_verification_email(base_url=base, token="x")
        _, onboarding_html = render_post_verification_getting_started_email(base_url=base)
        assert "xray-logo.png" not in verify_html, base
        assert "xray-logo.png" not in onboarding_html, base
        assert "Xray" in verify_html and "Radar" in verify_html


def test_render_post_verification_getting_started_email_content():
    """Onboarding email includes subject, 3 steps, dashboard/projects/tokens URLs and CTA."""
    base = "https://app.example.com"
    subject, html = render_post_verification_getting_started_email(base_url=base)
    assert subject == "[XrayRadar] Getting started in 3 steps"
    assert "Set up XrayRadar" in html
    assert "Your email is verified" in html
    assert "Create your first project" in html
    assert "Request an API token" in html
    assert "Grant token access" in html
    assert f"{base}/dashboard" in html
    assert f"{base}/dashboard/projects" in html
    assert f"{base}/dashboard/tokens" in html
    assert "Open dashboard" in html


def test_render_admin_new_user_email():
    """Admin new-user email includes subject, user email, plan, user ID, signed-up time, and admin dashboard CTA."""
    base = "https://app.example.com"
    signed_up_at = datetime(2025, 3, 7, 12, 0, 0, tzinfo=timezone.utc)
    subject, html = render_admin_new_user_email(
        base_url=base,
        user_email="newuser@example.com",
        plan="Teams",
        user_id=42,
        signed_up_at=signed_up_at,
    )
    assert subject == "[XrayRadar] New user signup"
    assert "New user signup" in html
    assert "newuser@example.com" in html
    assert "Teams" in html
    assert "42" in html
    assert "2025-03-07 12:00:00" in html
    assert f"{base}/admin" in html
    assert "Open admin dashboard" in html
    assert "A new user has signed up" in html


def test_render_admin_token_request_email():
    """Admin token-request email includes subject, user email, name, note, request ID, time, and CTA."""
    base = "https://app.example.com"
    requested_at = datetime(2025, 3, 7, 14, 30, 0, tzinfo=timezone.utc)
    subject, html = render_admin_token_request_email(
        base_url=base,
        user_email="dev@example.com",
        request_name="My SDK token",
        request_note="For production backend",
        request_id=5,
        requested_at=requested_at,
    )
    assert subject == "[XrayRadar] Token request"
    assert "Token request" in html
    assert "dev@example.com" in html
    assert "My SDK token" in html
    assert "For production backend" in html
    assert "5" in html
    assert "2025-03-07 14:30:00" in html
    assert f"{base}/admin#requests" in html
    assert "View token requests" in html
    assert "A user has requested an API token" in html
