#! /bin/bash
# This is a very simplistic install scipt. Use with care!

if [ -z $1 ] && [ "$1" = "--system" ]; then
  ./uninstall.sh --system
  (cd ext; python setup.py install)
  python setup.py install
  ./cleanfiles.sh
  (cd ext; ./cleanfiles.sh)
else
  ./uninstall.sh
  (cd ext; python setup.py install --home=$HOME)
  python setup.py install --home=$HOME
  ./cleanfiles.sh
  (cd ext; ./cleanfiles.sh)
  echo "Don't forget to add 'export PYTHONPATH=$HOME' to your .bashrc file."
fi

