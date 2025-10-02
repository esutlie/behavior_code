import pypylon.pylon as py
import matplotlib.pyplot as plt
import numpy as np
import time
import os


# definition of event handler class
class TriggeredImage(py.ImageEventHandler):
    def __init__(self):
        super().__init__()
        self.grab_times = []

    def OnImageGrabbed(self, camera, grabResult):
        self.grab_times.append(grabResult.TimeStamp)


def main():
    img = py.PylonImage()

    camera = py.InstantCamera(py.TlFactory.GetInstance().CreateFirstDevice())
    print("Using device ", camera.GetDeviceInfo().GetModelName())

    camera.Open()
    camera.UserSetSelector = "Default"
    camera.UserSetLoad.Execute()

    camera.LineSelector = "Line4"
    camera.LineMode = "Input"
    camera.TriggerSelector = "FrameStart"
    camera.TriggerSource = "Line4"
    camera.TriggerMode = "On"

    camera.ExposureTime.SetValue(50000)
    camera.StartGrabbing(py.GrabStrategy_OneByOne)
    last_frame_time = 0
    root = os.path.join('C:\\', 'video_data')
    path = os.path.join(root, 'test')
    if not os.path.isdir(path):
        os.mkdir(path)
    frame_number = 0
    need_new = True

    try:
        while True:
            if camera.GetGrabResultWaitObject().Wait(0):
                grab = camera.RetrieveResult(0, py.TimeoutHandling_Return)
                img.AttachGrabResultBuffer(grab)
                print(f'test frame = {frame_number}')
                if need_new:
                    path = os.path.join(root, time.strftime("%Y-%m-%d_%H-%M-%S"))
                    os.mkdir(path)
                    frame_number = 0
                    need_new = False
                ipo = py.ImagePersistenceOptions()
                ipo.SetQuality(50)
                timestamp = str(grab.TimeStamp)
                zeros = ['0'] * (20 - len(timestamp))
                timestamp = ''.join(zeros) + timestamp
                img.Save(py.ImageFileFormat_Jpeg, os.path.join(path, timestamp + '.jpeg'), ipo)

                last_frame_time = time.time()
                frame_number += 1
            if time.time() - 5 > last_frame_time and not need_new:
                need_new = True

    except:
        camera.StopGrabbing()
    camera.close()


def check_input():
    # open the camera
    tlf = py.TlFactory.GetInstance()
    cam = py.InstantCamera(tlf.CreateFirstDevice())
    print("Using device ", cam.GetDeviceInfo().GetModelName())

    cam.Open()
    # enable the chunk that
    # samples all IO lines on every FrameStart
    cam.ChunkModeActive = True
    cam.ChunkSelector = "LineStatusAll"
    cam.ChunkEnable = True

    # set max speed
    cam.Height = cam.Height.Min
    cam.Width = cam.Width.Min
    cam.ExposureTime = cam.ExposureTime.Min

    # limit to 1khz
    cam.AcquisitionFrameRateEnable = True
    cam.AcquisitionFrameRate = 1000

    print(cam.ResultingFrameRate.Value)
    cam.StartGrabbingMax(1000)

    io_res = []
    while cam.IsGrabbing():
        with cam.RetrieveResult(1000) as res:
            time_stamp = res.TimeStamp
            io_res.append((time_stamp, res.ChunkLineStatusAll.Value))

    cam.StopGrabbing()

    # simple logic analyzer :-)

    # convert to numpy array
    io_array = np.array(io_res)
    # extract first column timestamps
    x_vals = io_array[:, 0]
    #  start with first timestamp as '0'
    x_vals -= x_vals[0]

    # extract second column io values
    y_vals = io_array[:, 1]
    # for each bit plot the graph
    for bit in range(8):
        logic_level = ((y_vals & (1 << bit)) != 0) * 0.8 + bit
        # plot in seconds
        plt.plot(x_vals / 1e9, logic_level, label=bit)

    plt.xlabel("time [s]")
    plt.ylabel("IO_LINE [#]")
    plt.legend()
    plt.show()

    # This next bit should grab on of the images
    # get clean powerup state
    cam.UserSetSelector = "Default"
    cam.UserSetLoad.Execute()

    cam.LineSelector = "Line4"
    cam.LineMode = "Input"
    cam.TriggerSelector = "FrameStart"
    cam.TriggerSource = "Line4"
    cam.TriggerMode = "On"
    print(cam.TriggerActivation.Value)
    res = cam.GrabOne(py.waitForever)

    #     https://github.com/basler/pypylon-samples/blob/c3e323c07b0e0efaf59a85685d35ff36056d2ef9/notebooks/USB_hardware_trigger_and_chunks.ipynb
    # create event handler instance
    image_timestamps = TriggeredImage()

    # register handler
    # remove all other handlers
    cam.RegisterImageEventHandler(image_timestamps,
                                  py.RegistrationMode_ReplaceAll,
                                  py.Cleanup_None)

    # start grabbing with background loop
    cam.StartGrabbingMax(100, py.GrabStrategy_LatestImages, py.GrabLoop_ProvidedByInstantCamera)
    # wait ... or do something relevant
    while cam.IsGrabbing():
        time.sleep(0.1)
    # stop grabbing
    cam.StopGrabbing()
    np.diff(image_timestamps.grab_times)
    frame_delta_s = np.diff(np.array(image_timestamps.grab_times)) / 1.e9
    plt.plot(frame_delta_s, ".")
    plt.axhline(np.mean(frame_delta_s))
    plt.show()

    plt.hist(frame_delta_s - np.mean(frame_delta_s), bins=100)
    plt.xticks(rotation=45)
    plt.show()
    cam.Close()


if __name__ == '__main__':
    check_input()
