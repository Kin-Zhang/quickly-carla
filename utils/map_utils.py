# --- START OF FILE utils/map_utils.py ---
import carla
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import math
from PIL import Image

# 颜色定义
COLOR_ALUMINIUM_4 = pygame.Color(85, 87, 83)
COLOR_ALUMINIUM_5 = pygame.Color(46, 52, 54)
COLOR_WHITE = pygame.Color(255, 255, 255)
COLOR_YELLOW = pygame.Color(255, 255, 0)

PIXELS_PER_METER = 5 

class MapGenerator(object):
    def __init__(self, carla_world, pixels_per_meter=PIXELS_PER_METER):
        self._pixels_per_meter = pixels_per_meter
        self.scale = 1.0
        self.world = carla_world
        self.town_map = self.world.get_map()
        
        pygame.init()
        
        # 1. 计算地图边界
        waypoints = self.town_map.generate_waypoints(2)
        margin = 5
        max_x = max(waypoints, key=lambda x: x.transform.location.x).transform.location.x + margin
        max_y = max(waypoints, key=lambda x: x.transform.location.y).transform.location.y + margin
        min_x = min(waypoints, key=lambda x: x.transform.location.x).transform.location.x - margin
        min_y = min(waypoints, key=lambda x: x.transform.location.y).transform.location.y - margin

        self.world_width = max_x - min_x
        self.world_height = max_y - min_y
        self._world_offset = (min_x, min_y)

        self.pixel_width = int(self._pixels_per_meter * self.world_width)
        self.pixel_height = int(self._pixels_per_meter * self.world_height)
        
        self.big_map_surface = pygame.Surface((self.pixel_width, self.pixel_height))
        
        self._draw_road_map()

    def _draw_road_map(self):
        self.big_map_surface.fill(COLOR_ALUMINIUM_4)
        topology = self.town_map.get_topology()
        self._draw_topology(topology)

    def _draw_topology(self, carla_topology, index=0):
        topology = [x[index] for x in carla_topology]
        topology = sorted(topology, key=lambda w: w.transform.location.z)
        
        for waypoint in topology:
            waypoints = [waypoint]
            nxt = waypoint.next(2.0)
            if len(nxt) > 0:
                nxt = nxt[0]
                while nxt.road_id == waypoint.road_id:
                    waypoints.append(nxt)
                    nxt = nxt.next(2.0)
                    if len(nxt) > 0:
                        nxt = nxt[0]
                    else:
                        break

            # 1. 绘制路面 (灰色背景)
            road_left_side = [self._lateral_shift(w.transform, -w.lane_width * 0.5) for w in waypoints]
            road_right_side = [self._lateral_shift(w.transform, w.lane_width * 0.5) for w in waypoints]

            polygon = road_left_side + [x for x in reversed(road_right_side)]
            polygon = [self.world_to_pixel(x) for x in polygon]

            if len(polygon) > 2:
                pygame.draw.polygon(self.big_map_surface, COLOR_ALUMINIUM_5, polygon, 5)
                pygame.draw.polygon(self.big_map_surface, COLOR_ALUMINIUM_5, polygon)

            # 2. 绘制车道线 (新增)
            # 只有非路口才画线，路口画线太复杂且容易乱
            if not waypoint.is_junction:
                self._draw_lane_marking_single_side(waypoints, -1) # 左侧
                self._draw_lane_marking_single_side(waypoints, 1)  # 右侧

    def _draw_lane_marking_single_side(self, waypoints, sign):
        """ 绘制单侧车道线逻辑 """
        lane_marking = None
        previous_marking_type = carla.LaneMarkingType.NONE
        previous_marking_color = carla.LaneMarkingColor.Other
        temp_waypoints = []
        current_lane_marking = carla.LaneMarkingType.NONE

        for sample in waypoints:
            lane_marking = sample.left_lane_marking if sign < 0 else sample.right_lane_marking
            if lane_marking is None: continue

            if current_lane_marking != lane_marking.type:
                # 绘制之前积累的线段
                self._draw_line_segment(previous_marking_type, previous_marking_color, temp_waypoints, sign)
                current_lane_marking = lane_marking.type
                temp_waypoints = [sample] # 重新开始积累
                previous_marking_type = lane_marking.type
                previous_marking_color = lane_marking.color
            else:
                temp_waypoints.append(sample)

        # 绘制最后一段
        self._draw_line_segment(previous_marking_type, previous_marking_color, temp_waypoints, sign)

    def _draw_line_segment(self, marking_type, marking_color, waypoints, sign):
        if len(waypoints) < 2: return

        # 确定颜色
        color = COLOR_WHITE
        if marking_color == carla.LaneMarkingColor.Yellow:
            color = COLOR_YELLOW
        
        # 确定位置
        # 需要偏移一点点，防止压在路边缘看不见，sign * lane_width * 0.5 是车道边缘
        points = [self.world_to_pixel(self._lateral_shift(w.transform, sign * w.lane_width * 0.5)) for w in waypoints]
        
        width = 2 # 线宽
        
        # 实线
        if marking_type == carla.LaneMarkingType.Solid or marking_type == carla.LaneMarkingType.SolidSolid:
            pygame.draw.lines(self.big_map_surface, color, False, points, width)
        
        # 虚线
        elif marking_type == carla.LaneMarkingType.Broken or marking_type == carla.LaneMarkingType.BrokenBroken:
            # 简单的虚线算法：每隔一段画一段
            # 这里简化处理：每3个点画一段
            broken_lines = [x for n, x in enumerate(zip(*(iter(points),) * 4)) if n % 2 == 0]
            for line in broken_lines:
                pygame.draw.lines(self.big_map_surface, color, False, line, width)

    def _lateral_shift(self, transform, shift):
        transform.rotation.yaw += 90
        return transform.location + shift * transform.get_forward_vector()

    def world_to_pixel(self, location):
        x = self.scale * self._pixels_per_meter * (location.x - self._world_offset[0])
        y = self.scale * self._pixels_per_meter * (location.y - self._world_offset[1])
        return [int(x), int(y)]

    def get_pil_image(self):
        image_str = pygame.image.tostring(self.big_map_surface, "RGB")
        pil_image = Image.frombytes("RGB", self.big_map_surface.get_size(), image_str)
        return pil_image


import customtkinter
import glog as log
from PIL import Image, ImageTk
from . import map_utils

class EmbeddedMapPanel(customtkinter.CTkFrame):
    def __init__(self, master, world, ego_vehicle, map_gen=None, max_width=500, max_height=400):
        super().__init__(master)
        self.world = world
        self.ego_vehicle = ego_vehicle

        self.is_tracking = False
        self.trajectory_ids = [] 
        self.last_screen_pos = None

        # [逻辑优化]
        # 如果传入了现成的 map_gen，直接用（秒开）
        # 如果没传，才去新建（耗时）
        if map_gen is not None:
            self.map_gen = map_gen
            log.info("Using cached Map Data.")
        else:
            log.info(f"Generating Map... This may take 1-2 seconds.")
            self.map_gen = map_utils.MapGenerator(world)

        self.pil_image = self.map_gen.get_pil_image()
        self.map_w, self.map_h = self.pil_image.size
        
        self.raw_w, self.raw_h = self.pil_image.size
        scale_w = max_width / self.raw_w
        scale_h = max_height / self.raw_h
        self.render_scale = min(scale_w, scale_h)
        
        self.final_w = int(self.raw_w * self.render_scale)
        self.final_h = int(self.raw_h * self.render_scale)
        
        log.info(f"Map raw size: {self.raw_w}x{self.raw_h}, Display size: {self.final_w}x{self.final_h}")

        self.canvas = customtkinter.CTkCanvas(self, width=self.final_w, height=self.final_h, 
                                              bg="#333333", highlightthickness=0)
        self.canvas.pack(padx=5, pady=5) # 稍微留点内边距


        self.display_image = self.pil_image.resize((self.final_w, self.final_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.display_image)

        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        self.car_dot = self.canvas.create_oval(0, 0, 8, 8, fill="#FF5555", outline="white", width=2)
        self.car_arrow = self.canvas.create_line(0, 0, 0, 0, fill="#FFFF55", width=2, arrow=customtkinter.LAST)

    def update_ego_position(self):
        if not self.ego_vehicle: return
        
        try:
            transform = self.ego_vehicle.get_transform()
            loc = transform.location
            
            raw_pixel = self.map_gen.world_to_pixel(loc)
            
            screen_x = raw_pixel[0] * self.render_scale
            screen_y = raw_pixel[1] * self.render_scale
            
            arrow_len = 12
            yaw_rad = math.radians(transform.rotation.yaw)
            
            end_x = screen_x + arrow_len * math.cos(yaw_rad)
            end_y = screen_y + arrow_len * math.sin(yaw_rad)

            r = 5
            self.canvas.coords(self.car_dot, screen_x-r, screen_y-r, screen_x+r, screen_y+r)
            self.canvas.coords(self.car_arrow, screen_x, screen_y, end_x, end_y)
        except Exception as e:
            pass