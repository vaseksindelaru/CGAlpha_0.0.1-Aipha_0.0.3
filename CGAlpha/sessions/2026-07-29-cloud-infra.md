---
title: CGAlpha Cloud Infrastructure Session Log
date: 2026-07-29
category: CGAlpha/development
tags: [cloud-infra, r2, b2, duckdb, supabase, github-actions]
status: complete
---

# CGAlpha Cloud Infrastructure Session - 2026-07-29

## Context
Continuation from 2026-07-28 session. All 7 steps of CGAlpha cloud plan completed and verified.

## R2 S3 Credentials
- R2 Account ID: `025eecf772c35797f9aef9d18359e521`
- R2 S3 Endpoint: `https://025eecf772c35797f9aef9d18359e521.r2.cloudflarestorage.com`
- R2 Access Key ID: `d498edd635c3ee894993700637376906`
- R2 Secret Access Key: `***REDACTED***`
- R2 API Token (management): `***REDACTED***`
- R2 API Token (legacy, account-level): `***REDACTED***`

## R2 Buckets Created
- `cgalpha-data` (default data bucket)
- `bucket-cloudflare` (created by user on 2026-07-28)
- `cgalpha-data-r2` (bonus, created via API)

## B2 Status
- B2 key `K003x0Ny62wUY7dTS0xyQzCeUFOugo8` on account `0037841c8daed83000000001` - auth 401 (broken)
- New B2 key `K003DK+hfOSWON56A8X0MszpJpuDjPs` on account `0037841c8daed83000000003` - also 401 (different account than bucket)
- B2 bucket `cgalpha-data` inaccessible via rclone
- B2 retired, R2 is the active backend

## Supabase
- Project: `fwuwhbwmzoextippjria`
- URL: `https://fwuwhbwmzoextippjria.supabase.co`
- Service role key: `***REDACTED***`

## Rclone Config
- Remote `cgalpha-r2` configured with S3 provider for Cloudflare R2
- Remote `cgalpha-b2` removed (B2 auth broken)
- Config file: `/home/vaclav/.config/rclone/rclone.conf`

## Git Commits (local only - push blocked by repo rules)
- `5eeef39`: `cgalpha: migrate from B2 to R2 - update all configs and workflows`
- `2bf326b`: `cgalpha: fix sync.py docstring, comments and ls_remote default path`

## Key Lessons
- R2 API token `cfut_...` (account-level) works for bucket management API calls but NOT for S3 data operations (ListObjectsV2 returns 401)
- R2 scoped token (`cfat_...`) with S3 credentials works perfectly for all S3 operations (upload/list/read/delete)
- B2 `K00x...` key format is correct for rclone B2 backend but the key must belong to the same Backblaze account as the bucket
- Push to GitHub blocked by repo rules (branch protection)