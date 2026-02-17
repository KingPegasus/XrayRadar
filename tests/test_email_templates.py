from datetime import datetime, timezone

from xrayradar_server.email_templates import (
    render_error_digest_email,
    render_password_reset_email,
    render_post_verification_getting_started_email,
    render_team_invite_email,
    render_verification_email,
)


def test_render_error_digest_email_with_logo():
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
    assert "logo.svg" in html
    assert "Latest at" in html
    assert "Boom" in html
    assert now.isoformat(sep=" ", timespec="seconds") in html


def test_render_email_templates_without_logo():
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
    assert "logo.svg" not in verify_html
    assert "logo.svg" not in reset_html
    assert "logo.svg" not in onboarding_html
    assert "logo.svg" not in invite_html


def test_render_email_templates_no_logo_for_localhost():
    """localhost / 127.0.0.1 base URLs must not embed logo (recipients cannot load it)."""
    for base in ("http://localhost:8001", "https://localhost", "http://127.0.0.1:8000"):
        _, verify_html = render_verification_email(base_url=base, token="x")
        _, onboarding_html = render_post_verification_getting_started_email(base_url=base)
        assert "logo.svg" not in verify_html, base
        assert "logo.svg" not in onboarding_html, base


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
