#!/usr/bin/env python

# Created: 2022-12-28 15:10
# Copyright (C) 2022-now, RPL, KTH Royal Institute of Technology
# Authors: Kin ZHANG (https://kin-zhang.github.io/)

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# reference GUI code: https://github.com/TomSchimansky/CustomTkinter/blob/master/examples/complex_example.py

import tkinter.messagebox
import customtkinter
import glog as log
from .global_def import *
import random
import webbrowser
try:
    import carla
except:
    log.error(f"{bc.FAIL} !!! NO CARLA package, Please make sure carla lib is installed{bc.ENDC}")
    log.error(f"Install by run: pip install carla")
    exit()

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.init_all_window()
        self.init_var()

    def run_spectator(self):
        if self.spe_set:
            etransform = self.ego_vehicle.get_transform()
            spectator = self.world.get_spectator()
            spectator.set_transform(carla.Transform(etransform.location + carla.Location(z=50),
                                                    carla.Rotation(pitch=-90)))
    
    def run_bbx(self):
        if self.draw_set:
            etransform = self.ego_vehicle.get_transform()
            ebb = self.ego_vehicle.bounding_box
            ebb.location+=etransform.location
            if self.draw_all:
                for actor in self.vehicles_list:
                    vel = actor.get_velocity()
                    atran = actor.get_transform()
                    bb = actor.bounding_box
                    bb.location += atran.location
                    for t in range(0,self.time_draw,2):
                        bb.location += vel*t
                        self.world.debug.draw_box(bb, atran.rotation, 0.01, carla.Color(255,255,0,0), self.time_draw/5)
                # return
            else:
                self.world.debug.draw_box(ebb, etransform.rotation, 0.05, carla.Color(255,0,0,125),1)
    
    def search_rolename_event(self):
        # find all things in world
        rolename = self.rolename.get()
        hero_vehicles = [actor for actor in self.world.get_actors()
                            if 'vehicle' in actor.type_id and actor.attributes['role_name'] == rolename]
        self.ego_vehicle = None
        if len(hero_vehicles) > 0:
            self.ego_vehicle = random.choice(hero_vehicles)
            self.hero_transform = self.ego_vehicle.get_transform()
            log.info(f"{bc.OKGREEN}Select from length:{len(hero_vehicles)}, find ego car id:{self.ego_vehicle.id}{bc.ENDC}")
            self.search_role_text()
            self.enable_all_window()
        else:
            log.warn(f"{bc.FAIL}!! CANNOT find the ego car, please check the rolename as: {rolename}{bc.ENDC}")
            log.warn(f"if the role name is correct, pls try again by clicking button")
    
    def set_auto_driving_forEGO(self):
        self.auto_set = not self.auto_set
        if self.auto_set:
            self.auto_.configure(text="False")
        else:
            self.auto_.configure(text="True")
        self.ego_vehicle.set_autopilot(self.auto_set)
        log.info(f"setting the auto driving to ego vehicle, mode is: {self.auto_set}")
        

    def connect_button_event(self):            
        if self.port.get().isnumeric():
            port_num = int(self.port.get())
            # connect to carla
            self.client = carla.Client(self.host.get(), port_num)
            log.info(f"Trying to connect the CARLA.... may take some time....")
            self.client.set_timeout(5.0)
            self.world = self.client.get_world()
            self.carla_map = self.world.get_map()

            self.vehicles_list = self.world.get_actors().filter('vehicle.*')

            self.connect_text(port_num, len(self.vehicles_list), self.carla_map.name)
            log.info(f"{bc.OKGREEN} Connect the CARLA server successfully{bc.ENDC}")
            self.enable_finding_button()
        else:
            log.error(f"{bc.FAIL}Please insert valid port num! It's a number! default is 2000{bc.ENDC}")
    
    def print_log_info(self):
        log.info("TODO")

    def plot_figure_car(self):
        log.info("TODO, working hard by Kin. Welcome to contribute!")
        
    def init_all_window(self):
        # configure window
        self.title("Quickly CARLA By KIN")
        self.geometry(f"{1100}x{460}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Debug CARLA", font=customtkinter.CTkFont(size=25, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="developed by Kin ZHANG", font=customtkinter.CTkFont(size=15, weight="normal"))
        self.logo_label.grid(row=1, column=0, padx=20, pady=10)

        # connect to CARLA
        
        self.label_host = customtkinter.CTkLabel(master=self.sidebar_frame, text="host:", font=customtkinter.CTkFont(size=15))
        self.label_host.grid(row=2, column=0, padx=(10, 0), pady=(10, 10), sticky="w")

        self.host = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="based on your setting")
        self.host.grid(row=2, column=0, padx=(50,20), pady=10)
        self.host.insert(0,"localhost")

        self.label_port = customtkinter.CTkLabel(master=self.sidebar_frame, text="port:", font=customtkinter.CTkFont(size=15))
        self.label_port.grid(row=3, column=0, padx=(10, 0), pady=(10, 10), sticky="w")
        self.port = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="port to connect")
        self.port.grid(row=3, column=0, padx=(50,20), pady=10)
        self.port.insert(0,"2000")
        
        self.connect_switch = customtkinter.CTkSwitch(master=self.sidebar_frame, text="Connect",command=self.connect_button_event)
        self.connect_switch.grid(row=4, column=0, padx=10, pady=10)
        # self.connect_button = customtkinter.CTkButton(self.sidebar_frame, text="Connect",command=self.connect_button_event)
        # self.connect_button.grid(row=4, column=0, padx=10, pady=10)
        self.connect_textbox = customtkinter.CTkTextbox(self.sidebar_frame, height=50)
        self.connect_textbox.grid(row=5, column=0, padx=(10, 10), pady=(10, 10), sticky="w")
        self.connect_textbox.insert("0.0", "waiting for connecting to CARLA")  # insert at line 0 character 0
        self.connect_textbox.configure(state="disabled")

        # start appearance
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Appearance:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=(10,10), pady=(10, 10), sticky="w")
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       width=50,        
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=(10,10), pady=(10, 10), sticky="e")

        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=(10,10), pady=(10, 10), sticky="w")
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               width=50,
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=7, column=0, padx=(10,10), pady=(10, 10), sticky="e")
        # end appearance

        self.rolename_frame = customtkinter.CTkFrame(self)
        self.rolename_frame.grid(row=0, column=1, columnspan=1,padx=(20, 20), pady=(20, 20), sticky="nwe")

        self.label_rgroup = customtkinter.CTkLabel(master=self.rolename_frame, text="Role name of ego vehicle", font=customtkinter.CTkFont(size=15))
        self.label_rgroup.grid(row=0, column=1, padx=(10, 0), pady=(10, 10))

        self.rolename = customtkinter.CTkEntry(self.rolename_frame, placeholder_text="")
        self.rolename.grid(row=0, column=2, padx=(10, 0), pady=(10, 10))
        self.rolename.insert(0,"hero")
        self.search_ego = customtkinter.CTkButton(self.rolename_frame, text="Find",command=self.search_rolename_event)
        self.search_ego.grid(row=0, column=3, padx=(10, 0), pady=(10, 10))

        self.textbox = customtkinter.CTkTextbox(self.rolename_frame, width=300, height=10)
        self.textbox.grid(row=0, column=4, padx=(30, 0), pady=(10, 10))
        self.textbox.insert("0.0", "new text to insert")  # insert at line 0 character 0
        self.textbox.configure(state="disabled")

        # Start setting part
        self.setting_frame = customtkinter.CTkFrame(self)
        self.setting_frame.grid(row=0, column=1, columnspan=1,padx=(20, 0), pady=(100, 0), sticky="nw")

        self.label_sgroup = customtkinter.CTkLabel(master=self.setting_frame, text="Set spectator to ego", font=customtkinter.CTkFont(size=15))
        self.label_sgroup.grid(row=0, column=1, padx=(10, 0), pady=(10, 10))
        self.set_spectator = customtkinter.CTkButton(self.setting_frame, text="Set",command=self.set_spectator)
        self.set_spectator.grid(row=0, column=3, padx=(20, 10), pady=(10, 10))

        self.auto_sgroup = customtkinter.CTkLabel(master=self.setting_frame, text="Set Auto Driving", font=customtkinter.CTkFont(size=15))
        self.auto_sgroup.grid(row=1, column=1, padx=(10, 0), pady=(10, 10))
        self.auto_ = customtkinter.CTkButton(self.setting_frame, text="True",command=self.set_auto_driving_forEGO)
        self.auto_.grid(row=1, column=3, padx=(20, 10), pady=(10, 10))

        self.draw_sgroup = customtkinter.CTkLabel(master=self.setting_frame, text="Draw bounding box", font=customtkinter.CTkFont(size=15))
        self.draw_sgroup.grid(row=2, column=1, padx=(10, 0), pady=(10, 10))
        self.draw_ = customtkinter.CTkButton(self.setting_frame, text="Draw",command=self.draw_bbx)
        self.draw_.grid(row=2, column=3, padx=(20, 10), pady=(10, 10))

        self.debug_sgroup = customtkinter.CTkLabel(master=self.setting_frame, text="Print log info", font=customtkinter.CTkFont(size=15))
        self.debug_sgroup.grid(row=3, column=1, padx=(10, 0), pady=(10, 10))
        self.print_info = customtkinter.CTkButton(self.setting_frame, text="Print",command=self.set_print_info)
        self.print_info.grid(row=3, column=3, padx=(20, 10), pady=(10, 10))

        self.plot_sgroup = customtkinter.CTkLabel(master=self.setting_frame, text="Plot figure", font=customtkinter.CTkFont(size=15))
        self.plot_sgroup.grid(row=5, column=1, padx=(10, 0), pady=(10, 10))
        self.plot_ = customtkinter.CTkButton(self.setting_frame, text="Plot",command=self.plot_figure_car)
        self.plot_.grid(row=6, column=3, padx=(20, 10), pady=(10, 10))

        self.plot_mode = customtkinter.CTkOptionMenu(self.setting_frame, dynamic_resizing=False,
                                                        values=["Map", "Velocity-time", "Throttle-time"])
        self.plot_mode.grid(row=5, column=3, padx=(20, 10), pady=(10, 10))
        # End setting part
        self.entry = customtkinter.CTkLabel(self, text="This tool firstly developed by Kin, Star this repo: https://github.com/Kin-Zhang/quickly-carla, Click me")
        self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")
        self.entry.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/Kin-Zhang/quickly-carla"))
        self.disable_all_window()

    def init_var(self):
        self.draw_set = False
        self.draw_all = False
        self.spe_set = False
        self.print_info_set = False
        self.auto_set = False

    def set_spectator(self):
        self.spe_set = not self.spe_set
        if self.spe_set:
            self.set_spectator.configure(text="Release")
            log.info(f"{bc.OKGREEN} Setting the spectator to ego vehicle, check your CARLA main window{bc.ENDC}")
        else:
            self.set_spectator.configure(text="Set")

    def draw_bbx(self):
        self.draw_set = not self.draw_set
        if self.draw_set:
            self.draw_.configure(text="Release")
            log.info(f"{bc.OKGREEN} Draw the bounding box in CARLA main window now{bc.ENDC}")
            log.info("It will be visulizeable by camera... Pay attention on THIS!!! Only for debug")
        else:
            self.draw_.configure(text="Draw")
    def set_print_info(self):
        self.print_info_set = not self.print_info_set
        if self.print_info_set:
            self.print_info.configure(text="Release")
        else:
            self.print_info.configure(text="Draw")

    def search_role_text(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("0.0","end")
        self.textbox.insert("0.0", f"Vehicle id: {self.ego_vehicle.id}")
        self.textbox.configure(state="disabled")

    def connect_text(self, port_num, vehicle_num, town_name):
        log.info(f"port num is {port_num}")
        self.connect_textbox.configure(state="normal")
        self.connect_textbox.delete("0.0","end")
        self.connect_textbox.insert("0.0", f"Town Map: {town_name.split('/')[-1]}\nVehicle num: {vehicle_num}")  # insert at line 0 character 0

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)
    
    def disable_all_window(self):
        self.search_ego.configure(state="disabled")
        self.set_spectator.configure(state="disabled")
        self.print_info.configure(state="disabled")
        self.plot_mode.configure(state="disabled")
        self.auto_.configure(state="disabled")
        self.draw_.configure(state="disabled")
        self.plot_.configure(state="disabled")

    def enable_finding_button(self):
        self.search_ego.configure(state="normal")

    def enable_all_window(self):
        self.set_spectator.configure(state="normal")
        self.print_info.configure(state="normal")
        self.plot_mode.configure(state="normal")
        self.auto_.configure(state="normal")
        self.draw_.configure(state="normal")
        self.plot_.configure(state="normal")