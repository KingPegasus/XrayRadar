# Roadmap

This document tracks pending and future features for XrayRadar.

## Pending Features

_Features that are planned but not yet started._

### Authentication & Security

1. **Email verification for newly sign-up users** ✅
   - Verify email addresses during user registration
   - Send verification email with confirmation link
   - Prevent unverified accounts from accessing the platform

2. **Password reset flow**
   - Allow users to reset forgotten passwords
   - Send password reset email with secure token
   - Implement secure password reset endpoint

### Dashboard & Analytics

3. **Dashboard graphs for showing error statistics**
   - Total errors (last 24h / 7d / 30d)
   - Unique issues count
   - Error trend graph (up/down vs previous period)
   - Top 5 errors by frequency

### Notifications

4. **Email alerts for errors** ✅
   - Configure email notifications for error events
   - Set up alerting rules and thresholds
   - Send email notifications when errors occur

### Usage & Limits

5. **Usage limiting for events stored per basic or free account** ✅
   - Implement event storage limits for free/basic tiers
   - Track event count per account (all event levels: error, warning, info, debug)
   - Enforce limits and notify users when approaching limits

## Future Features

_Features that are under consideration for future releases._

---

## Notes

- Features are organized by priority and status
- Add new items with a brief description and any relevant context
- Mark items as completed by moving them to a "Completed" section or removing them
