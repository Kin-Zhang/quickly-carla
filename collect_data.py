
#!/usr/bin/env python
# Created: 2022-03-25 23:10
# Updated: 2023-1-13 19:23
# Copyright (C) 2022-now, RPL, KTH Royal Institute of Technology
# Author: Kin ZHANG  (https://kin-zhang.github.io/)

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
# Part of these codes are from some reference please check comments
"""

此代码主要用于收集数据示意（简易版）
对应博文的详细教程在 https://www.cnblogs.com/kin-zhang/p/16057173.html

0. 此示意引用参考全部总结与博客之中 再次不做赘述
1. 记得修改一下保存数据的绝对路径
2. 检查CARLA PORT是否和设置的是一致的 免得连接不上
3. 相关注释基本都没咋写 具体可以看看博客
"""
import os
import glog as log
from utils.global_def import *
import open3d as o3d
try:
    import carla
except:
    log.error(f"{bc.FAIL} !!! NO CARLA package, Please make sure carla lib is installed{bc.ENDC}")
    log.error(f"Install by run: pip install carla")
    exit()

import carla
import random
import numpy as np
import cv2
from queue import Queue, Empty
import copy
import random
random.seed(0)

# args
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--host', metavar='H',    default='127.0.0.1', help='IP of the host server (default: 127.0.0.1)')
parser.add_argument('--port', '-p',           default=2000, type=int, help='TCP port to listen to (default: 2000)')
parser.add_argument('--tm_port',              default=8000, type=int, help='Traffic Manager Port (default: 8000)')
parser.add_argument('--ego-spawn', type=list, default=None, help='[x,y] in world coordinate')
parser.add_argument('--top-view',             default=True, help='Setting spectator to top view on ego car')
parser.add_argument('--map',                  default='Town04', help='Town Map')
parser.add_argument('--sync',                 default=True, help='Synchronous mode execution')
parser.add_argument('--sensor-h',             default=2.4, help='Sensor Height')
# 给绝对路径 记得改位置哦！
parser.add_argument('--save-path',            default='/home/kin/bags/hus_data/', help='Synchronous mode execution')
args = parser.parse_args()

# 图片大小可自行修改
IM_WIDTH = 1024
IM_HEIGHT = 768
update_hz = 10
actor_list, sensor_list = [], []

sensor_type = ['rgb','lidar','depth']

def main(args):
    poses2save = ""
    # We start creating the client
    client = carla.Client(args.host, args.port)
    client.set_timeout(5.0)
    
    # world = client.get_world()
    world = client.load_world('Town01')
    carla_map = world.get_map()
    blueprint_library = world.get_blueprint_library()
    
    try:
        original_settings = world.get_settings()
        settings = world.get_settings()

        # We set CARLA syncronous mode
        settings.fixed_delta_seconds = 0.05
        settings.synchronous_mode = True
        world.apply_settings(settings)
        spectator = world.get_spectator()

        # 手动规定
        # transform_vehicle = carla.Transform(carla.Location(0, 10, 0), carla.Rotation(0, 0, 0))
        # 自动选择
        transform_vehicle = carla.Transform(carla.Location(92.1, 37.1, 0.1), carla.Rotation(0,-90, -3.05))#random.choice(world.get_map().get_spawn_points())
        
        ego_vehicle_bp = random.choice(blueprint_library.filter("model3"))
        ego_vehicle_bp.set_attribute('role_name', 'hero')
        ego_vehicle = world.spawn_actor(ego_vehicle_bp, transform_vehicle)
        
        path2follow = [carla_map.get_waypoint(carla.Location(92.1, 37.1, 0.1)).transform.location,
                       carla_map.get_waypoint(carla.Location(134.6, 1.5, 0.1)).transform.location,
                       carla_map.get_waypoint(carla.Location(153.6, 38.5, 0.1)).transform.location,
                       carla_map.get_waypoint(carla.Location(136.6, 55.3, 0.1)).transform.location,
                       carla_map.get_waypoint(carla.Location(115.2, 55.4, 0.1)).transform.location,
                       carla_map.get_waypoint(carla.Location(92.1, 37.1, 0.1)).transform.location,
                       ]

        # 设置traffic manager
        tm = client.get_trafficmanager(args.tm_port)
        tm.set_synchronous_mode(True)
        # 是否忽略红绿灯
        tm.ignore_lights_percentage(ego_vehicle, 100)
        # 如果限速30km/h -> 30*(1-10%)=27km/h
        tm.global_percentage_speed_difference(-10.0)
        ego_vehicle.set_autopilot(True, tm.get_port())
        tm.set_path(ego_vehicle, path2follow)
        actor_list.append(ego_vehicle)

        #-------------------------- 进入传感器部分 --------------------------#
        sensor_queue = Queue()
        cam_bp = blueprint_library.find('sensor.camera.rgb')
        cam_depth_bp = blueprint_library.find('sensor.camera.depth')
        lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
        imu_bp = blueprint_library.find('sensor.other.imu')
        gnss_bp = blueprint_library.find('sensor.other.gnss')

        # 可以设置一些参数 set the attribute of camera
        cam_bp.set_attribute("image_size_x", "{}".format(IM_WIDTH))
        cam_bp.set_attribute("image_size_y", "{}".format(IM_HEIGHT))
        cam_bp.set_attribute("fov", "66.5")
        cam_depth_bp.set_attribute("image_size_x", "{}".format(IM_WIDTH))
        cam_depth_bp.set_attribute("image_size_y", "{}".format(IM_HEIGHT))
        cam_depth_bp.set_attribute("fov", "66.5")
        # cam_bp.set_attribute('sensor_tick', '0.1')

        cam01 = world.spawn_actor(cam_bp, carla.Transform(carla.Location(z=args.sensor_h),carla.Rotation(yaw=0)), attach_to=ego_vehicle)
        cam01.listen(lambda data: sensor_callback(data, sensor_queue, "rgb_front"))
        sensor_list.append(cam01)

        cam02 = world.spawn_actor(cam_depth_bp, carla.Transform(carla.Location(z=args.sensor_h),carla.Rotation(yaw=0)), attach_to=ego_vehicle)
        cam02.listen(lambda data: sensor_callback(data, sensor_queue, "rgb_depth"))
        sensor_list.append(cam02)

        lidar_bp.set_attribute('channels', '128')
        lidar_bp.set_attribute('points_per_second', '5000000')
        lidar_bp.set_attribute('range', '100')
        lidar_bp.set_attribute('rotation_frequency', str(int(1/settings.fixed_delta_seconds)*2)) #
        
        lidar01 = world.spawn_actor(lidar_bp, carla.Transform(carla.Location(z=args.sensor_h)), attach_to=ego_vehicle)
        lidar01.listen(lambda data: sensor_callback(data, sensor_queue, "lidar"))
        sensor_list.append(lidar01)
        #-------------------------- 传感器设置完毕 --------------------------#


        start_frame=0
        no_vel = True
        while True:
            # Tick the server
            world.tick()
            w_frame = world.get_snapshot().frame
            print("\nWorld's frame: %d" % w_frame)
            v=ego_vehicle.get_velocity()
            if math.sqrt(v.x**2 + v.y**2 + v.z**2)<1 and start_frame==0:
                ego_vehicle.set_autopilot(True, tm.get_port())
                tm.set_path(ego_vehicle, path2follow)
            else:
                no_vel = False
            try:
                rgbs = []
                now_pose = None
                for i in range (0, len(sensor_list)):
                    s_frame, s_name, s_data = sensor_queue.get(True, 1.0)
                    print("    Frame: %d   Sensor: %s" % (s_frame, s_name))
                    sensor_type = s_name.split('_')[0]
                    if sensor_type == 'rgb':
                        rgbs.append(_parse_image_cb(s_name, s_data))
                    elif sensor_type == 'lidar':
                        lidar = _parse_lidar_cb(s_data)
                        s_lidar = s_data

                        # reference: https://github.com/carla-simulator/ros-bridge/blob/master/carla_common/src/carla_common/transforms.py
                        tf = ego_vehicle.get_transform()

                        # Considers the conversion from left-handed system (unreal) to right-handed system (ROS)
                        roll = math.radians(tf.rotation.roll)
                        pitch=-math.radians(tf.rotation.pitch)
                        yaw = -math.radians(tf.rotation.yaw)

                        quat = euler2quat(roll, pitch, yaw)
                        now_pose = "{:.8f}, {:.8f}, {:.8f}, {:.8f}, {:.8f}, {:.8f}, {:.8f}\n".format(tf.location.x, -tf.location.y, tf.location.z, quat[0],quat[1],quat[2],quat[3])
                
                if no_vel:
                    continue
                # 仅用来可视化 可注释
                img_rgb = rgbs[0]
                img_dep = rgbs[1]
                rgb=np.concatenate(rgbs, axis=1)[...,:3]
                cv2.imshow('vizs', visualize_data(rgb, lidar))
                cv2.waitKey(100)
                if now_pose is not None and (w_frame-start_frame) > update_hz:
                    # 检查是否有各自传感器的文件夹
                    mkdir_folder(args.save_path)

                    filename = args.save_path +'rgb/'+str(w_frame)+'.png'
                    cv2.imwrite(filename, np.array(img_rgb[...,::-1]))
                    filename = args.save_path +'depth/'+str(w_frame)+'.png'
                    cv2.imwrite(filename, np.array(img_dep[...,::-1]))
                    filename = args.save_path +'lidar/'+str(w_frame)+'.ply'
                    s_lidar.save_to_disk(filename)
                    poses2save = poses2save + now_pose
                    # Pass xyz to Open3D.o3d.geometry.PointCloud and visualize
                    # pcd = o3d.geometry.PointCloud()
                    # pcd.points = o3d.utility.Vector3dVector(lidar[...,:3])
                    # o3d.io.write_point_cloud(filename, pcd)
                    # np.save(filename, lidar)
                    start_frame = w_frame
                # else:
                #     print(f"{bc.WARNING} No camera data now....{bc.ENDC}")
            except Empty:
                print("    Some of the sensor information is missed")

    finally:
        with open(f'{args.save_path}/pose.txt', 'w') as file:
            file.write(poses2save)
        world.apply_settings(original_settings)
        tm.set_synchronous_mode(False)
        for sensor in sensor_list:
            sensor.destroy()
        for actor in actor_list:
            actor.destroy()
        print("All cleaned up!")

def mkdir_folder(path):
    for s_type in sensor_type:
        if not os.path.isdir(os.path.join(path, s_type)):
            os.makedirs(os.path.join(path, s_type))
    return True

def sensor_callback(sensor_data, sensor_queue, sensor_name):
    # Do stuff with the sensor_data data like save it to disk
    # Then you just need to add to the queue
    sensor_queue.put((sensor_data.frame, sensor_name, sensor_data))

# modify from world on rail code
def visualize_data(rgb, lidar, imu_yaw=None, gnss=None, text_args=(cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,255), 1)):

    canvas = np.array(rgb[...,::-1])

    if lidar is not None:
        lidar_viz = lidar_to_bev(lidar).astype(np.uint8)
        lidar_viz = cv2.cvtColor(lidar_viz,cv2.COLOR_GRAY2RGB)
        canvas = np.concatenate([canvas, cv2.resize(lidar_viz.astype(np.uint8), (canvas.shape[0], canvas.shape[0]))], axis=1)

    # cv2.putText(canvas, f'yaw angle: {imu_yaw:.3f}', (4, 10), *text_args)
    # cv2.putText(canvas, f'log: {gnss[0]:.3f} alt: {gnss[1]:.3f} brake: {gnss[2]:.3f}', (4, 20), *text_args)

    return canvas
# modify from world on rail code
def lidar_to_bev(lidar, min_x=-24,max_x=24,min_y=-16,max_y=16, pixels_per_meter=4, hist_max_per_pixel=10):
    xbins = np.linspace(
        min_x, max_x+1,
        (max_x - min_x) * pixels_per_meter + 1,
    )
    ybins = np.linspace(
        min_y, max_y+1,
        (max_y - min_y) * pixels_per_meter + 1,
    )
    # Compute histogram of x and y coordinates of points.
    hist = np.histogramdd(lidar[..., :2], bins=(xbins, ybins))[0]
    # Clip histogram
    hist[hist > hist_max_per_pixel] = hist_max_per_pixel
    # Normalize histogram by the maximum number of points in a bin we care about.
    overhead_splat = hist / hist_max_per_pixel * 255.
    # Return splat in X x Y orientation, with X parallel to car axis, Y perp, both parallel to ground.
    return overhead_splat[::-1,:]

# modify from manual control
def _parse_image_cb(type_name, image):
    if type_name.split('_')[-1]=="depth":
        image.convert(carla.ColorConverter.LogarithmicDepth)
    # log.info(type_name)
    array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    array = np.reshape(array, (image.height, image.width, 4))
    array = array[:, :, :3]
    array = array[:, :, ::-1]
    return array
# modify from leaderboard
def _parse_lidar_cb(lidar_data):
    points = np.frombuffer(lidar_data.raw_data, dtype=np.dtype('f4'))
    points = copy.deepcopy(points)
    points = np.reshape(points, (int(points.shape[0] / 4), 4))
    return points


if __name__ == "__main__":
    try:
        main(args)
    except KeyboardInterrupt:
        print(' - Exited by user.')