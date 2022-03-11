## Physik Instrumente M-112 motorized stage with C-863 controller ##

This is a Python module for high-level operation of a 3D stage assembled with three M-112 motorized positioners (possibly also other M-1xx models) and three C-863 controllers from Physik Instrumente (PI). The controllers are connected in a daizy chain with only one USB interface towards the PC. The module automatically detects all controllers and initializes them.

It uses low-level modules `GCSDevice` and `pitools` from PI.
