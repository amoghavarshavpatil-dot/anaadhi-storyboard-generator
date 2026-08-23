# Zyrex Ayurveda India — Full Catalogue Audit

This directory is deliberately isolated on the `zyrex-catalogue-audit` branch and is not intended to be merged into the ANAADHI movie project's `main` branch.

## Goal

Enumerate and verify the complete public product catalogue at `https://zyrexayurveda.com/`, then build machine-readable records for the future Zyrex product-advisor project without inventing missing product information.

## Discovery order

1. Public XML sitemap(s), if available.
2. Public WooCommerce Store API, if available.
3. Complete `/shop/` pagination fallback.

## Output

- `data/zyrex/product_urls.txt` — canonical URLs discovered.
- `data/zyrex/products.jsonl` — normalized product registry.
- `data/zyrex/products.csv` — spreadsheet-friendly registry.
- `data/zyrex/manifest.json` — counts, source methods, gate status.
- `data/zyrex/failed_urls.jsonl` — product pages that could not be verified.
- `data/zyrex/possible_variant_groups.json` — heuristic variant candidates requiring review.
- `reports/zyrex/CRAWL_REPORT.md` — audit summary.

## Safety / claim separation

Each record keeps three concepts separate:

- `zyrex_official_claim`: what the Zyrex page says.
- `general_information`: deliberately left unpopulated by the crawler; independent evidence belongs here later.
- `recommendation_allowed`: what a future shopper-facing advisor may responsibly do.

The crawler does not diagnose, guarantee cures, bypass access controls, log in, add products to cart, or submit checkout requests. Missing public-page fields remain blank.
