#!/usr/bin/python3

#
# Example miniirc-based bot
#
# © 2018 by luk3yx
#

import miniirc, sys
assert miniirc.ver >= (1,4,0), 'This bot requires miniirc >= v1.4.0.'

# Variables
nick     = 'miniirc-test' + str(hash('.'))[1:4] # Make a unique(-ish) nickname
ident    = nick
realname = 'Example miniirc bot - https://gitlab.com/luk3yx/stdinbot'
identity = None
# identity = '<username> <password>'
debug    = False
channels = ['#lurk']
prefix   = '`'

ip = 'xeroxirc.net'
port = 6697

# Welcome!
print('Welcome to {}!'.format(nick), file=sys.stderr)
irc = IRC(ip, port, nick, channels, ident=ident, realname=realname,
    ns_identity=identity, debug=debug, auto_connect=False)

# Handle normal messages
# This could probably be better than a large if/else statement.
@irc.Handler('PRIVMSG', colon=False)
def handle_privmsg(irc, hostmask, args):
    channel = args[0]
    text = args[-1].split(' ')
    cmd = text[0].lower()
    # Unprefixed commands here
    if cmd.startswith('meep'):
        irc.msg(channel, '\u200bMeep!')
    elif cmd.startswith(prefix):
        # Prefixed commands
        cmd = cmd[len(prefix):]
        if cmd == 'yay':
            irc.msg(channel, '\u200bYay!')
        elif cmd == 'rev':
            if len(text) > 1:
                irc.msg(channel, "{}: {}".format(hostmask[0],
                    ' '.join(text[1:])[::-1]))
            else:
                irc.msg(channel, 'Invalid syntax! Syntax: ' + prefix +
                    'rev <string>')
        elif cmd == 'about':
            irc.msg(channel,
                'I am {}, an example miniirc bot.'.format(irc.nick))

# Connect
if __name__ == '__main__':
    irc.connect()
