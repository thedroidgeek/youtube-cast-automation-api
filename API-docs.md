## GET /SetTvHost/`<host>`
Sets the TV hostname/IP, this is set to `tizen` by default.

## GET /WakeTv
Broadcasts Wake-on-LAN packets to attempt to wake the TV up.

## GET /PlayYtQuery/`<query>`
Attempts to wake up the TV, launches the YouTube app on it, retreives the `loungeToken`, does a YouTube search for the `query` parameter, then proceedes to queue the 10 first video results on the TV while starting with the first one.

## GET /SetDisplayName/`<name>`
Sets the YouTube remote display name (the notification that shows up on connection).

## GET /SetTvMac/`<macAddr>`
Manually sets the TV's mac address (usually obtained automatically), which is used for WoL purposes.

## GET /ClearTvMac
Clears the previously set mac address, so that it's detected automatically the next time it's needed.
