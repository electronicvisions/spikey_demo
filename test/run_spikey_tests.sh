pushd ./

if [ "$PYNN_HW_PATH" = "" ] || [ "$SPIKEYHALPATH" = "" ]; then
  echo "environment variables not set"
  exit 1
fi

cd $SPIKEYHALPATH
cd ..
PROJECTPATH=$(pwd -P)

if [ "$PYNN_HW_PATH_TEST" = "" ]; then
  cd $PYNN_HW_PATH
  cd ../../../test/spikey
  PYNN_HW_PATH_TEST=$(pwd -P)
fi

#TP (19.05.2015): next two lines are required, otherwise following ADC test will fail
#remove when bug fixed, see issue #1718
cd $PYNN_HW_PATH_TEST/system
nosetests test_empty_exp.py || true

cd $PROJECTPATH/bin
echo "starting ADC tests"
#get config for station
if [ "$MY_STAGE1_STATION" != "" ]; then
  echo "loading station config according to environment variable MY_STAGE1_STATION"
  STATION=$MY_STAGE1_STATION
  SERIAL=$(sed '1!d' $SPIKEYHALPATH/config/$STATION.cfg)
  BOARD=$(sed '2!d' $SPIKEYHALPATH/config/$STATION.cfg)
else
  echo "loading station config according to connected USB device"
  cd $SPIKEYHALPATH
  SERIAL=$(lsusb -v -d 04b4:1003 | grep iSerial | awk '{print $3}')
  for CONFIGFILE in $(find ./config -iname "*.cfg"); do
    SERIALTEMP=$(head -1 $CONFIGFILE);
    if [ $SERIALTEMP = $SERIAL ]; then
      SERIAL=$(sed '1!d' $CONFIGFILE)
      BOARD=$(sed '2!d' $CONFIGFILE)
    fi
  done
fi

#run tests
cd $PROJECTPATH/bin
./readout_adc_spikey $BOARD $SERIAL 4 || { popd; exit 1; }
./readout_adc_spikey $BOARD $SERIAL 0 8 || { popd; exit 1; }

cd $PROJECTPATH/bin/tests
./test-main --gtest_filter=-*runDecorrNetworkInf --gtest_output="xml:report-spikeyHAL.xml" || true

cd $PYNN_HW_PATH_TEST/system
sh run_test_system.sh
sh run_test_plasticity.sh

popd
