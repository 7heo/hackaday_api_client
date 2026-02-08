# hackaday_api_client
HackADay API Client in Python

## How to use

1. Log in to <https://dev.hackaday.io/>
2. Go to <https://dev.hackaday.io/applications>
3. Click on "Create Application"
4. Fill details in
5. in the file `~/.hackaday_api.json`, put a JSON object containing all the
    information returned by hackaday when you finish creating your application
6. Download both
   <https://raw.githubusercontent.com/7heo/hackaday_api_client/refs/heads/main/hackaday_api.py>
   and
   <https://raw.githubusercontent.com/7heo/hackaday_api_client/refs/heads/main/requirements.txt>
7. Put them in a directory, `cd` to it
8. From there, run `python -m venv .venv`
9. Then, `. .venv/bin/activate`
10. Then, `pip install -r requirements.txt`
11. Then, `./hackaday_api.py`
12. The script will open your default browser and have you click on a link that
    will lead to a hackaday.io page asking you to authorize "with scope" or
    "without scope". Select "with".

> [!TIP]
> When running the script, it will open your default browser. To figure out
> what it is, simply run `python -m webbrowser -t "https://www.python.org"` and
> see what browser python.org opens on.

If it works, you should see something like

```json
{
  "access_token": "l1XT50gxKdXr9VJHgBnZXW/G2DM13STb8hiK+qzUxq+Kqzo09URFr5MMhXIt9v0p",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "ifQkN53wZbES6jZR6RykcSgweEjDJHldA8E9cojUxNVNin5v0NA6l5aqlJMGxa+Q"
}
```

> [!CAUTION]
> The returned information is **CONFIDENTIAL**. Do not share it anywhere.

If it doesn't work, you should see a 403.

## Notes

if you want to check if your `~/.hackaday_api.json` file is correct, here is
the format is shall have:

```json
{
  "application_url": "<value>",
  "call_back_url": "<value>",
  "client_id": "<value>",
  "client_secret": "<value>",
  "api_key": "<value>",
  "description": "<value>",
}
```
