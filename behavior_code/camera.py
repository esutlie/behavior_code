import pypylon.pylon as py
import time
import os
from pypylon._genicam import RuntimeException


def main():
    img = py.PylonImage()
    while True:
        tlf = py.TlFactory.GetInstance()
        devices = tlf.EnumerateDevices()
        if devices:
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
                        camera.ExposureTime.SetValue(50000)  # We dont actually need to set this again, its just so if
                        # the camera is unplugged it will raise a RuntimeExcception. Then the code will chill until
                        # the camera is plugged back in
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
            except RuntimeException:
                print('camera disconnected (probably)')
            except KeyboardInterrupt:
                camera.StopGrabbing()
                camera.close()
        else:
            time.sleep(1)

if __name__ == '__main__':
    main()
