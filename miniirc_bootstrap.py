#!/usr/bin/env python3
#
# Bootstraps pip if required and installs miniirc.
# Note that this is not required if you already have and know how to use pip,
#   simply run 'pip install miniirc' instead.
#
# © 2019 by luk3yx.
#

import importlib.util, os, subprocess, sys, tempfile, urllib.request

assert sys.version_info >= (3, 4)

# Download a webpage
def wget(url, raw=False):
    try:
        with urllib.request.urlopen(url) as f:
            if raw:
                return f.read()
            else:
                return f.read().decode('utf-8', 'replace')
    except urllib.request.HTTPError:
        return ''

def bootstrap_pip():
    """
    Bootstrap installs pip. This will print messages to stdout/stderr.

    This is required because some versions of Ubuntu do not have pip or
    ensurepip installed with Python by default.
    """

    print('[This should never happen] Downloading pip...')
    url = 'https://bootstrap.pypa.io/{}get-pip.py'

    # If this machine is using an obsolete Python, download the
    #   version-specific one.
    major, minor = sys.version_info[:2]
    pip = wget(url.format('{}.{}/'.format(major, minor)), raw=True)

    if not pip:
        # Apparently a Python3.4-specific pip doesn't exist yet, so download
        #   the Python 3.3 one and upgrade.
        if major == 3 and minor == 4:
            pip = wget(url.format('3.3/'), raw=True)
        else:
            pip = wget(url.format(''), raw=True)
        assert pip, 'Error downloading pip!'

    print('[This should never happen] Installing pip...')
    fd, filename = tempfile.mkstemp()
    with open(fd, 'wb') as f:
        f.write(pip)
    del pip

    subprocess.call((sys.executable, '--', filename, '--user'))
    os.remove(filename)

    if major == 3 and sys.version_info.minor == 4:
        print('[This should never happen] Upgrading pip...')
        pip_install('pip', upgrade=True)

    print('[This should never happen] pip (should be) installed!')

# Install a package
def pip_install(*pkgs, upgrade=False):
    """
    Installs or upgrades packages using pip. `pip` will print to stdout/stderr.

    This automatically calls bootstrap_pip() if required.
    """

    args = [sys.executable, '-m', 'pip', 'install']
    if upgrade:
        args.append('--upgrade')
    args.extend(('--user', '--'))
    args.extend(pkgs)
    try:
        assert subprocess.call(args) == 0
    except (AssertionError, subprocess.CalledProcessError):
        if importlib.util.find_spec('pip') is not None:
            raise

        print('pip is (somehow) not installed!')
        bootstrap_pip()
        assert subprocess.call(args) == 0

# Install miniirc
def main():
    # Do nothing if arguments are specified.
    import argparse
    argparse.ArgumentParser().parse_args()

    # Get miniirc
    upgrade = True
    try:
        import miniirc
    except ImportError:
        upgrade = False

    pip_install('miniirc', upgrade=upgrade)
    print('miniirc (should be) installed!')

if __name__ == '__main__':
    main()
