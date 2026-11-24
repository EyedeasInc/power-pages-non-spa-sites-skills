# Power Pages non-SPA site toolkit (Claude Code & GitHub Copilot plugin)

Skills for **provisioning**, building, integrating, and **securing** non-SPA **Power Pages** sites —
the Dataverse-backed Studio/Liquid sites on the **enhanced data model** (`mspp_*` tables +
`powerpagecomponent`). This is a community companion to Microsoft's
[Power Pages plugin](https://github.com/microsoft/power-platform-skills/blob/main/plugins/power-pages/README.md).
Since version 3.0.0, Microsoft's plugin creates, edits and scans non-SPA sites itself (`/create-site`,
`/edit-site`, `/analyze-performance`, in preview). Use it to start and reshape a site; use these `pp-*`
skills to work record by record on the live site, including the basic forms, lists, multistep forms,
column permissions, page access rules, redirects and navigation that Microsoft's non-SPA workflow
does not build. See [Using it with Microsoft's Power Pages plugin](#using-it-with-microsofts-power-pages-plugin)
for which plugin to use for each task.

> **Renamed in 0.10.0.** This plugin was `powerpages-traditional-site` in the
> `power-pages-traditional-sites-skills` repo. Microsoft now calls these sites non-SPA, so the plugin is
> `powerpages-non-spa-site` and the repo is `power-pages-non-spa-sites-skills`. Old GitHub URLs redirect,
> but the plugin ID changed: uninstall the old plugin and install the new one (see Install).

> Community-authored, led by [Zero to Hero](https://fromzerotoheroes.com). Not a Microsoft
> product. Built on the documented Dataverse Web API + `pac` CLI surface for enhanced-data-model
> sites.

> Every content skill assumes the shared backbone in
> [`references/non-spa-site-editing-model.md`](references/non-spa-site-editing-model.md) —
> the component storage model, the read-live-first rule, the robust-parse / PATCH technique, the
> shared auth pattern, and the cache-flush rule. Read it first.

## Using it with Microsoft's Power Pages plugin

The two plugins work in different ways, and they can run side by side.

- **Microsoft's plugin works on a local copy.** It edits a site downloaded with `pac pages download`,
  tracks the changes in Git and pushes them back with `/deploy-site`. Its basic form and list
  components only reference records that already exist.
- **These `pp-*` skills work on the live site.** They read and patch the `mspp_*` records and
  `powerpagecomponent` rows through the Dataverse Web API, then flush the cache.

When both are installed, pick by task:

| Task | Use |
|---|---|
| Create a new non-SPA site from a template | Microsoft `/create-site`, `/activate-site` |
| Reshape pages, content, styling and layout across a site | Microsoft `/edit-site`, `/author-webpage-content` |
| Deploy a downloaded site to an environment | Microsoft `/deploy-site` |
| Bootstrap 3 to 5 | Microsoft `/migrate-bootstrap` |
| Standard to Enhanced data model | Microsoft `/migrate-datamodel` |
| Firewall (WAF) rules | Microsoft `/manage-firewall` |
| Security headers and CSP | Microsoft `/manage-headers` |
| Full release-readiness security review | Microsoft `/security-review`, then `/pp-securityreview` for the Liquid and Web API checks |
| Performance scan, design review, cross-environment comparison, ALM | Microsoft `/analyze-performance`, `/exceptional-web-design`, `/compare-site-configurations`, `/plan-alm` |
| Create or edit basic forms, multistep forms and lists | `/pp-basicform`, `/pp-multistepform`, `/pp-list` |
| Column permissions and page access rules | `/pp-columnpermission`, `/pp-pageaccessrule` |
| Navigation menus, redirects, site markers | `/pp-weblink`, `/pp-redirect`, `/pp-sitemarker` |
| Change one live record now (a template, snippet, web file, page, role, permission, Web API setting) | the matching `pp-*` skill |
| A change does not show on the site | `/pp-cache` |
| Writing or debugging Liquid | `/pp-liquid` |
| Site start, stop, restart, trial to production, visibility, delete | `/pp-website` |
| What a site will cost: capacity packs vs pay-as-you-go | `/pp-licensing` |

The `pp-*` skills that overlap with Microsoft's (`pp-bootstrap-migrate`, `pp-datamodel-migrate`,
`pp-firewall`, `pp-headers`, `pp-website`, `pp-upload`) stay in this plugin for anyone who does not
install Microsoft's. Their descriptions point to the Microsoft skill when it is available.

> **Do not mix live edits with a stale download.** An upload pushes the whole local folder, so
> `/deploy-site` (Microsoft) or `/pp-upload` can overwrite any change a `pp-*` skill made live after
> that folder was downloaded. Download again right before you start local edits, and download or
> diff again before you upload if anyone changed the live site in between.

## Skills

Skills are **noun-named** (the object, not a verb) so each covers its whole lifecycle — e.g.
`/pp-webpage` creates, edits, *and* deletes pages, not just "adds" one. Object skills are one
word (`/pp-webtemplate`); action/CLI skills keep a hyphen (`/pp-datamodel-migrate`).

### Content authoring — `mspp_*` / `powerpagecomponent`

| Skill | What it does |
|---|---|
| **`/pp-webpage`** | Create, edit, navigate, and delete web pages (root + localized content `mspp_webpage` records). |
| **`/pp-pagetemplate`** | Create, edit, and delete page templates (`mspp_pagetemplate`) — the required link between a page and its web-template layout. |
| **`/pp-webtemplate`** | Create, edit, read, and delete web templates (`powerpagecomponent` type 8): read live → robust-parse → guarded edit → PATCH → flush. |
| **`/pp-webfile`** | Create, update, and delete web files (type 3 — CSS/JS/images) whose bytes live in the `filecontent` File column. |
| **`/pp-contentsnippet`** | Create, edit, and delete content snippets (`mspp_contentsnippet`) — named, localizable text/HTML blocks. |
| **`/pp-serverlogic`** | Create, edit, deploy, and remove server-side JavaScript via the type-35 / type-15 storage model. |
| **`/pp-liquid`** | Write correct, safe Liquid — the `nil != blank` trap, FetchXML guards, output escaping, `safeAjax`. |

### Navigation & routing

| Skill | What it does |
|---|---|
| **`/pp-weblink`** | Manage navigation — web link sets (`mspp_weblinkset`) and links (`mspp_weblink`): menus, dropdowns, page/external links. |
| **`/pp-sitemarker`** | Manage site markers (`mspp_sitemarker`) — named page references Liquid resolves (`{{ sitemarkers[…] }}`). |
| **`/pp-redirect`** | Manage URL redirects (`mspp_redirect`) — map inbound URLs to a page/marker/external target with 301/302. |

### Forms, lists & data

| Skill | What it does |
|---|---|
| **`/pp-basicform`** | Basic forms (`mspp_entityform`) — insert/edit/read-only record forms: record source, on-success/redirect, file upload, record actions, per-field metadata, custom JS, AI form-fill. |
| **`/pp-list`** | Lists (`mspp_entitylist`) — record grids from saved views: toolbar/row actions, my/account filters, map/calendar/modern views, search, and AI natural-language search + list summary. |
| **`/pp-multistepform`** | Multistep forms (`mspp_webform` + steps) — wizards: step types & branching, progress indicator, per-field metadata, session/edit-expiry, custom JS. |
| **`/pp-webapi`** | Enable, consume, audit, and disable the Power Pages Web API (`/_api/*`) for a table. |

### Access & security

| Skill | What it does |
|---|---|
| **`/pp-webrole`** | Create, assign, and manage web roles (`mspp_webrole`) — the access groups everything binds to. |
| **`/pp-tablepermission`** | Configure `mspp_entitypermission` and bind it to web roles; verify via the intersect. |
| **`/pp-columnpermission`** | Column-level security (`mspp_columnpermissionprofile` + `mspp_columnpermission`) within a table permission. |
| **`/pp-pageaccessrule`** | Page-level authorization (`mspp_webpageaccesscontrolrule`) — restrict/grant a page to web roles. |
| **`/pp-headers`** | Configure security response headers / CSP via `mspp_sitesetting`, then verify them on the wire. |
| **`/pp-firewall`** | Inspect and configure the WAF and IP allow-list in front of a production site via `pac power-pages` (Preview). |
| **`/pp-securityreview`** | Audit the platform's real failure modes and run the `pac power-pages` quick/deep scans first. |

### Site lifecycle & CLI — `pac`

| Skill | What it does |
|---|---|
| **`/pp-website`** | Provision and run the site itself via `pac power-pages` (Preview): create, list, start/stop/restart, visibility, delete. |
| **`/pp-datamodel-migrate`** | Migrate a site Standard(`adx_`)→Enhanced(`mspp_`) via `pac pages migrate-datamodel` — the prerequisite the content skills assume. |
| **`/pp-download`** | Download site content to disk (`pac pages download` / `clone`) for backup, diff, source control. |
| **`/pp-upload`** | Upload/promote site content across environments (`pac pages upload`) with deployment profiles. |
| **`/pp-bootstrap-migrate`** | Bootstrap 3→5 for Liquid templates via `pac pages bootstrap-migrate`, plus residual fixes. |

### Utility

| Skill | What it does |
|---|---|
| **`/pp-cache`** | Invalidate the portal cache so component changes actually show. |
| **`/pp-licensing`** | Licensing in both directions: what N packs cover and whether the environment split is valid, or what to buy for N expected users (capacity packs, tiers, per-environment minimums, pay-as-you-go, cheapest mix). Bundled calculator over Microsoft Learn list prices. |

## Install

One repo, one manifest (`.claude-plugin/plugin.json`), read by both Claude Code and GitHub Copilot.

### Claude Code

```text
/plugin marketplace add EyedeasInc/power-pages-non-spa-sites-skills
/plugin install powerpages-non-spa-site@powerpages-non-spa-site
```

Or from a local clone: `/plugin marketplace add /path/to/power-pages-non-spa-sites-skills`.

### GitHub Copilot CLI

```bash
copilot plugin install EyedeasInc/power-pages-non-spa-sites-skills
```

Or via the marketplace: `copilot plugin marketplace add EyedeasInc/power-pages-non-spa-sites-skills`,
then `copilot plugin install powerpages-non-spa-site@powerpages-non-spa-site`.
After pulling changes, reinstall to refresh Copilot's plugin cache.

### GitHub Copilot in VS Code (agent plugins, Preview)

Add the repo as a plugin marketplace in `settings.json`, then install it from the Extensions view
(`@agentPlugins`) or **Chat: Plugins**:

```json
"chat.plugins.marketplaces": ["EyedeasInc/power-pages-non-spa-sites-skills"]
```

Or run **Chat: Install Plugin From Source** with the repo URL. Plugins installed with the Copilot CLI
are picked up by VS Code automatically.

### Using it

Invoke a skill by name (e.g. `/pp-webtemplate`) or just describe the task
("add a members-only page", "put a contact form on the home page", "why isn't my template change showing").

> Prefer one as a standalone skill instead of a plugin? Copy the `skills/<name>/` folder to your
> personal skills folder (`~/.claude/skills/` or `~/.copilot/skills/`). Skills that link to
> `../../references/` need that folder copied alongside.

### Sample prompts (new in 0.12.0)

**`/pp-licensing`: packs-first** (you already own packs, or have a quote)

```text
/pp-licensing We bought 3 authenticated packs and 2 anonymous packs.
We want to split them across Prod (250 signed-in users, 900 anonymous visitors a month)
and Test (25 signed-in users, no anonymous). Is that split valid, how much headroom
do we have, and would pay-as-you-go have been cheaper?
```

**`/pp-licensing`: usage-first** (what should we buy?)

```text
/pp-licensing Estimate the monthly cost for a client proposal.
- Partner portal, Prod environment: about 3,000 people sign in each month,
  150 of them are staff with Power Apps per user licenses. 20,000 anonymous visitors.
- Events site, also in Prod: anonymous only, about 4,000 visitors a month.
- Portal UAT, Test environment: 30 testers who sign in.
Compare capacity packs with pay-as-you-go and give me the cheapest mix.
```

**`/pp-licensing`: quick questions**

```text
/pp-licensing What does one authenticated pack cover, and how many environments can it serve?
/pp-licensing Our member site is sign-in only, about 400 members a month. Do we need anonymous capacity?
/pp-licensing At what number of signed-in users does tier 2 become cheaper than tier 1?
/pp-licensing Here are the counts from the admin center's Power Pages authenticated and anonymous reports: ...
```

For an accurate estimate, give **monthly users who actually visit** (not everyone who could),
**per site** (one person on two sites counts twice), and the **environment** of each site (the
25 authenticated / 200 anonymous minimums apply per environment).

**New checks and recipes in other skills**

```text
/pp-securityreview Run check 8 on our site: authorization model, Download buttons on lists,
permissions still live after we removed them in dev, and flows that trust a record ID.

/pp-columnpermission Hide the SSN column from the Partner role. Check first whether the site
uses enhanced authorization.

/pp-pageaccessrule Make the whole site sign-in only, but keep the sign-in and registration
pages styled for anonymous visitors.

/pp-cache My site setting change isn't showing. Which cache layer is it, and should I use
Clear config or Clear cache?

/pp-list Highlight rows on the Orders list where status is Overdue, after the grid loads.

/pp-webapi Read orders with their product names in one call using FetchXML.

/pp-website Connect www.contoso.com to the site. We have WAF turned on.
```

## Requirements

- A Power Pages **enhanced data model** site and Dataverse access — a **Dataverse MCP** (preferred
  for reads; respects security roles), or a Web API **bearer token**.
- **Python 3** for the bundled scripts and the reminder hook. On macOS/Linux run them with `python3`;
  on Windows `python` is fine.
- The bundled Python scripts share one auth pattern: they reuse a workspace `scripts/auth.py`
  exposing `get_token()` (the `dv-connect` pattern) if present, otherwise read a bearer token from
  the `DATAVERSE_TOKEN` env var. `DATAVERSE_URL` comes from a `--url` arg or the env var.
- **Two auth models.** The **content** skills use the Dataverse Web API (MCP or `DATAVERSE_TOKEN`)
  and patch **live** components individually — they never batch-upload, so they're safe alongside
  Studio edits. The **CLI** skills (`pp-website`, `pp-datamodel-migrate`, `pp-download`,
  `pp-upload`, `pp-bootstrap-migrate`, `pp-firewall`) drive `pac pages` / `pac power-pages`, which
  use a **`pac auth`** profile + `--environment`. Run `pac auth create` / `pac auth list` first;
  requires the Power Platform CLI (`pac`). Several `pac power-pages` commands are **Preview**.
- `pp-upload` is the **bulk** promotion tool (whole folder) for moving a site between
  environments — distinct from the live single-component patch the content skills do.

## Layout

```
powerpages-non-spa-site/
├─ .claude-plugin/
│  ├─ plugin.json                      # plugin manifest (Claude Code + Copilot)
│  └─ marketplace.json                 # single-plugin marketplace
├─ agents/                             # read-only specialists (spawned by skills)
│  ├─ security-auditor.agent.md
│  └─ web-template-architect.agent.md
├─ hooks/                              # automatic reminders
│  ├─ hooks.json                       # PostToolUse(Skill) → cache/permission reminder
│  └─ skill_reminder.py
├─ references/                         # shared knowledge (MS Learn + community, cited)
│  ├─ non-spa-site-editing-model.md   # shared backbone (read first)
│  ├─ webapi-field-configuration.md
│  ├─ security-model.md
│  ├─ web-template-components.md
│  ├─ server-logic-objects.md
│  ├─ site-settings-catalog.md
│  └─ community-credits.md
└─ skills/                             # 28 skills
   ├─ Content:     pp-webpage/ pp-pagetemplate/ pp-webtemplate/ pp-webfile/
   │               pp-contentsnippet/ pp-serverlogic/ pp-liquid/
   ├─ Nav/routing: pp-weblink/ pp-sitemarker/ pp-redirect/
   ├─ Forms/data:  pp-basicform/ pp-list/ pp-multistepform/ pp-webapi/
   ├─ Security:    pp-webrole/ pp-tablepermission/ pp-columnpermission/
   │               pp-pageaccessrule/ pp-headers/ pp-firewall/ pp-securityreview/
   ├─ Lifecycle:   pp-website/ pp-datamodel-migrate/ pp-download/ pp-upload/ pp-bootstrap-migrate/
   └─ Utility:     pp-cache/ pp-licensing/
```

## Agents, hooks & references

- **Agents** (`agents/`) — read-only specialists a skill can spawn for a focused, isolated job:
  `security-auditor` (deep security audit, from `pp-securityreview`) and `web-template-architect`
  (reusable-component / Liquid design, from `pp-webtemplate` / `pp-webpage` / `pp-pagetemplate`).
  In Claude Code they appear as `powerpages-non-spa-site:security-auditor`; in Copilot, pick them
  from the agent list (`/agent`).
- **Hooks** (`hooks/`) — a `PostToolUse` reminder (Claude-format hooks, also honored by Copilot) that, after a content-mutating `pp-*` skill,
  nudges you to flush the portal cache (`/pp-cache`) and confirm table permissions + web roles.
- **References** (`references/`) — shared knowledge grounded in **Microsoft Learn** (authoritative),
  cross-checked against Microsoft's official Power Pages plugin, and enriched with credited community
  best practices. Each skill's *"Microsoft docs & shared references"* section points into these.

## Sources & community credits

Knowledge is grounded first in Microsoft Learn, then enriched with field-tested insight from the
Power Pages community — paraphrased, credited, and (where they conflict with Microsoft) corrected in
Microsoft's favor. Full list in [`references/community-credits.md`](references/community-credits.md):
Nick Doelman, Nicholas Hayduk, Oleksandr Olashyn, Ulrikke Akerbak, Tino Rabe, Michel Mendes, Franco
Musso. Community-led by [Zero to Hero](https://fromzerotoheroes.com); not a Microsoft product.
