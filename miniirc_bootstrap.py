#!/usr/bin/env python3
#
# Bootstraps pip if required and installs miniirc.
# Note that this is not required if you already have and know how to use pip,
#   simply run 'pip install miniirc' instead.
#
# © 2020 by luk3yx.
#

import importlib.util, os, shutil, subprocess, sys, tempfile, urllib.request

assert sys.version_info >= (3, 4)

# A horrible workaround for a partially existing distutils.
_distutils_usercustomize = """
# miniirc_bootstrap: Make user-provided packages load first.
# This can safely be removed if distutils has been properly installed.
import os, sys
dir = os.path.expanduser('~/.local/lib/python{}.{}/site-packages'.format(
    *sys.version_info[:2]))
if dir in sys.path:
    sys.path.remove(dir)
    sys.path.insert(0, dir)
del dir
# End of miniirc_bootstrap changes
""".lstrip()

# Debian has decided to remove distutils from Python installs by default.
# TODO: Make less assumptions about the system.
def bootstrap_distutils():
    """
    Bootstrap installs distutils on Debian systems. This is horrible and should
    probably be avoided if possible.
    """
    import glob, tarfile
    if importlib.util.find_spec('distutils.util') is not None:
        return

    print('[This should never happen] Downloading distutils...')
    if sys.platform != 'linux' or not shutil.which('apt-get'):
        raise NotImplementedError('Cannot bootstrap distutils on non-Debian '
            'systems!')

    partial_distutils = importlib.util.find_spec('distutils')

    # Get paths
    python = 'python{}.{}'.format(*sys.version_info[:2])
    pkg = 'python{}-distutils'.format(sys.version_info[0])

    local_lib = os.path.expanduser('~/.local/lib')
    if not os.path.isdir(local_lib):
        os.mkdir(local_lib)
    local_python = os.path.join(local_lib, python)
    if not os.path.isdir(local_python):
        os.mkdir(local_python)
    local_python = os.path.join(local_python, 'site-packages')
    if not os.path.isdir(local_python):
        os.mkdir(local_python)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download the package.
        subprocess.check_call(('apt-get', 'download', pkg), cwd=tmpdir)
        files = os.listdir(tmpdir)
        assert len(files) == 1, 'Error downloading .deb!'

        # Extract the downloaded .deb file.
        print('[This should never happen] Installing distutils...')
        subprocess.check_call(('ar', 'x', '--', files[0]), cwd=tmpdir)

        files = glob.glob(os.path.join(glob.escape(tmpdir), 'data.tar*'))
        assert len(files) == 1, 'Error extracting .deb!'
        with tarfile.open(files[0], 'r') as tarf:
            tarf.extractall(tmpdir)

        # Move distutils out of the extracted package.
        f = os.path.join(tmpdir, 'usr', 'lib', python, 'distutils')
        os.rename(f, os.path.join(local_python, 'distutils'))

    if partial_distutils is not None:
        # Symlink extra files.
        old_distutils = os.path.dirname(partial_distutils.origin)
        for fn in os.listdir(old_distutils):
            if not fn.endswith('.py'):
                continue
            dst = os.path.join(local_python, 'distutils', fn)
            if os.path.exists(dst):
                continue
            os.symlink(os.path.join(old_distutils, fn), dst)

        # A horrible tweak to make user-provided packages load before system ones.
        usercustomize = os.path.join(local_python, 'usercustomize.py')
        print('[This should never happen] Adding {}...'.format(usercustomize))
        with open(usercustomize, 'a') as f:
            # If the file already contains data write a leading newline.
            if f.tell():
                f.write('\n')

            # Write the custom distutils data.
            f.write(_distutils_usercustomize)

    print('[This should never happen] distutils should be installed!')

    # Recommend the user installs distutils correctly if possible.
    print(('If you have root access, please install {}, remove the '
        'changes made in {!r}, and delete {!r}.').format(pkg, usercustomize,
        os.path.join(local_python, 'distutils')), file=sys.stderr)

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

    if importlib.util.find_spec('distutils.util') is None:
        bootstrap_distutils()

    print('Downloading pip...')
    url = 'https://bootstrap.pypa.io/{}get-pip.py'

    # If this machine is using an obsolete Python, download the
    #   version-specific one.
    major, minor = sys.version_info[:2]
    pip = wget(url.format('{}.{}/'.format(major, minor)), raw=True)

    # Otherwise use the generic one.
    if not pip:
        pip = wget(url.format(''), raw=True)
        assert pip, 'Error downloading pip!'

    print('Installing pip...')
    fd, filename = tempfile.mkstemp()
    with open(fd, 'wb') as f:
        f.write(pip)
    del pip

    subprocess.call((sys.executable, '--', filename, '--user'))
    os.remove(filename)

    print('pip (should be) installed!')

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
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        if importlib.util.find_spec('pip') is not None:
            raise

        print('pip is (somehow) not installed!')
        bootstrap_pip()
        subprocess.check_call(args)

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
