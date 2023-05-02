# Anki2Toggl

Python script to automatically fill Toggl Track with Anki reviews.

## Recommended usages

### First usage (Export : Anki -> Toggl)

Properly configure the script as explained [below](#configuration), in particular the `ALL_REVIEWS_FROM_DTIME` setting which lets the script know from when it should start exporting Anki Reviews.

If you want to export all your Anki reviews, just switch the year from `2023` to `1789`.<br>They didn't have Anki back then, so you should be good 😜

### Frequent usage (Synchronization : Anki -> Toggl)

After the initial export, you can start using the script every day (or every week, or every month, or ...) after doing your Anki reviews to add new time entires in Toggl for your last Anki reviews.

If you feel fancy : Set up a scheduled task to run `py anki2toggl.py` automatically for you every evening.

## Configuration
I haven't taken the time to implement something proper for the configuration (yet?)... So I'll have you open and edit the python script directly (using your favorite notepad application : Notepad, Notepad++, Visual Code, etc.).

However, even if you are not a developer, it shouldn't be too complicated as I have put everything in a very obvious location at the top of the file. It's goign to be very difficult to miss 😉 Just look for this :
https://github.com/Y-LBG/Anki2Toggl/blob/602b14619a16c80d7dd899800c0e891f1512bfcf/anki2toggl.py#L12-L23

<details>
<summary>Details</summary>

| Variable | Description | ... |
|---|---|---|
| ANKI_PROFILE | Anki's profile from which you want to export the reviews<br><br>Default: `User 1` (Anki's default profile, if like me, you couldn't be bothered with modifying it) | If you don't know, simply press `Ctrl+Shift+P` (or go to `File` > `Switch Profile`) in Anki to find the list of profiles. |
| ALL_REVIEWS_FROM_DTIME | Date/Time (in ISO format[^1]) from which you want to export your Anki reviews.<br><br>Default: `2023-01-01T00:00:00Z` | All your reviews after that date/time will be synchronized from Anki to Toggl.<br>This date/time should only be useful for the very first synchronization. After that, it will only synchronize new Anki reviews. |
| BATCHING_ANKI_REVIEWS<br>_THRESHOLD_IN_SEC | Interval of time (in seconds) between 2 card reviews for which those should be considered as part of the same "review session".<br><br>Default: `120` (after testing, it seemed to produce the "better-looking" results in Toggl) | Indeed, Anki reviews are "per card".<br>However, you most probably don't want one time entry in Toggl for each card you reviewed.<br>This setting allows you to batch multiple, yet close (in time), Anki card reviews into a single time entry in Toggl.<br><br>If set to `0`, Anki card reviews won't get batched and will be exported as-is in Toggl. |
| API_TOKEN | Your Toggl API token. | More info on where to find it here : https://support.toggl.com/en/articles/3116844-where-is-my-api-key-located |
| WORKSPACE_NAME | Name of your Toggl workspace. | Can be found here : https://track.toggl.com/organization/workspaces |
| PROJECT_NAME | Name of the Toggl project in which the time entry will be added.<br><br>Default: `Priming` (Following Refold's recommendation[^2]) | Can be found here : https://track.toggl.com/projects/<br>The project should have been previously created in Toggl. |
| TIME_ENTRY_DESCRIPTION | Description of the created time entries.<br><br>Default: `Anki Review` (Following Refold's recommendation[^2]) | |
</details>

## How to get it ?

Right-click > "Save link as..." :
[anki2toggl.py](https://raw.githubusercontent.com/Y-LBG/Anki2Toggl/master/anki2toggl.py)

## How to run it ?

The first (obvious) step is to download and install Python.<br>
You can find that here : https://www.python.org/ > "Downloads"

Once the installation is over, open a command prompt (`Win+R` > type 'cmd' > `Enter`) and use the following command to verify the version :
```bash
py --version"
```
(The script was tested with Python 3.11.3, so anything greater than or equal to that should work fine.)

After that, you will most probably need to install some dependencies:
```bash
py -m pip install requests
```

And finally... Run it:
```bash
cd C:\path\where\you\downloaded\the\py\script\
py anki2toggl.py
```

## Troubleshooting

### sqlite3.OperationalError: database is locked
The script needs Anki to be closed to access the card reviews in Anki's database.

### requests.exceptions.HTTPError: 403 Client Error: XYZ
Verify your Toggl API Token is properly configured.

## Next steps

1. Turn that Anki2Toggl script into an Anki addon, which would simply run when closing Anki (similarly to the Anki synchronization with AnkiWeb)
2. See if I can contribute to the [asbplayer project](https://github.com/killergerbah/asbplayer/) to auto-start/stop a time entry in Toggl

[^1]: More info on the ISO 8601: https://en.wikipedia.org/wiki/ISO_8601
[^2]: Refold's video on time tracking with Toggl: https://www.youtube.com/watch?v=dm6RYK9J61k
