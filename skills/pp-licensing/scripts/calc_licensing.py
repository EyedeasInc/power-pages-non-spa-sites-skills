#!/usr/bin/env python
"""Estimate monthly Power Pages licensing cost from expected users per website.

Prices, pack sizes, tiers and per-environment minimums come from pricing.json next to this
script (Microsoft Learn list prices; see its "checked" date and sources). The script never
invents a number: every figure it prints is either your input or arithmetic on pricing.json.

Input is one --site per website:  NAME:ENVIRONMENT:AUTH_USERS:ANON_USERS[:LICENSED_INTERNAL]
  AUTH_USERS         unique users who sign in to that website in a month
  ANON_USERS         unique anonymous visitors to that website in a month (0 if the only
                     anonymous page is sign-in)
  LICENSED_INTERNAL  optional: of AUTH_USERS, how many already hold Power Apps per user or
                     Dynamics 365 enterprise licenses in the same tenant and sign in with the
                     Microsoft Entra ID provider (not counted by Power Pages)

Users are counted per website: someone who signs in to two sites counts twice.

For each environment the script compares a subscription (capacity packs, with the 25
authenticated / 200 anonymous per-environment allocation minimums) against pay-as-you-go,
then searches every subscription / pay-as-you-go mix across environments for the cheapest
total, because pack tiers are bought per tenant.

Packs-first mode (--packs AUTH_PACKS:ANON_PACKS) starts from packs you own or were quoted
and reports the users they cover, the monthly cost at the tier they reach, whether a cheaper
tier is in reach, and how many environments the packs can serve given the allocation minimums.
Add --env NAME[:AUTH_ALLOCATION:ANON_ALLOCATION] per environment to check a planned split
(allocations at or above the minimums, total within capacity) and compare pay-as-you-go for
those users.

Examples:
  python calc_licensing.py --packs 3:0
  python calc_licensing.py --packs 3:2 --env Prod:250:900 --env Test:25:0
  python calc_licensing.py --site "Partner portal:Prod:1200:0"
  python calc_licensing.py --site "Portal:Prod:3000:20000:150" --site "Events:Prod:0:4000" \\
      --site "Portal UAT:Test:30:0"
  python calc_licensing.py --site "Portal:Prod:800:5000" --json
"""
import argparse
import itertools
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_ENVS_FOR_SEARCH = 12


def load_pricing(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_site(text):
    parts = [p.strip() for p in text.split(":")]
    if len(parts) not in (4, 5):
        raise argparse.ArgumentTypeError(
            f"--site '{text}': expected NAME:ENVIRONMENT:AUTH_USERS:ANON_USERS[:LICENSED_INTERNAL]")
    name, env = parts[0], parts[1]
    try:
        nums = [int(p) for p in parts[2:]]
    except ValueError:
        raise argparse.ArgumentTypeError(f"--site '{text}': user counts must be whole numbers")
    if any(n < 0 for n in nums):
        raise argparse.ArgumentTypeError(f"--site '{text}': user counts can't be negative")
    auth, anon = nums[0], nums[1]
    internal = nums[2] if len(nums) == 3 else 0
    if internal > auth:
        raise argparse.ArgumentTypeError(
            f"--site '{text}': LICENSED_INTERNAL ({internal}) is more than AUTH_USERS ({auth})")
    if not name or not env:
        raise argparse.ArgumentTypeError(f"--site '{text}': NAME and ENVIRONMENT are required")
    return {"name": name, "environment": env, "auth": auth, "anon": anon,
            "licensed_internal": internal, "billable_auth": auth - internal}


def tier_for(packs, tiers):
    """Highest tier whose minimum purchase the pack count meets (volume pricing)."""
    best = None
    for t in sorted(tiers, key=lambda t: t["min_packs"]):
        if packs >= t["min_packs"]:
            best = t
    return best


def pack_cost(packs, tiers, allow_buy_up=True):
    """Cost of `packs` packs, optionally buying up to a higher tier's minimum when cheaper."""
    if packs <= 0:
        return {"packs_needed": 0, "packs_bought": 0, "tier": None, "price_per_pack": 0.0,
                "cost": 0.0, "bought_up": False}
    t = tier_for(packs, tiers)
    best = {"packs_needed": packs, "packs_bought": packs, "tier": t["tier"],
            "price_per_pack": t["price_per_pack"], "cost": packs * t["price_per_pack"],
            "bought_up": False}
    if allow_buy_up:
        for higher in tiers:
            if higher["min_packs"] > packs:
                cost = higher["min_packs"] * higher["price_per_pack"]
                if cost < best["cost"]:
                    best = {"packs_needed": packs, "packs_bought": higher["min_packs"],
                            "tier": higher["tier"], "price_per_pack": higher["price_per_pack"],
                            "cost": cost, "bought_up": True}
    return best


def environments(sites):
    envs = {}
    for s in sites:
        e = envs.setdefault(s["environment"], {"environment": s["environment"], "sites": [],
                                               "auth": 0, "anon": 0})
        e["sites"].append(s["name"])
        e["auth"] += s["billable_auth"]
        e["anon"] += s["anon"]
    return list(envs.values())


def allocation(users, minimum, apply_minimum):
    if users <= 0:
        return 0
    return max(users, minimum) if apply_minimum else users


def evaluate(envs, choice, pricing, apply_minimum, allow_buy_up):
    """choice[i] is 'subscription' or 'payg' for envs[i]."""
    sub = pricing["subscription"]
    payg = pricing["pay_as_you_go"]
    auth_alloc = anon_alloc = 0
    payg_cost = 0.0
    rows = []
    for env, how in zip(envs, choice):
        if how == "payg":
            cost = (env["auth"] * payg["authenticated_per_active_user_per_website"]
                    + env["anon"] * payg["anonymous_per_active_user_per_website"])
            payg_cost += cost
            rows.append({**env, "model": "pay-as-you-go", "payg_cost": round(cost, 2)})
        else:
            a = allocation(env["auth"], sub["authenticated"]["environment_minimum_users"],
                           apply_minimum)
            n = allocation(env["anon"], sub["anonymous"]["environment_minimum_users"],
                           apply_minimum)
            auth_alloc += a
            anon_alloc += n
            rows.append({**env, "model": "subscription", "auth_allocation": a,
                         "anon_allocation": n})
    auth_packs = math.ceil(auth_alloc / sub["authenticated"]["users_per_pack"])
    anon_packs = math.ceil(anon_alloc / sub["anonymous"]["users_per_pack"])
    auth = pack_cost(auth_packs, sub["authenticated"]["tiers"], allow_buy_up)
    anon = pack_cost(anon_packs, sub["anonymous"]["tiers"], allow_buy_up)
    total = auth["cost"] + anon["cost"] + payg_cost
    storage = None
    if auth["packs_bought"] or anon["packs_bought"]:
        sa = sub["authenticated"]["storage_per_pack_gb"]
        sn = sub["anonymous"]["storage_per_pack_gb"]
        storage = {
            "database_gb": sub["tenant_database_storage_gb"]
            + auth["packs_bought"] * sa["database"] + anon["packs_bought"] * sn["database"],
            "file_gb": auth["packs_bought"] * sa["file"] + anon["packs_bought"] * sn["file"],
        }
    return {"environments": rows,
            "subscription": {"authenticated_users_allocated": auth_alloc,
                             "anonymous_users_allocated": anon_alloc,
                             "authenticated_packs": auth, "anonymous_packs": anon,
                             "included_storage": storage},
            "payg_cost": round(payg_cost, 2),
            "monthly_total": round(total, 2)}


def parse_packs(text):
    parts = [p.strip() for p in text.split(":")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"--packs '{text}': expected AUTH_PACKS:ANON_PACKS")
    try:
        a, n = int(parts[0]), int(parts[1])
    except ValueError:
        raise argparse.ArgumentTypeError(f"--packs '{text}': pack counts must be whole numbers")
    if a < 0 or n < 0 or a + n == 0:
        raise argparse.ArgumentTypeError(f"--packs '{text}': give at least one pack, none negative")
    return {"auth": a, "anon": n}


def parse_env(text):
    parts = [p.strip() for p in text.split(":")]
    if len(parts) not in (1, 3) or not parts[0]:
        raise argparse.ArgumentTypeError(
            f"--env '{text}': expected NAME or NAME:AUTH_ALLOCATION:ANON_ALLOCATION")
    if len(parts) == 1:
        return {"environment": parts[0], "auth": None, "anon": None}
    try:
        a, n = int(parts[1]), int(parts[2])
    except ValueError:
        raise argparse.ArgumentTypeError(f"--env '{text}': allocations must be whole numbers")
    if a < 0 or n < 0:
        raise argparse.ArgumentTypeError(f"--env '{text}': allocations can't be negative")
    return {"environment": parts[0], "auth": a, "anon": n}


def packs_first(packs, envs, pricing, apply_minimum):
    sub = pricing["subscription"]
    payg = pricing["pay_as_you_go"]
    out = {"groups": {}, "environments": [], "problems": [], "monthly_total": 0.0}
    for key, label, rate_key in (("auth", "authenticated", "authenticated_per_active_user_per_website"),
                                 ("anon", "anonymous", "anonymous_per_active_user_per_website")):
        cfg = sub[label]
        n = packs[key]
        if not n:
            continue
        t = tier_for(n, cfg["tiers"])
        cost = n * t["price_per_pack"]
        users = n * cfg["users_per_pack"]
        minimum = cfg["environment_minimum_users"] if apply_minimum else 1
        g = {"packs": n, "users_covered": users, "tier": t["tier"],
             "price_per_pack": t["price_per_pack"], "monthly_cost": cost,
             "cost_per_user": cost / users,
             "max_environments": users // minimum,
             "environment_minimum": minimum,
             "payg_if_all_covered_users_active": users * payg[rate_key],
             "cheaper_tier": None}
        for higher in cfg["tiers"]:
            if higher["min_packs"] > n:
                hc = higher["min_packs"] * higher["price_per_pack"]
                if hc <= cost:
                    g["cheaper_tier"] = {"tier": higher["tier"], "packs": higher["min_packs"],
                                         "monthly_cost": hc,
                                         "users_covered": higher["min_packs"] * cfg["users_per_pack"]}
                    break
        nxt = [h for h in cfg["tiers"] if h["min_packs"] > n]
        if nxt:
            g["next_tier"] = {"tier": nxt[0]["tier"], "min_packs": nxt[0]["min_packs"],
                              "price_per_pack": nxt[0]["price_per_pack"]}
        out["groups"][label] = g
        out["monthly_total"] += cost

    named = [e for e in envs if e["auth"] is not None]
    if envs and not named:
        for label, key in (("authenticated", "auth"), ("anonymous", "anon")):
            g = out["groups"].get(label)
            if g and len(envs) > g["max_environments"]:
                out["problems"].append(
                    f"{len(envs)} environments need at least {len(envs) * g['environment_minimum']:,} "
                    f"{label} users at the minimum allocation; {packs[key]} pack(s) cover "
                    f"{g['users_covered']:,}.")
    for label, key, rate_key in (("authenticated", "auth", "authenticated_per_active_user_per_website"),
                                 ("anonymous", "anon", "anonymous_per_active_user_per_website")):
        if not named:
            continue
        cfg = sub[label]
        minimum = cfg["environment_minimum_users"] if apply_minimum else 1
        covered = packs[key] * cfg["users_per_pack"]
        total = sum(e[key] for e in named)
        for e in named:
            if 0 < e[key] < minimum:
                out["problems"].append(
                    f"{e['environment']}: {e[key]:,} {label} users is below the {minimum}-user "
                    f"minimum allocation per environment.")
        if total > covered:
            out["problems"].append(
                f"Planned {label} allocation {total:,} exceeds the {covered:,} users the "
                f"packs cover; you need {math.ceil(total / cfg['users_per_pack'])} pack(s).")
        if label in out["groups"] or total:
            out["groups"].setdefault(label, {})["allocated"] = total
            out["groups"][label]["headroom"] = covered - total
            out["groups"][label]["payg_for_allocated_users"] = total * pricing["pay_as_you_go"][rate_key]
    out["environments"] = named
    out["monthly_total"] = round(out["monthly_total"], 2)
    return out


def print_packs_first(packs, envs, res, pricing):
    print(f"Power Pages packs check (list prices checked {pricing['checked']}, USD)")
    print(pricing["price_basis"])
    print(f"Packs: {packs['auth']} authenticated, {packs['anon']} anonymous\n")
    for label in ("authenticated", "anonymous"):
        g = res["groups"].get(label)
        if not g or "packs" not in g:
            continue
        print(f"{label.capitalize()}: {g['packs']} pack(s) cover {g['users_covered']:,} users per "
              f"month, tier {g['tier']} at {money(g['price_per_pack'])} = "
              f"{money(g['monthly_cost'])} ({money(g['cost_per_user'])} per user)")
        print(f"  Serves up to {g['max_environments']:,} environment(s) at the "
              f"{g['environment_minimum']}-user minimum allocation")
        if g.get("cheaper_tier"):
            c = g["cheaper_tier"]
            print(f"  Cheaper: {c['packs']} packs at tier {c['tier']} cost "
                  f"{money(c['monthly_cost'])} and cover {c['users_covered']:,} users")
        elif g.get("next_tier"):
            nt = g["next_tier"]
            print(f"  Next tier: {nt['min_packs']} packs at {money(nt['price_per_pack'])}")
        if "allocated" in g:
            print(f"  Planned allocation {g['allocated']:,}, headroom {g['headroom']:,}; "
                  f"pay-as-you-go for those users: {money(g['payg_for_allocated_users'])}")
        else:
            print(f"  Pay-as-you-go if every covered user is active: "
                  f"{money(g['payg_if_all_covered_users_active'])}")
    for label in ("authenticated", "anonymous"):
        g = res["groups"].get(label)
        if g and "packs" not in g and g.get("allocated"):
            print(f"{label.capitalize()}: no packs, but {g['allocated']:,} users allocated")
    if res["environments"]:
        print("\nPlanned split:")
        for e in res["environments"]:
            print(f"  {e['environment']}: {e['auth']:,} authenticated, {e['anon']:,} anonymous")
    print(f"\nPacks total: {money(res['monthly_total'])} per month")
    if res["problems"]:
        print("\nProblems:")
        for p in res["problems"]:
            print(f"  - {p}")
    else:
        print("No allocation problems found.")
    print("\nSources: " + pricing["sources"]["licensing_faq"])
    print("         " + pricing["sources"]["payg_meters"])


def money(x):
    return f"${x:,.2f}"


def print_plan(title, plan):
    print(f"\n{title}: {money(plan['monthly_total'])} per month")
    for r in plan["environments"]:
        sites = ", ".join(r["sites"])
        if r["model"] == "pay-as-you-go":
            print(f"  {r['environment']} ({sites}): pay-as-you-go, {r['auth']:,} authenticated + "
                  f"{r['anon']:,} anonymous = {money(r['payg_cost'])}")
        else:
            print(f"  {r['environment']} ({sites}): subscription, allocate "
                  f"{r['auth_allocation']:,} authenticated / {r['anon_allocation']:,} anonymous "
                  f"(expected {r['auth']:,} / {r['anon']:,})")
    s = plan["subscription"]
    for label, key in (("Authenticated", "authenticated_packs"), ("Anonymous", "anonymous_packs")):
        p = s[key]
        if p["packs_bought"]:
            extra = (f" (needs {p['packs_needed']}, buying up to the tier {p['tier']} minimum is "
                     f"cheaper)" if p["bought_up"] else "")
            print(f"  {label} packs: {p['packs_bought']} x {money(p['price_per_pack'])} "
                  f"(tier {p['tier']}) = {money(p['cost'])}{extra}")
    if s["included_storage"]:
        st = s["included_storage"]
        print(f"  Dataverse storage included with these packs: {st['database_gb']:g} GB database "
              f"(incl. 5 GB per tenant), {st['file_gb']:g} GB file")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--site", action="append", type=parse_site,
                      help="usage-first: NAME:ENVIRONMENT:AUTH_USERS:ANON_USERS[:LICENSED_INTERNAL]")
    mode.add_argument("--packs", type=parse_packs,
                      help="packs-first: AUTH_PACKS:ANON_PACKS you own or were quoted")
    ap.add_argument("--env", action="append", type=parse_env, default=[],
                    help="with --packs: NAME or NAME:AUTH_ALLOCATION:ANON_ALLOCATION")
    ap.add_argument("--no-env-minimums", action="store_true",
                    help="ignore the 25 authenticated / 200 anonymous per-environment minimums")
    ap.add_argument("--no-buy-up", action="store_true",
                    help="don't consider buying up to a cheaper tier's minimum pack count")
    ap.add_argument("--pricing", default=os.path.join(HERE, "pricing.json"))
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = ap.parse_args()

    pricing = load_pricing(args.pricing)
    if args.env and not args.packs:
        ap.error("--env only works with --packs")
    if args.packs:
        if args.env and len({e["auth"] is None for e in args.env}) > 1:
            ap.error("--env: give allocations for every environment or for none")
        res = packs_first(args.packs, args.env, pricing, not args.no_env_minimums)
        if args.json:
            print(json.dumps({"pricing_checked": pricing["checked"], "packs": args.packs,
                              **res}, indent=2))
        else:
            print_packs_first(args.packs, args.env, res, pricing)
        return
    envs = environments(args.site)
    if len(envs) > MAX_ENVS_FOR_SEARCH:
        sys.exit(f"{len(envs)} environments: the mix search is capped at {MAX_ENVS_FOR_SEARCH}.")
    apply_min = not args.no_env_minimums
    buy_up = not args.no_buy_up

    all_sub = evaluate(envs, ["subscription"] * len(envs), pricing, apply_min, buy_up)
    all_payg = evaluate(envs, ["payg"] * len(envs), pricing, apply_min, buy_up)
    best = min((evaluate(envs, list(c), pricing, apply_min, buy_up)
                for c in itertools.product(["subscription", "payg"], repeat=len(envs))),
               key=lambda p: p["monthly_total"])

    result = {"pricing_checked": pricing["checked"], "price_basis": pricing["price_basis"],
              "sources": pricing["sources"], "environment_minimums_applied": apply_min,
              "sites": args.site, "all_subscription": all_sub, "all_pay_as_you_go": all_payg,
              "cheapest_mix": best}
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Power Pages licensing estimate (list prices checked {pricing['checked']}, USD)")
    print(pricing["price_basis"])
    for s in args.site:
        excl = (f", {s['licensed_internal']:,} already licensed (not counted)"
                if s["licensed_internal"] else "")
        print(f"  {s['name']} [{s['environment']}]: {s['auth']:,} authenticated{excl}, "
              f"{s['anon']:,} anonymous per month")
    print_plan("All subscription", all_sub)
    print_plan("All pay-as-you-go", all_payg)
    print_plan("Cheapest mix", best)
    if not apply_min:
        print("\nPer-environment minimums were NOT applied (--no-env-minimums).")
    print("\nSources: " + pricing["sources"]["licensing_faq"])
    print("         " + pricing["sources"]["payg_meters"])


if __name__ == "__main__":
    main()
