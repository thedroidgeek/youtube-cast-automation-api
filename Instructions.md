## IFTTT + Google Assistant Instructions (DEPRECATED)

#### UPDATE: As of August 31, 2022, this integration is no longer possible due to [Google's changes](https://ifttt.com/explore/google-assistant-changes) (variable input on commands is no longer supported).

0. Make sure you have Python 3
1. `git clone https://github.com/thedroidgeek/youtube-cast-automation-api`
2. `cd youtube-cast-automation-api && pip3 install -r requirements.txt`
3. Start the API server - `python3 server.py` `<host>` `<port>`
4. Expose it to the internet - either port forward + dynamic DNS, or use a reverse proxy service such as [ngrok](https://ngrok.com/) and [localtunnel](https://localtunnel.me/) (but make sure the URL doesn't change)
5. Sign up for [IFTTT](https://ifttt.com/user/new) and link your Google account.
6. [Create](https://ifttt.com/create) a new applet.
7. For the condition (if this), pick Google Assistant.
8. Pick 'Say a phrase with a text ingredient'.
9. Fill out the form, where `$` is the YouTube search query.
10. In the next step (then that), choose Webhooks as an action.
11. In the URL field, do as so (with your own `publicurl`), and leave the other fields as default):

![a](https://i.0x41.cf/E9ECyCQ.gif)

12. Review, and deploy your applet.
