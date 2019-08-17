# stdinbot

A collection of miniirc bots.

## stdinbot.py

A stupidly simple IRC bot to interact with stdin.

## example.py

An example miniirc bot. If you want to make your own bot, you can use this as
the base.

## relay.py

A miniirc-based relay bot. Edit the networks list before using.

## minetest-trackr.py

Made for IRC channels with lots of Minetest servers, where only Minetest servers
are voiced, and will allow IRC users to run `.players` to get a list of players
on all the servers without flooding the channel (as badly as requesting a player
list from every server). Currently not cross-channel and will ignore devoices.

# Python scripts/applications that aren't strictly bots

## miniirc_bootstrap.py

Automatically installs pip (if required) and then runs
`pip install --upgrade miniirc`. This should work if `pip` isn't in your PATH
or if the `pip` in your PATH is for a different Python version.

**You do not need this if you already have and know how to install packages
with pip.**

## lua.py

A wrapper around [lupa](https://github.com/scoder/lupa) to make creating
miniirc bots with lua easier. This may move eventually.

Dependencies: `sudo pip3 install lupa>=1.8 miniirc_extras miniirc>=1.4.0`

### Usage

```
./lua.py <path to lua file>
```

This lua file will be able to use the `miniirc` global variable. `IRC` objects
are not called with `:` (`irc.msg(...)` instead of `irc:msg(...)`). *Remember
that lua table indexes start with 1 and not 0.*

#### `await`

Handlers are executed inside coroutines and an `await` function is created, so
that Python functions can be called without blocking the lua thread. The main
lua file can return a function that will be called inside a coroutine.

```lua
await(blocking_python_function, parameters)
await{blocking_python_function, parameters, keyword='argument'}
```

*Note: `await`ing a lua function is pointless and will still block the lua
thread.*

#### `sleep`

The same syntax as `time.sleep`, doesn't block the lua thread if called inside
a coroutine.

# miniirc

A simple IRC client framework.

The miniirc framework is now on a separate repo
([GitLab](https://gitlab.com/luk3yx/miniirc),
[GitHub](https://github.com/luk3yx/miniirc))
and can be installed via pip
with `sudo -H pip3 install miniirc`.
