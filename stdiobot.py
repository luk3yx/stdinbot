#!/usr/bin/python3
#
# stdiobot
#

import subprocess, sys
from miniirc import IRC

# Variables
identity = None
# identity = '<username> <password>'

channel = '#channel'

ip = 'irc.example.com'
port = 6697

# Welcome!
print("Welcome to stdiobot!", file=sys.stderr)
irc = IRC(ip, port, 'stdiobot', channel, ns_identity=identity,
          auto_connect=False)


# Read stdin
@irc.Handler('001', colon=False)
def handle_stdin(irc, hostmask, args):
    for raw_line in iter(proc.stdout.readline, b''):
        msg = raw_line.decode('utf-8').rstrip('\n').replace('\n', '  ')
        if msg:
            irc.msg(channel, '\u200b' + msg)
    irc.disconnect()


@irc.Handler('PRIVMSG', colon=False)
def handle_stdout(irc, hostmask, args):
    if (args[0] == channel and args[1][0].isalnum() and
            '/services/' not in hostmask[2] and '/bot/' not in hostmask[2]):
        if '/' in args[1] or '.' in args[1]:
            irc.msg(channel, 'Sorry, you may not use "/" or "." in commands.')
            return

        proc.stdin.write(args[1].replace(';', '\n').encode('utf-8') + b'\n')
        proc.stdin.flush()


if __name__ == '__main__':
    proc = subprocess.Popen(sys.argv[1:], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    irc.connect()
    irc.wait_until_disconnected()
