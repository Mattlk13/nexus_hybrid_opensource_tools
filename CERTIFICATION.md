# NEXUS resumed certification — 2026-10-16

Decision: **HOLD**. No production deployment, merge, release publication or service purchase.

## Resumed certification results

- PASS: authenticated live notification retrieval through this adapter and the existing Mattlk13 GitHub CLI session. API snapshot counted 5000 unread entries; this is a best-effort API snapshot, not a guarantee of historical completeness. No token value was extracted or printed.
- PASS: live subscribe operation on a notification for nexus_hybrid_devtools draft PR #1, followed by restoration of the exact previous subscribed/ignored state and API readback. No notification was marked read during acceptance.
- PASS: 12 Python tests cover read/write schemas, identity, repository scope, duplicate mark-read, failure readback, authentication/permission/timeout failures and subscription rollback after an ambiguous write timeout.
- Implemented engine methods: manage_notification_thread and rollback_notification_subscription. Mark-read has no documented inverse and explicitly returns rollback_supported=False. Subscription operations preserve a restore receipt. No bulk notification mutation is performed.
- OPEN SECURITY BLOCKER: the semantic-release lockfile still has the previously documented unpatched braces advisory. Security gate remains enabled; no bypass or false certification.
- Current-head CI remains required; hosted jobs are queued.

## Earlier evidence (historical)

# NEXUS certification evidence — 2026-10-16

Decision: **HOLD**. Draft PR #1; no merge, production deployment, service purchase, or publication authorized by this evidence.

5 Python tests pass locally. The real semantic-release 25.0.9 isolated local bare-repository fixture computed 1.1.0 from a conventional feat commit; both local and remote tags remained v1.0.0. The upstream dry-run log says Published release even though no publish plugin runs; tag readback confirms no release was published.
Release adapter is preview-only and never returns version_released. Operator must select a trusted checkout; release configurations/plugins execute code. Notification adapter authenticates identity, reads paginated GitHub unread notifications, rejects malformed/duplicate evidence, and performs no mark-read mutations. Mock identity/notification tests pass; live token adapter acceptance remains unverified.
SECURITY BLOCKER: npm audit reports 7 High package entries stemming from braces <=3.0.3, GHSA-vfj7-8cjw-p6xm / CVE-2026-93687. The reviewed advisory lists no patched version. Do not apply the suggested major downgrade automatically. Audit CI remains a blocking failure until a reviewed fix or replacement removes the affected dependency. No advisory suppression was added.
Source: https://github.com/advisories/GHSA-vfj7-8cjw-p6xm

## Reproduce

`python -m unittest discover -v -p 'test_*.py'`

GitHub Actions runs on the PR branch with contents:read and a bounded job timeout. Review current-head Actions results; prior passing commits are not substitutes for current-head evidence. No tests against live Sentry/Jenkins or a production environment were executed.
