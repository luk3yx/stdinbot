#!/usr/bin/python3

#
# Minetest player tracker
#
# © 2018 by luk3yx
#

import miniirc, os, time

# Create the IRC object
_irc = miniirc.IRC(
    'xeroxirc.net', 6697, 'trackr', ['#Edgy1'],
    realname = 'Minetest player tracker',
    ns_identity = 'username password',
    auto_connect = False
)

servers  = {}
admins   = {'invalid/your-hostmask-here'}
cooldown = 15

# Odd/even
plural = lambda n : '' if n == 1 else 's'

# Handle PRIVMSGs
last_list = 0
@miniirc.Handler('PRIVMSG')
def _handle_privmsg(irc, hostmask, args):
    global last_list
    nick = hostmask[0]
    msg  = args[-1][1:]

    # Check for join/leave/connected players messages
    if nick in servers:
        if args[-1].startswith(':***'):
            n = args[-1].split(' ', 3)
            if len(n) <= 2:
                return
            if n[2] == 'joined':
                servers[nick].add(n[1])
            elif n[2] == 'left' and n[1] in servers[nick]:
                servers[nick].remove(n[1])
            return
        elif args[-1].startswith(':Connected players: '):
            servers[nick] = set(args[-1][20:].replace(' ', '').split(','))
            if '' in servers[nick]:
                servers[nick].remove('')
            return

    # Check for MT players
    if msg.startswith('<'):
        n = msg.split(' ', 1)
        if len(n) > 1 and n[0].endswith('>') and n[0][1].isalnum():
            nick = '{}@{}'.format(n[0][1:-1], nick)
            msg  = n[1].strip()

    # Check for the players command
    if msg == '.players':
        t = time.time()
        if t <= last_list + cooldown:
            irc.msg(args[0], nick + ': You can only run \2.players\2 once',
                'every \2{} seconds\2.'.format(cooldown))
            return
        last_list = t

        # Get the player list
        total    = 0
        tplayers = 0
        for server in servers:
            if len(servers[server]) > 0:
                total    += 1
                tplayers += len(servers[server])
                players   = list(servers[server])
                players.sort()
                irc.msg(args[0], 'Players on \2{}\2: {}'.format(server,
                    ', '.join(players)))
                last_list += 0.5
                time.sleep(0.5)
        inactive = len(servers) - total
        irc.msg(args[0], ('Total: \2{} player{}\2 across \2{} active server{}\2'
            ' (and {} inactive server{}).').format(tplayers, plural(tplayers),
            total, plural(total), inactive, plural(inactive)))
    elif hostmask[-1] in admins and msg == (irc.nick + ': die'):
        irc.disconnect(hostmask[0] +
            ' ordered me to die- wait, why did I listen?')
        os._exit(0)

# Add a server
def add_server(irc, server):
    if type(server) != str:
        server = server[0]
    if server not in servers:
        servers[server] = set()
        irc.msg(server, 'players - If you are a human, report this to luk3yx.')

# Handle WHO replies
@miniirc.Handler('352')
def _handle_who(irc, hostmask, args):
    nick, status = args[-3:-1]
    if '+' in status:
        add_server(irc, nick)

# Hadle MODEs - This is primitive but should work
@miniirc.Handler('MODE')
def _handle_mode(irc, hostmask, args):
    if len(args) < 3 or not args[0].startswith('#'):
        return
    if args[1] == '+v':
        add_server(irc, args[2])
    elif args[1].startswith('+') and 'v' in args[1]:
        # Don't bother handling this and just send a WHO
        irc.quote('WHO', args[0])

# Handle JOIN of this bot
@miniirc.Handler('JOIN')
def _handle_join(irc, hostmask, args):
    if hostmask[0].lower() == irc.nick.lower():
        irc.quote('WHO', args[0])

# Handle PARTs and QUITs from MT servers
@miniirc.Handler('PART', 'QUIT')
def _handle_quit(irc, hostmask, args):
    if hostmask[0] in servers:
        del servers[hostmask[0]]

# Handle KICKs
@miniirc.Handler('KICK')
def _handle_kick(irc, hostmask, args):
    if args[-2] in servers:
        del servers[args[-2]]

_irc.persist = True
_irc.connect()
