Building software for the Spikey neuromorphic System
====================================================

Configure, build and install:

    $ ./waf setup --project=deb-pynn@0.6
    $ ./waf configure
    $ ./waf install --targets=*

Run:

    $ . bin/env.sh # sourcing the environment variables
    $ python networks/example.py

During installation the following github repositories are automatically cloned:

* [electronicvisions/PyNN](https://github.com/electronicvisions/PyNN)
* [electronicvisions/spikeyhal](https://github.com/electronicvisions/spikeyhal)
* [electronicvisions/vmodule](https://github.com/electronicvisions/vmodule)
* [electronicvisions/logger](https://github.com/electronicvisions/logger)

For information about the Spikey neuromorphic system see http://www.kip.uni-heidelberg.de/spikey.
