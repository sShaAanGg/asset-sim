# Real total assets (實質總資產)

Add a `real_total` column to `simulate()`'s output: total assets in today's purchasing power.

## Goal (目標)

- `total` is in nominal TWD (名目): a million TWD thirty years from now buys less than a million today, because of inflation (通膨).
- `real_total` shows what the total assets are worth in today's money (real purchasing power, 實質購買力), so results from different years, and from different inflation assumptions, can be compared.
- `Params.inflation` already raises expenses each year; this feature reuses the same rate.

## Interface (介面)

## Properties (性質)

## Open questions (待釐清的問題)
