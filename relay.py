#!/usr/bin/python3
#
# miniirc-based relay bot
#
# © 2018 by luk3yx
#

import miniirc, sys
from miniirc import IRC

# Variables
debug    = True

# Network list
networks = {
#   'Network Name': {
#       'ip':       'irc.servers.ip',
#       'port':     6697,
#       'nick':     'testing-relay',
#       'ignored':  {'lowercase-identifier'}, # Matched against nick, ident
#       '#channel': 'local-routing-name',     #     and host.
#   },
}

# Format strings
# formatstrings = {
#     'PRIVMSG': '<{host[0]}@{network}> {msg}',
#     'ACTION':  '* {host[0]}@{network} {msg}',
#     'JOIN':    '--> {host[0]}@{network} ({host[1]}@{host[2]}) has joined',
#     'PART':    '<-- {host[0]}@{network} ({host[1]}@{host[2]}) has left ({msg})',
#     'KICK':    '<-- {victim} has been kicked by {kicker} ({msg})',
#     'NICK':    ' -- {host[0]}@{network} ({host[1]}@{host[2]}) is now known as'
#         '{msg}',
#     'QUIT':    '<-- {victim} ({host[1]}@{host[2]}) has quit ({msg})'
# }

# This looks messy, but it creates nice coloured/colored strings.
_uh = '\x036(\x0310{{host[1]}}@{{host[2]}}\x036)'
_ = '\x03{0}{1}\x03 {{host[0]}}@{{network}} ' + _uh + \
    '\x03{0} has {2} \x036(\x0310{{msg}}\x036)'
_hn = '{host[0]}@{network}'
formatstrings = {
    'PRIVMSG': '<' + _hn + '> {msg}',
    'ACTION':  '* ' + _hn + ' {msg}',
    'JOIN':    _.format(3, '-->', 'joined').replace(' \x036(\x0310{msg}\x036)',
        ''),
    'PART':    _.format(4, '<--', 'left'),
    'KICK':    _.format(4, '<--', 'been yaykicked by {kicker}').replace(' ' +
        _uh.format(), '').replace('{host[0]}', '{victim}'),
    'NICK':    _.format(6, ' --', '{NICK}').replace('({msg})',
        '{msg}').replace('has {NICK}', 'is now known as'),
    'QUIT':    _.format(4, '<--', 'quit IRC')
}
del _
del _hn
del _uh

# Welcome!
print('Welcome to miniirc-relay!', file=sys.stderr)
is_channel = lambda channel : type(channel) == str and not channel[:1].isalnum()

# Parse the networks list and connect to any new IRC networks
_ircs   = {}
relayed = {}
def parse_networks():
    print('Parsing networks...', file=sys.stderr)
    relayed.clear()
    for name in networks:
        network = networks[name]

        channels = set()
        for channel in network:
            if is_channel(channel):
                lchan = channel.lower()
                if channel != lchan:
                    network[lchan] = network[channel]
                    del network[channel]
                    channel = lchan
                del lchan
                channels.add(channel)
                id = network[channel]
                if id not in relayed:
                    relayed[id] = {}
                relayed[id][name] = channel

        if not network.get(IRC):
            print('Connecting to {}...'.format(repr(name)), file=sys.stderr)
            network[IRC] = IRC(network['ip'], network['port'], network['nick'],
                channels, ns_identity = network.get('ns_identity'),
                debug = debug)
            network[IRC].debug('Channels on {}: {}'.format(repr(name),channels))
            _ircs[network[IRC]] = name
    print('Done.', file=sys.stderr)

# Check to see if a user is ignored.
def is_ignored(hostmask, network):
    if not networks.get(network) or not networks[network].get('ignored'):
        return
    for name in hostmask:
        if name.lower() in networks[network]['ignored']:
            networks[network][IRC].debug('Ignoring message from ' +
                repr(hostmask))
            return True
    return False

# Send a message to networks
def relay_message(irc, msg, channel=None):
    if not msg:
        return
    network = _ircs.get(irc)

    if channel:
        channel = channel.lower()
        irc.debug('Sending message from', channel, 'on', network)
        if not is_channel(channel) or channel not in networks[network]:
            return
        id = networks[network][channel]
        if id not in relayed:
            print('WARNING: Non-existent channel ID detected!', file=sys.stderr)
            parse_networks()
        to_relay = relayed[id]
        for n in to_relay:
            if n != network and networks[n].get(IRC):
                irc.debug('Relaying from', network, 'to', n, 'via', networks[n][IRC])
                networks[n][IRC].msg(to_relay[n], msg)
    else:
        for n in networks:
            if n != network and networks[n].get(IRC):
                for channel in networks[n]:
                    if is_channel(channel):
                        networks[n][IRC].msg(channel, msg)


# Handle PRIVMSGs
@miniirc.Handler('PRIVMSG', colon=False)
def handle_privmsg(irc, hostmask, args):
    text = args[-1]
    msg = None
    net = _ircs.get(irc)
    if is_ignored(hostmask, net):
        return

    if text == '\x01ACTION\x01' or (text.startswith('\x01ACTION ')
      and text.endswith('\x01')):
        msg = formatstrings['ACTION'].format(host=hostmask, network=net,
            msg=text[8:-1])
    elif not text.startswith('\x01'):
        msg = formatstrings['PRIVMSG'].format(host=hostmask, network=net,
            msg=text)

    relay_message(irc, msg, args[0])

# Handle JOINs
@miniirc.Handler('JOIN', colon=False)
def handle_join(irc, hostmask, args):
    net = _ircs.get(irc)
    if is_ignored(hostmask, net):
        return
    if net:
        msg = formatstrings['JOIN'].format(host=hostmask, network=net)
        relay_message(irc, msg, args[0])

# Handle PARTs
@miniirc.Handler('PART', colon=False)
def handle_part(irc, hostmask, args):
    net = _ircs.get(irc)
    if is_ignored(hostmask, net):
        return
    if net:
        msg = formatstrings['PART'].format(host=hostmask, network=net,
            msg=args[-1])
        relay_message(irc, msg, args[0])

# Handle PARTs
@miniirc.Handler('KICK', colon=False)
def handle_part(irc, hostmask, args):
    net = _ircs.get(irc)
    if is_ignored(hostmask, net):
        return
    if net:
        msg = formatstrings['KICK'].format(victim=args[-2], network=net,
            kicker=hostmask[0], msg=args[-1])
        relay_message(irc, msg, args[0])

# Handle QUITs
@miniirc.Handler('QUIT', colon=False)
def handle_quit(irc, hostmask, args):
    net = _ircs.get(irc)
    if is_ignored(hostmask, net):
        return
    if net:
        msg = formatstrings['QUIT'].format(host=hostmask, network=net,
            msg=args[-1] if args else '')
        relay_message(irc, msg)

# Handle NICKs
@miniirc.Handler('NICK', colon=False)
def handle_quit(irc, hostmask, args):
    net = _ircs.get(irc)
    if is_ignored(hostmask, net):
        return
    if net:
        msg = formatstrings['NICK'].format(host=hostmask, network=net,
            newnick=args[0])
        relay_message(irc, msg)

# Parse the network list
parse_networks()
