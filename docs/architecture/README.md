# Architecture

This folder documents the architecture of XrayRadar features. Each document describes a feature area with data flow, components, and diagrams where applicable.

## Contents

| Document | Description |
|----------|-------------|
| [Event ingest](event-ingest.md) | Event storage API, fingerprinting, and persistence |
| [Email alerts](email-alerts.md) | Email notifications for errors via Resend (project owner + additional recipients) |
| [Usage limiting](usage-limiting.md) | Event storage limits per plan tier (Free / Basic / Pro) |
| [Event frequency](event-frequency.md) | 30-day event frequency charts (project and issue views) |

## Diagram format

Diagrams use [Mermaid](https://mermaid.js.org/) syntax (sequence diagrams, flowcharts). They render in GitHub, GitLab, and many Markdown viewers.
