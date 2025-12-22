#!/usr/bin/env python

# Created: 2022-12-28 15:10
# Copyright (C) 2022-now, RPL, KTH Royal Institute of Technology
# Authors: Qingwen Zhang (https://kin-zhang.github.io/)

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# reference GUI code: https://github.com/TomSchimansky/CustomTkinter/blob/master/examples/complex_example.py

import math, time
import tkinter.messagebox
import customtkinter
import glog as log
from . import bc
from .map_utils import EmbeddedMapPanel, MapGenerator
import random
try:
    import webbrowser
except:
    webbrowser = None
    log.warn("no webbrowser module loaded, cannot open link when clicked")
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

        self.map_panel = None
        self.cached_map_gen = None

    def custom_looprun(self):
        if self.spe_set:
            etransform = self.ego_vehicle.get_transform()
            spectator = self.world.get_spectator()
            spectator.set_transform(carla.Transform(etransform.location + carla.Location(z=50),
                                                    carla.Rotation(pitch=-90)))

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

        if self.print_info_set:
            v = self.ego_vehicle.get_velocity()
            vv = 3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)
            if vv > 0.1:
                log.info(f"ego vehicle speed: {vv:.2f} km/h")
        
        # [新增] 更新地图位置
        if self.map_panel is not None:
            self.map_panel.update_ego_position()

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
        if self.ego_vehicle is None:
            log.warn("Please find ego vehicle first!")
            return

        # [新增] 逻辑：如果面板已经存在，说明用户想刷新
        if self.map_panel is not None:
            log.info("Refreshing Map Size...")
            # 停止之前的轨迹跟踪（可选：如果想保留轨迹比较复杂，这里先简单清空）
            self.map_panel.destroy()
            self.map_panel = None

        # 1. 强制刷新 UI 计算
        self.update_idletasks()

        # 2. 动态获取当前剩余空间
        ws_width = self.workspace_frame.winfo_width()
        ws_height = self.workspace_frame.winfo_height()
        setting_width = self.setting_frame.winfo_width()
        
        # 留出边距 padding
        calc_max_w = ws_width - setting_width - 40
        calc_max_h = ws_height - 20
        # 保底尺寸
        calc_max_w = max(300, calc_max_w)
        calc_max_h = max(300, calc_max_h)

        # 3. 检查是否有缓存的 Generator
        if self.cached_map_gen is None:
            # 第一次点击：创建并缓存
            self.cached_map_gen = MapGenerator(self.world)

        # 4. 创建面板，传入缓存的 map_gen
        self.map_panel = EmbeddedMapPanel(self.workspace_frame, self.world, self.ego_vehicle, 
                                          map_gen=self.cached_map_gen, # 传入缓存
                                          max_width=calc_max_w, 
                                          max_height=calc_max_h)
        
        self.map_panel.grid(row=0, column=1, padx=(20, 0), sticky="nw")
        self.map_panel.update_ego_position()
        # 5. 恢复按钮状态
        self.track_btn.configure(state="normal", text="Start") # 重置Track按钮文字
        
        log.info(f"Map loaded/refreshed. Size limit: {calc_max_w}x{calc_max_h}")

    def init_all_window(self):
        # configure window
        self.title("Quickly CARLA By Qingwen")
        self.geometry(f"{1200}x{460}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # 右侧主区域
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Quick Vis CARLA", font=customtkinter.CTkFont(size=25, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        # self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="developed by Qingwen Zhang", font=customtkinter.CTkFont(size=15, weight="normal"))
        # self.logo_label.grid(row=1, column=0, padx=20, pady=10)

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
        self.connect_textbox = customtkinter.CTkTextbox(self.sidebar_frame, height=100, width=300)
        self.connect_textbox.grid(row=5, column=0, padx=(10, 10), pady=(10, 10), sticky="w")
        self.connect_textbox.insert("0.0", f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Waiting to connect CARLA servers.")  # insert at line 0 character 0
        self.connect_textbox.configure(state="disabled")

        # ========= start UI appearance
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

        # ============ CARLA Settings part
        self.rolename_frame = customtkinter.CTkFrame(self)
        self.rolename_frame.grid(row=0, column=1, columnspan=1,padx=(20, 20), pady=(20, 10), sticky="nwe")

        self.label_rgroup = customtkinter.CTkLabel(master=self.rolename_frame, text="Role name of ego vehicle", font=customtkinter.CTkFont(size=15))
        self.label_rgroup.grid(row=0, column=1, padx=(10, 0), pady=(10, 10))

        self.rolename = customtkinter.CTkEntry(self.rolename_frame, placeholder_text="hero")
        self.rolename.grid(row=0, column=2, padx=(10, 0), pady=(10, 10))
        self.rolename.insert(0,"hero")
        self.search_ego = customtkinter.CTkButton(self.rolename_frame, text="Find",command=self.search_rolename_event)
        self.search_ego.grid(row=0, column=3, padx=(10, 0), pady=(10, 10))
        
        self.textbox = customtkinter.CTkTextbox(self.rolename_frame, width=200, height=10)
        self.textbox.grid(row=0, column=4, padx=(10, 0), pady=(10, 10))
        self.textbox.configure(state="disabled")

        self.workspace_frame = customtkinter.CTkFrame(self, fg_color="transparent") # transparent 让它看不见背景
        self.workspace_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        self.workspace_frame.grid_columnconfigure(0, weight=0) 
        self.workspace_frame.grid_columnconfigure(1, weight=1)
        self.workspace_frame.grid_rowconfigure(0, weight=1)

        # Start setting part
        self.setting_frame = customtkinter.CTkFrame(self.workspace_frame)
        self.setting_frame.grid(row=0, column=0, sticky="nw") 

        labels = ["Spectator", "Auto Pilot", "Draw Box", "Print Log", "Plot Map", "Track Traj"]
        row_idx = 0
        cmds = [self.set_spectator, self.set_auto_driving_forEGO, self.draw_bbx, self.set_print_info, self.plot_figure_car, self.toggle_trajectory_event]
        for i, (txt, cmd) in enumerate(zip(labels, cmds)):
            lbl = customtkinter.CTkLabel(master=self.setting_frame, text=txt, font=customtkinter.CTkFont(size=14))
            lbl.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            if txt == "Track Traj":
                self.track_btn = customtkinter.CTkButton(self.setting_frame, text="Start", command=cmd, fg_color="#E59400", hover_color="#B57400") # 用个不同的颜色
                self.track_btn.grid(row=i, column=1, padx=10, pady=5)
                # 默认禁用，直到地图加载
                self.track_btn.configure(state="disabled")             
            if txt == "Plot Map":
                self.plot_ = customtkinter.CTkButton(self.setting_frame, text="Show Map", command=cmd)
                self.plot_.grid(row=i, column=1, padx=10, pady=5)
            elif txt == "Auto Pilot":
                self.auto_ = customtkinter.CTkButton(self.setting_frame, text="True", command=cmd)
                self.auto_.grid(row=i, column=1, padx=10, pady=5)
            elif txt == "Spectator":
                self.set_spectator = customtkinter.CTkButton(self.setting_frame, text="Set", command=cmd)
                self.set_spectator.grid(row=i, column=1, padx=10, pady=5)
            elif txt == "Draw Box":
                self.draw_ = customtkinter.CTkButton(self.setting_frame, text="Draw", command=cmd)
                self.draw_.grid(row=i, column=1, padx=10, pady=5)
            elif txt == "Print Log":
                self.print_info = customtkinter.CTkButton(self.setting_frame, text="Print", command=cmd)
                self.print_info.grid(row=i, column=1, padx=10, pady=5)
                
        # self.plot_mode = customtkinter.CTkOptionMenu(self.setting_frame, dynamic_resizing=False, values=["Map"])
        # self.plot_mode.grid(row=5, column=1, padx=10, pady=5)

        # End setting part
        # self.entry = customtkinter.CTkLabel(self, text="This tool firstly developed by Qingwen, Star this repo: https://github.com/Kin-Zhang/quickly-carla, Click me")
        # self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")
        # if webbrowser is not None:
        #     self.entry.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/Kin-Zhang/quickly-carla"))
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

    def toggle_trajectory_event(self):
        if self.map_panel is None:
            log.warn("Please show map first!")
            return
        
        is_tracking = self.map_panel.toggle_tracking()
        
        if is_tracking:
            self.track_btn.configure(text="Stop & Clear")
        else:
            self.track_btn.configure(text="Start")

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
        # self.plot_mode.configure(state="disabled")
        self.auto_.configure(state="disabled")
        self.draw_.configure(state="disabled")
        self.plot_.configure(state="disabled")

    def enable_finding_button(self):
        self.search_ego.configure(state="normal")

    def enable_all_window(self):
        self.set_spectator.configure(state="normal")
        self.print_info.configure(state="normal")
        # self.plot_mode.configure(state="normal")
        self.auto_.configure(state="normal")
        self.draw_.configure(state="normal")
        self.plot_.configure(state="normal")