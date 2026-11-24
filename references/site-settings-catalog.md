# Site settings catalog (headers, security, and useful lesser-known settings)

Shared reference of high-value `mspp_sitesetting` records for a non-SPA site. Used by
`pp-headers`, `pp-website`, `pp-webapi`, `pp-basicform`.

> **Authority:** Microsoft Learn for every section marked **Learn** (linked inline): headers,
> SameSite, search, date/time formats, registration, server logic, lists and output caching.
> The **lookup modal** names are **community-cataloged** (Oleksandr Olashyn) and not on Learn —
> **verify the exact name on your site version** before relying on them.
> **Sources:** [Configure site settings](https://learn.microsoft.com/en-us/power-pages/configure/configure-site-settings) ·
> [CORS / headers](https://learn.microsoft.com/en-us/power-pages/configure/cors-support) ·
> [Important changes (SameSite)](https://learn.microsoft.com/en-us/power-pages/important-changes-deprecations) ·
> Olashyn catalog: https://www.dancingwithcrm.com/portal-settings-list/ ·
> https://github.com/OOlashyn/PowerAppsPortalSiteSettingsAndSnippets

> **Note on naming/storage.** Setting names use `/` (e.g. `HTTP/X-Frame-Options`). When exported via
> `pac`, header settings become `*.sitesetting.yml` files with `/` → `-` in the filename. Confirm
> names in the Portal Management app; some entries below are **content snippets**, not site settings.

## Security response headers (map to `pp-headers`) — Microsoft-documented

| Setting | Effect |
|---|---|
| `HTTP/Content-Security-Policy` | CSP. Avoid `unsafe-inline`/`unsafe-eval` in `script-src`. |
| `HTTP/X-Frame-Options` | Clickjacking: `SAMEORIGIN` / `DENY`. |
| `HTTP/X-Content-Type-Options` | `nosniff`. |
| `HTTP/Referrer-Policy` | e.g. `strict-origin-when-cross-origin`. |
| `HTTP/Permissions-Policy` | Least-privilege browser-feature policy. |
| `HTTP/Access-Control-Allow-Origin` / `-Methods` / `-Headers` / `-Credentials` / `-Max-Age` | CORS set. |
| `HTTP/SameSite/Default` | Cookie SameSite for all cookies: `None` / `Lax` / `Strict`. Default `Lax`. |
| `HTTP/SameSite/{CookieName}` | SameSite for a specific cookie. |

> ⚠️ **Platform-managed — do not try to set these:** `Cache-Control` and
> `HTTP/Strict-Transport-Security` (HSTS) are managed by the platform; a site setting has no effect.

## Search — Learn

| Setting | Effect |
|---|---|
| `Search/EnableDataverseSearch` | `true` to use Dataverse search (Lucene.NET search is deprecated). |
| `Search/EnableProgressiveSearchCounts` | `true` to evaluate up to 50 records per search for permissions and keywords, so counts stop disagreeing with results (shows **50+**). Rebuild the index after changing it. ([Progressive search](https://learn.microsoft.com/power-pages/configure/search/progressive)) |

## Date and time formats — Learn

Override the language default with .NET [custom date and time format strings](https://learn.microsoft.com/dotnet/standard/base-types/custom-date-and-time-format-strings).
([Date and time fields](https://learn.microsoft.com/power-pages/configure/behavior-format-date-time-field))

| Setting | Effect |
|---|---|
| `DateTime/DateFormat` | Site-wide date format (e.g. `dd/MM/yyyy`). |
| `DateTime/TimeFormat` | Site-wide time format (e.g. `HH:mm`). |
| `DateTime/DateTimeFormat` | Full date and time format. |

The column's Dataverse behaviour (User Local, Date Only, Time-Zone Independent) decides time zone
conversion on forms and lists; Date Only and Time-Zone Independent can't be changed after saving.

## Lists — Learn

| Setting | Effect |
|---|---|
| `Site/EnableSortingOnLinkedEntities` | `true` lets visitors sort list columns that come from related tables. ([Sort lists](https://learn.microsoft.com/power-pages/configure/sort-lists)) |

## Output caching — Learn

| Setting | Effect |
|---|---|
| `Footer/OutputCache/Enabled` | Keep `true`; Site Checker flags it when off. Keep user-specific Liquid out of cached header and footer markup (use the substitution tag). ([Site Checker performance](https://learn.microsoft.com/power-pages/admin/site-checker-performance)) |

## Server logic — Learn

| Setting | Default | Effect |
|---|---|---|
| `ServerLogic/Enabled` | `true` | Turns the feature on or off. |
| `ServerLogic/AllowedDomains` | all domains | Restricts which external domains server logic can call. |
| `ServerLogic/TimeoutInSeconds` | `120` | Maximum execution time; can be raised to **240**. |
| `ServerLogic/AllowNetworkingToAllDomains` | `true` | Allows networking across domains. |

([Server logic overview](https://learn.microsoft.com/power-pages/configure/server-logic-overview))

## Lookup modal (community-cataloged, NOT on Learn — verify per version)

None of these names appear on Microsoft Learn. Confirm each one on a dev site (create it, flush
the cache, open a lookup) before telling anyone it works.

| Setting / snippet | Effect (as cataloged) |
|---|---|
| `Portal/Lookup/Modal/Size` | Lookup modal size (`Small` / `Large`). |
| `Portal/Lookup/Modal/Grid/PageSize` | Rows per page in lookup grids (default 10). |
| `Portal/Lookup/Modal/Title` | Lookup modal heading text. |
| `Portal/Lookup/Modal/Grid/Search/PlaceholderText` *(snippet)* | Lookup search placeholder. |
| `Portal/Lookup/Modal/Grid/Search/TooltipText` *(snippet)* | Lookup search wildcard tooltip. |

Related, and on Learn: a lookup rendered as a **dropdown** on a basic or multistep form slows the
page once it lists more than **200** records that change often. Use dropdown mode only for small,
static lists (countries, states). ([Site Checker performance](https://learn.microsoft.com/power-pages/admin/site-checker-performance#basic-form-lookup-configuration))

## Registration / login paths — Learn

([Local authentication, registration, and other settings](https://learn.microsoft.com/power-pages/security/authentication/set-authentication-identity))

| Setting | Default | Effect |
|---|---|---|
| `Authentication/Registration/Enabled` | `true` | Master switch; the others only work when this is on. |
| `Authentication/Registration/OpenRegistrationEnabled` | `true` | Any anonymous visitor can create an account. Turn off for controlled access. |
| `Authentication/Registration/InvitationEnabled` | `true` | Invitation code redemption form. |
| `Authentication/Registration/RequiresInvitation` | n/a | Require invitation codes to register. |
| `Authentication/Registration/CaptchaEnabled` | `false` | Captcha on registration; create it to turn it on. |
| `Authentication/Registration/LocalLoginEnabled`, `ExternalLoginEnabled`, `RememberMeEnabled`, `ResetPasswordEnabled` | | Toggle each sign-in path. |
| `Authentication/LoginThrottling/*` | | Failed sign-in throttling (`IpAddressTimeoutTimeSpan`, `MaxAttemptsTimeLimitTimeSpan`, `MaxInvaildAttemptsFromIPAddress`, spelled as on Learn). |

Learn's security best practices: turn **open registration off** when access must be controlled,
don't use local authentication in production, and keep `AllowContactMappingWithEmail` **off**
unless email mapping is required (emails change and get reassigned). Microsoft's
`/audit-permissions` already flags open registration on non-SPA sites.

## Head / font injection (content snippets)

| Snippet | Effect |
|---|---|
| `Head/Bottom` | Inject markup/metadata at the end of `<head>`. |
| `Head/Fonts` | Add stylesheets/CSS to `<head>`. |

Auth-page copy snippets (`Account/SignIn/PageCopy`, `Account/Nav/SignIn`,
`Account/PasswordReset/ForgotPasswordFormHeading`, …) customize sign-in/reset text.

*Catalog credit: Oleksandr Olashyn (Dancing with CRM, and the MIT-licensed
[PowerAppsPortalSiteSettingsAndSnippets](https://github.com/OOlashyn/PowerAppsPortalSiteSettingsAndSnippets)
repo), who documents the obscure Power Pages settings and snippets. Sections marked **Learn** were
re-checked against Microsoft Learn in November 2026; the rest still need confirming on your site
version.*
