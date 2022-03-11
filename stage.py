from pipython import GCSDevice
from pipython import pitools

import atexit

class StageController3D:
    """Class that represents exactly three C-863 controllers in a daisy chain.
    Units are in [mm]
    """

    def __init__(self):
        # Create three objects for three stages
        self.devs = [GCSDevice('C-863'), GCSDevice('C-863'), GCSDevice('C-863')]

        # Get a descriptor of the directly attached controller
        descriptors = self.devs[0].EnumerateUSB()
        if len(descriptors) < 1:
            print("Could not connect to any controller")
            exit()
        print(f"Directly attached controller: {descriptors[0]}")

        # Open the directly attached controller (daisy chain master):
        print("Searching for devices in the daisy chain...")
        self.chaindevs = self.devs[0].OpenUSBDaisyChain(description=descriptors[0])
        # Registers the disconnect method to release the driver at exit
        atexit.register(self.disconnect)
        print("Found chained devices:")
        self.devnums = []
        for i, strng in enumerate(self.chaindevs):
            if "not connected" in strng:
                continue
            self.devnums.append(i+1) # DeviceID is a 1-based index
            print(f"Address {i}: {strng}")
        print("\n\n")

        self.rangemin = []
        self.rangemax = []
        self.default_axis = []
        # Open and initialize all controllers in the chain:
        daisychainid = self.devs[0].dcid
        for i in range(len(self.devnums)):
            self.devs[i].ConnectDaisyChainDevice(self.devnums[i], daisychainid)
            default_axis = self.devs[i].axes[0]
            self.default_axis.append(default_axis)
            self.rangemin.append(self.devs[i].qTMN()[default_axis])
            self.rangemax.append(self.devs[i].qTMX()[default_axis])
            # Turning on servo feed-back loop
            self.devs[i].send('SVO 1 1')
            # Calibrating using reference position
            # Referenced? 
            # FRF?
            # 0 - no
            # 1 - yes
            self.devs[i].send('RON 1 1')
            self.devs[i].send('FRF 1')

        for i in range(len(self.devnums)):
            pitools.waitontarget(self.devs[i])


    def move_absolute(self, devid, target, axis=None, wait=True):
        """
        @param devid: Device ID (0..2)
        @param target: Absolute position to move to in [mm]
        @param axis: Axis ID to move. Can be omitted for one-axis devices.
        """
        if axis is None:
            axis = self.default_axis[devid]

        self.devs[devid].MOV(axis, target)

        if wait:
            pitools.waitontarget(self.devs[devid])


    def move_relative(self, devid, amount, axis=None, wait=True):
        """
        @param devid: Device ID (0..2)
        @param amount: Relative distance to move in [mm]. Can be negative.
        @param axis: Axis ID to move. Can be omitted for one-axis devices.
        """
        self.move_absolute(self.get_position(devid, axis) + amount, axis=axis, wait=wait)


    def get_position(self, devid, axis=None):
        """
        @param devid: Device ID (0..2)
        @param axis: Axis ID to move. Can be omitted for one-axis devices.
        @return: Current position in [mm]
        """
        if axis is None:
            axis = self.default_axis[devid]
        return self.devs[devid].qPOS(axis)[axis]


    def get_axes(self, devid):
        return self.devs[devid].axes


    def wait(self, devid):
        """
        Wait till stage stops moving
        @param devid: Device ID (0..2)
        """
        pitools.waitontarget(self.devs[devid])


    def disconnect(self):
        print("Disconnecting PI C-863 controllers...")
        self.devs[0].CloseDaisyChain()
        print("Done")



class Stage3D():
    """
    This contains 3 x StageController.
    The default axis of the StageController will be used
    """
    x_axis = 0
    y_axis = 1
    z_axis = 2
    axes = (x_axis, y_axis, z_axis)

    def __init__(self):
        self.stage = StageController3D()

    def move_absolute(self, axis, target, wait=True):
        self.stage.move_absolute(axis, target, wait=wait)

    def move_relative(self, axis, amount, wait=True):
        self.stage.move_relative(axis, amount, wait=wait)

    def get_position(self, axis):
        return self.stage.get_position(axis)

    def move_absolute_3D(self, position, wait=True):
        """
        Moves all axes simultaneously to a position
        @param position: tuple (x, y, z)
        """
        for axis, value in zip(self.axes, position):
            self.stage.move_absolute(axis, value, wait=False)
        if wait:
            for axis in self.axes:
                self.stage.wait(axis)

    def get_position_3D(self):
        """
        @return: tuple of coordinates (x, y, z)
        """
        return [self.get_position(axis) for axis in self.axes]

    def move_relative_3D(self, amount, wait=True):
        """
        @param amount: Tuple (x, y, z) of relative distances to move in [mm]. Values can be negative.
        """
        self.move_absolute_3D([a + b for a, b in zip(self.get_position_3D(), amount)], wait=wait)



if __name__ == '__main__':
    stage = Stage3D()
    stage.move_absolute_3D((20.0, 20.0, 20.0))
