---
name: pp-licensing
description: "Estimate and explain Power Pages licensing for one or more sites: authenticated and anonymous capacity packs (tiers, per-environment allocation minimums), pay-as-you-go meters, which visitors are and aren't counted, internal users already covered by Power Apps or Dynamics 365 licenses, and the cheapest subscription / pay-as-you-go mix across environments. Works packs-first (what do N packs cover, is the environment split valid) or usage-first (what to buy for N users). Uses a bundled calculator over Microsoft Learn list prices, so every figure is reproducible. Works for any Power Pages site (SPA or non-SPA). WHEN: how much will this Power Pages site cost, Power Pages pricing, Power Pages licensing, capacity packs, authenticated users per month, anonymous users per month, pay-as-you-go vs subscription, licensing estimate for a proposal, do internal users need a license, does the sign-in page count as anonymous, licensing for dev and test environments, read the capacity consumption report, what does one pack cover, are my packs enough, split packs across environments."
license: MIT
metadata:
  author: Victor Dantas
  version: "0.2.0"
---

# Power Pages licensing — estimate, explain, compare

Power Pages is licensed **per website, per month**, by unique **authenticated** and **anonymous**
users. You either buy **capacity packs** (subscription) and allocate them to environments, or
switch an environment to **pay-as-you-go** and pay per active user. This skill turns expected
usage into a cost estimate with `scripts/calc_licensing.py`, in either direction: from packs to the users they cover,
or from expected users to the packs to buy.

> **Never quote a price from memory.** Run the calculator: it reads `scripts/pricing.json`,
> which holds Microsoft's list prices with the date they were last checked against Learn. If that
> date is more than a few months old, re-check the
> [licensing FAQ](https://learn.microsoft.com/power-platform/admin/powerapps-flow-licensing-faq#power-pages)
> and [pay-as-you-go meters](https://learn.microsoft.com/power-platform/admin/pay-as-you-go-meters)
> pages and update the file first. List prices exclude education, non-profit and negotiated
> agreements; say so whenever you share an estimate.

## Microsoft's price list (start here)

Microsoft sells capacity in packs per user group. Show this table first when someone asks what
Power Pages costs; it needs no usage numbers.

**Subscription capacity packs** (bought per tenant, allocated per environment):

| | Authenticated | Anonymous |
|---|---|---|
| Users per pack | 100 | 500 |
| Tier 1 | 1+ packs, $200 / pack / month | 1+ packs, $75 / pack / month |
| Tier 2 | 100+ packs, $75 | 20+ packs, $37.50 |
| Tier 3 | 1,000+ packs, $50 | 200+ packs, $25 |
| Minimum allocation per environment | 25 users | 200 users |

- **Allocation minimums**: each environment that gets authenticated capacity takes at least 25
  users, and at least 200 for anonymous; after that, any number. A small dev environment can
  use up a large share of a single pack.
- Unused capacity **doesn't carry over** to the next month.
- Packs include Dataverse storage: authenticated 2 GB database + 16 GB file per pack, anonymous
  500 MB + 4 GB per pack, plus 5 GB database per tenant.
- CDN and WAF need no extra license.
- Learn gives a minimum purchase per tier but doesn't spell out the billing mechanics. The
  calculator prices **all** packs at the tier the purchase reaches; confirm with your Microsoft
  partner before promising a tier price.

**Pay-as-you-go** (per environment, billed through a linked Azure subscription):

- $4 per active authenticated user per website per month; $0.30 per active anonymous user.
- No packs and no minimums, so it usually wins for small or seasonal sites.
- In a pay-as-you-go environment, prepaid capacity assigned to it is **ignored**; reallocate it.

The calculator has two modes, one for each direction:

| Question | Mode |
|---|---|
| "We own (or were quoted) N packs. What do they cover, and is the split right?" | **Packs-first**: `--packs` |
| "We expect N users. What should we buy?" | **Usage-first**: `--site` |

Use `python3` on macOS and Linux. Add `--json` for machine-readable output and
`--no-env-minimums` to see the effect of the allocation minimums.

## Packs-first — what do these packs cover?

```
python scripts/calc_licensing.py --packs AUTH_PACKS:ANON_PACKS [--env NAME[:AUTH:ANON] ...]
```

```
# What does one authenticated pack get me?
python scripts/calc_licensing.py --packs 1:0

# 3 authenticated + 2 anonymous packs, split across production and test
python scripts/calc_licensing.py --packs 3:2 --env Prod:250:900 --env Test:25:0

# Can 1 authenticated pack serve five environments? (no: 5 x 25 = 125 users)
python scripts/calc_licensing.py --packs 1:0 --env Dev --env Test --env UAT --env Prod --env Demo
```

For each user group it reports the users covered, the tier and monthly cost, the cost per user,
how many environments the packs can serve at the minimum allocation, and the next tier, or a
**cheaper tier** when buying more packs costs less (90 authenticated packs at $200 cost more
than 100 at $75). With a planned split (`--env NAME:AUTH:ANON`) it flags allocations below the
minimums or above capacity, shows the headroom, and prices pay-as-you-go for the same users so
you can see whether the packs pay off.

## Usage-first — what should we buy?

Gather, for **each website** (or read them from the consumption reports below):

| Input | Meaning |
|---|---|
| Website name and **environment** | Capacity is allocated per environment; minimums apply per environment. |
| **Authenticated users** | Unique users who sign in at least once that calendar month. Not total logins. |
| **Anonymous users** | Unique anonymous visitors that month (browser cookie based). |
| **Already licensed internal users** (optional) | Of the authenticated users, those with Power Apps per user or Dynamics 365 enterprise licenses in the **same tenant**, signing in with the **Microsoft Entra ID** provider. They aren't counted. |

Plan for the **monthly** peak of users who actually visit, not everyone who *could* sign in: a
site open to 100,000 people that 5,000 use in a month needs capacity for 5,000 (Learn FAQ).

```
python scripts/calc_licensing.py --site "NAME:ENVIRONMENT:AUTH:ANON[:LICENSED_INTERNAL]" [--site ...]
```

```
# One partner portal, sign-in only (anonymous = 0)
python scripts/calc_licensing.py --site "Partner portal:Prod:1200:0"

# Two sites in production, one test site; 150 staff already hold Power Apps per user licenses
python scripts/calc_licensing.py --site "Portal:Prod:3000:20000:150" \
    --site "Events:Prod:0:4000" --site "Portal UAT:Test:30:0"
```

It prints three plans: **all subscription**, **all pay-as-you-go**, and the **cheapest mix**
(it tries every subscription / pay-as-you-go combination across environments, because pack
tiers are bought per tenant). It also buys up to a cheaper tier when that costs less;
`--no-buy-up` turns that off.

## Who is and isn't counted

Not counted, in either model:

- Sites in **trial** or **private** mode.
- Anonymous visitors who only reach sign-in, register, invitation or external-auth callback
  pages, `/_` system pages (`/_services`, `/_resource`), pages answering 3xx, 4xx or 5xx, or
  static files only. A **sign-in-only** site needs no anonymous capacity, provided the rest is
  locked with a Home page rule, not a JavaScript redirect (see `pp-pageaccessrule`).
- Someone who browses anonymously and signs in the same UTC day counts once, as authenticated.
- Bots and crawlers. Point uptime monitors at `/_services/about` so they aren't counted.
- Internal users with Power Apps per user (any number of sites), Power Apps per app (one site),
  or Dynamics 365 enterprise licenses (sites mapped to that app's environment) — same tenant,
  Entra ID provider only. **B2B guest users are not internal** and must be licensed.

**Counting quirks:** uniqueness is per **website**, so one person on two sites counts twice.
Anonymous uniqueness is a cookie: new browser, device or cleared cookies means a new user.
Client-side analytics (Application Insights, Google Analytics) won't match the official counts.

## Present it

For usage-first, lead with the cheapest mix and its monthly total, then the per-environment allocation and pack
counts, then the assumptions. For packs-first, lead with users covered and cost, then any allocation
problems. Always state: user counts are estimates, list prices as of the date in
`pricing.json`, tier billing to confirm with Microsoft. Link the two Learn pages. Don't round
the calculator's numbers or add your own.

## Check against real usage

Admins can download the **Power Pages authenticated** and **Power Pages anonymous** reports from
the Power Platform admin center (**Resources → Capacity → Add-ons → Download reports**); each
covers the 30 days before the chosen date. Feed those counts back into the calculator to
right-size capacity. Under-licensing a production site can degrade its performance, because
site resources scale with the capacity assigned. Pay-as-you-go usage shows in the downloadable
pay-as-you-go report.
([Website capacity consumption reports](https://learn.microsoft.com/power-pages/admin/website-consumption-reports))

## Microsoft docs & shared references

- [Power Platform licensing FAQ: Power Pages](https://learn.microsoft.com/power-platform/admin/powerapps-flow-licensing-faq#power-pages) — packs, tiers, minimums, who is counted.
- [Pay-as-you-go meters](https://learn.microsoft.com/power-platform/admin/pay-as-you-go-meters) and [its FAQ](https://learn.microsoft.com/power-platform/admin/pay-as-you-go-issues-faq).
- Microsoft's official Power Pages plugin has no licensing skill; this one fills that gap.
- Credit: Tino Rabe's [Power Pages pricing calculator](https://tinorabe.de/en/tools/power-pages-pricing-calculator/) inspired this skill and its per-environment minimum rule. The prices and rules here come from Learn.
