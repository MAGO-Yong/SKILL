# Web Article Access

Use this reference when a public article page blocks static fetches or needs browser state.

## WeChat Official Accounts

Observed on 2026-05-16 with `mp.weixin.qq.com/s/pOF5IqIj9i8iNml9GjXvcw`:

- `curl` and Jina may return an environment verification page instead of the article.
- Opening the same URL in the user's normal Chrome can render the article successfully.
- If Chrome AppleScript JS is disabled, enable it from `View > Developer > Allow JavaScript from Apple Events`.
- Do not silently replace the WeChat original with a search result, mirror page, or official repost. If a fallback source is used, explicitly label it as a fallback and do not present it as the original article.
- After enabling, verify with:

```bash
osascript -e 'tell application "Google Chrome" to get {title, URL} of active tab of window 1'
osascript -e 'tell application "Google Chrome" to tell active tab of window 1 to execute javascript "document.body.innerText"'
```

If AppleScript points at the wrong Chrome window, list all windows and tabs first:

```bash
osascript -e 'tell application "Google Chrome"' \
  -e 'set out to ""' \
  -e 'repeat with w from 1 to count of windows' \
  -e 'set out to out & "WINDOW " & w & linefeed' \
  -e 'repeat with t from 1 to count of tabs of window w' \
  -e 'set out to out & t & " | " & title of tab t of window w & " | " & URL of tab t of window w & linefeed' \
  -e 'end repeat' \
  -e 'end repeat' \
  -e 'out' \
  -e 'end tell'
```

Use short excerpts in the final answer. Do not paste a full article unless the user explicitly asks and copyright limits allow it.

## Required Completion Check

Before reporting that a WeChat article has been read, answer these internally:

- Did I extract text from the original `mp.weixin.qq.com` page rendered in the user's Chrome?
- If not, did I try Chrome/AppleScript/CDP before using a fallback?
- If I used a fallback source, did I name it clearly and avoid presenting it as the WeChat original?
- Did I provide a title or short snippet from the source I actually read?
