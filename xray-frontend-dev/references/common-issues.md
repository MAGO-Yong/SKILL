# Common Issues

## Login Loop In Local Environment

If the local app keeps redirecting to login repeatedly, check Chrome cookies first.

Steps:
1. Open Chrome DevTools.
2. Open `Application`.
3. Open `Cookies`.
4. Find the cookie values related to the current environment.

Rules:
- If the user wants to debug with production data, copy the value of `common-internal-access-token-prod` to `access-token-local.xiaohongshu.com`.
- If the user wants to debug with SIT data, copy the value of `common-internal-access-token-sit` to `access-token-local.xiaohongshu.com`.

When this issue appears, check cookie alignment before changing business code.

## Debug With Production Data

To debug with production data:
1. Update the relevant proxy target in the sub-application's `formula.config.ts`.
2. Ensure the local cookie also uses the production token configuration.
3. Reuse the cookie handling steps in `Login Loop In Local Environment`.

Do not switch only the proxy without also checking the cookie environment, because mixed environments can cause login or data access issues.

## Default Troubleshooting Order

1. Check `/etc/hosts`.
2. Check Node.js and pnpm versions.
3. Check whether the package-level dev command starts correctly.
4. Check `formula.config.ts` proxy targets.
5. Check local cookies when login or environment data looks wrong.
