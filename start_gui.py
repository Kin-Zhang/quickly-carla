#!/usr/bin/env python

# Created: 2022-12-28 15:10
# Copyright (C) 2022-now, RPL, KTH Royal Institute of Technology
# Authors: Kin ZHANG kin_eng@163.com

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


from utils.global_def import *
from utils.gui_app import App
import glog as log

log.setLevel("INFO")  # Integer levels are also allowed.

if __name__ == "__main__":
    try:
        log.info(f"=========== {bc.BOLD}Starting the Quick_CARLA GUI NOW.... {bc.ENDC} ===========")
        app = App()
        time_loop_ms = 50

        # reference: https://stackoverflow.com/a/459131/9281669
        def task_in_loop():
            app.run_spectator()
            app.run_bbx()
            app.after(time_loop_ms, task_in_loop)
        app.after(time_loop_ms, task_in_loop)

        app.mainloop()
        log.info(f"=========== {bc.BOLD}Quit the Quick_CARLA GUI, Bye! (Kin){bc.ENDC} ===========")

    except KeyboardInterrupt:
        log.info(f"=========== {bc.BOLD}Quit the Quick_CARLA GUI, Bye! (Kin){bc.ENDC} ===========")