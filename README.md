# Quickly-CARLA

Firstly! Please git clone this repo  `${YOU_CARLA_PATH}/PythonAPI`

```bash
# exmaple in my computer
cd CARLA_0.9.14/PythonAPI
git clone https://github.com/kin-zhang/quickly-carla
```

Demo for this repo usage:

- [ ] TODO attach the video here

When you tried this repo, please firstly successfully run the official example like:

```bash
cd CARLA_0.9.14/PythonAPI
python3 examples/manual_control.py
```

Test computer and System (py38):

- Desktop setting: i9-12900KF, GPU 3090, CUDA 11.3
- System setting: Ubuntu 20.04, **<u>ROS noetic (Python 3.8)</u>**
- Test Date: 2022/12/28, CARLA Version: 0.9.14, Using the system env python 3.8



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

1. Python GUI: https://github.com/TomSchimansky/CustomTkinter



✨✨Stargazers, positive feedback

---

[![Stargazers repo roster for @nastyox/Repo-Roster](https://reporoster.com/stars/Kin-Zhang/quickly-carla)](https://github.com/Kin-Zhang/OpenPCDet_ros/stargazers)
