#_______________________________________________________________________
# create executable needed by planar hydrostatic mountain wave (native output)

thetal_setup()
#              name                 target NP  NC PLEV USE_PIO  WITH_ENERGY QSIZE_D
createTestExec(theta-l-nlev200-native         theta-l  4   4  200   TRUE    TRUE       3       )
