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

# miniirc

A simple IRC client framework.

The miniirc framework is now on a separate repo
([GitLab](https://gitlab.com/luk3yx/miniirc),
[GitHub](https://github.com/luk3yx/miniirc))
and can be installed via pip
with `sudo -H pip3 install miniirc`.
