Building software for the Spikey neuromorphic System
====================================================

Configure, build and install:

    $ ./waf setup --project=deb-pynn@0.6
    $ ./waf configure
    $ ./waf install --targets=*

Run:

    $ . bin/env.sh # sourcing the environment variables
    $ python networks/example.py
