# Quickly-CARLA

Debug Tools for CARLA

![image](https://user-images.githubusercontent.com/35365764/209858504-7b4e4738-ddb1-47a3-aa80-9e1e59e8763c.png)

Firstly! Please git clone this repo  `${YOU_CARLA_PATH}/PythonAPI`

```bash
# exmaple in my computer
cd CARLA_0.9.14/PythonAPI
git clone https://github.com/kin-zhang/quickly-carla
```

Demo for this repo usage:

https://user-images.githubusercontent.com/35365764/209858346-9608bad7-a976-4615-bac8-98ca2211ff92.mp4

When you tried this repo, please make sure that you can run the official example like:

```bash
cd ~/CARLA_0.9.14/PythonAPI
python3 examples/manual_control.py
```

Test computer and System (py38):

- Desktop setting: i9-12900KF, GPU 3090, CUDA 11.3
- System setting: Ubuntu 20.04, **<u>Python 3.8</u>**
- Test Date: 2022/12/28, CARLA Version: 0.9.14, Using the system env python

## Install

```bash
cd ~/CARLA_0.9.14/PythonAPI
git clone https://github.com/Kin-Zhang/quickly-carla
pip install customtkinter glog webbrowser
python3 quickly-carla/start_gui.py
```

## Usage

![image](https://user-images.githubusercontent.com/35365764/209858782-b9e7ec20-0885-4eaf-9321-6e79df2c1c08.png)

① Correct your port, normally the default one is 2000 to CARLA servers

② Click Connect button and make sure the log print: `Connect the CARLA server successfully`

③ Change the rolename based on your setting on your ego vehicle, normally is `hero` or `ego_vehicle`

④ Click Find button, and make sure it find your car

Now, you can try everything like video shown at beginning. 

## Other infos

### Issue
1. tkgui cannot show great font.

   For some reasons https://github.com/corpnewt/ProperTree/issues/86, https://github.com/ContinuumIO/anaconda-issues/issues/776, https://github.com/TomSchimansky/CustomTkinter/issues/206:

    ```bash
    conda remove tk
    ```
    But it will cause [another problem](https://stackoverflow.com/questions/58758447/how-to-fix-module-platform-has-no-attribute-linux-distribution-when-instal), fixed by
    ```bash
    sudo apt remove python3-pip
    sudo python3.8 -m easy_install pip
    ```



### Acknowledgement

1. CARLA community: https://github.com/carla-simulator/carla
1. Python GUI: https://github.com/TomSchimansky/CustomTkinter

And welcome to contribute!!

✨✨Stargazers, positive feedback

---

[![Stargazers repo roster for @nastyox/Repo-Roster](https://reporoster.com/stars/Kin-Zhang/quickly-carla)](https://github.com/Kin-Zhang/OpenPCDet_ros/stargazers)
