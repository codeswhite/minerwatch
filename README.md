## MineWatch
Get telegram notifications about disconnections and other performance losses in your `ethermine.org` pool

The script will constantly watch your address of the pool for identifying issues with your workers, for example: 
* Active workers count decreased (worker/s disconnected)
* Stale shares percentage increased
* Reported hashrate decreased

If the user requested to get notified of a particular issue then the program will dispatch a message once it occurs.

### How it works?
We perform timed requests to `https://api.ethermine.org/` and compare each response with the cached previous response, to create a differential data structure.

### Notification Dispatch
Currently we only support `Telegram` but further support for discord, slack and other API-enabled messaging services is welcome to be pull-requested :)
If you are interested in a particular service integration please open an issue.

## Running
Instructions on getting everything ready and running the project

### Requirements
- `python3` with `pip` and `requests` library

### Clone

    $ git clone https://github.com/codeswhite/minerwatch
    $ cd minerwatch

### Install locally (with non-root privileges)

    $ pip3 install .

### Running as a normal user

    $ minerwatch -h

### Systemd
To use the script as a systemd service one needs to:

Symlink `minerwatch.service` file into user systemd services directory

    $ cd minerwatch && ln -s "$(pwd)/minerwatch.service" ~/.config/systemd/user/

Then reload the daemon to ensure the service file have beed loaded

    $ systemctl --user daemon-reload

And start the service:

    $ systemctl --user start minerwatch

To automatically run the service on boot `enable` the service:

    $ systemctl --user enable minerwatch

### Logging
By default we log into STDOUT, To specify log target use `--log-file` option.
For additional data in your log use `--debug` option.

### More pools
Currently only `ethermine.org` is supported, but integral support for more pools is possible, so open an issue if you are interested in such development.