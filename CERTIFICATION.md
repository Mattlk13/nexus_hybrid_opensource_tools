# NEXUS resumed certification — 2026-10-16

Decision: **HOLD**. No production deployment, merge, release publication or service purchase.

## Latest verification — 2026-10-17 UTC

- REMEDIATED in this branch: removed the vulnerable Node semantic-release 25.0.9 dependency graph, including braces. Replaced it with pinned Python Semantic Release 10.7.0 for non-publishing version previews. This is a backend change: Node release plugins/configuration are no longer executed or supported by this adapter.
- PASS locally: all 15 Python tests, including real conventional feature/patch/breaking version calculations (1.1.0, 1.1.1, 2.0.0), repeat preview, dirty-checkout rejection, timeout and changed-state rejection. Local HEAD/refs/worktree are read back; isolated bare-remote refs remain unchanged.
- PASS locally: pip-audit 2.10.1 reports no known vulnerabilities across the pinned replacement environment, including upgraded pip 26.2.1. Raw evidence: verification/release-audit-20261017.json. No suppressions. Advisory state can change; CI audits again.
- Preview uses the current Python interpreter with isolated imports, a fixed temporary configuration, --noop and version --print. Service credentials are not forwarded. Publication remains disabled; next_version is a preview, version_released stays null.
- Current-head GitHub Actions must pass before this change is certified. Historical failures below are retained as history, not current results.

Install with `python -m pip install -r requirements-release.txt`; run `python -m unittest discover -v -p 'test_*.py'` and `python -m pip_audit`.

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
