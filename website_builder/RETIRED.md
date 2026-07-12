# Retired — Hotel CMS is RevNextCMS

This Django app is **no longer mounted**.

- Runtime: `cms.revnext.in` / `app.revnext.in` (RevNextCMS VPS `84.247.183.69`)
- Billing: ChannelManager product code `cms` (`cms_starter` / `cms_pro` / `revnext_suite`)
- Legacy paths `/website-builder/` and `/api/website-builder/` redirect via
  `products.middleware.ProductHostMiddleware` to the RevNextCMS launch URL

Do not re-add `website_builder` to `INSTALLED_APPS`. See
`docs/PLATFORM_HOSTS.md` and RevNextCMS `docs/channel-manager-cms-bridge.md`.
