#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2024 IISLab at the Technical University of Košice.
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import glob
import os
import sys
import time
import random

try:
    # Dynamic path to CARLA .egg file
    sys.path.append(glob.glob(os.path.join(
        '/home/vlmteam/carla_0.9.14/PythonAPI/carla/dist',  # Base CARLA path
        'carla-*%d.%d-%s.egg' % (                            # Dynamic pattern
            sys.version_info.major,
            sys.version_info.minor,
            'win-amd64' if os.name == 'nt' else 'linux-x86_64'
        )
    ))[0])
except IndexError:
    pass

# Path to CARLA PythonAPI source directory (absolute path)
sys.path.append('/home/vlmteam/carla_0.9.14/PythonAPI')

# Now import CARLA
import carla
from util import *
from checks import is_inside_bounding_box, get_vehicle_speed, update_trigger_points

class FootballHighway():
    """
    Represents a scenario a football is sht over the fence (brick wall) and onto high-speed road.

    This scenario spawns one actor and is triggered when the ego vehicle enters a specified trigger area.
    The objective of the scenario is to test ego vehicle's ability to predict dangerous and non-dangerous situations.
    The vehicle should not collide with the football, but it should also not stop or make hard evasive manouvers unnecessarily.

    Attributes:
        triggered (bool): Indicates whether the scenario has been triggered.
        trigger_points (list): List of trigger points defining the trigger area.
        trigger_area (list): List of trigger points defining the trigger area.
        timer (int): The countdown timer for the scenario.
        actor_list (list): List of actors spawned for the scenario.

    Methods:
        __init__(self, world, ego_vehicle, trigger_points=None): Initializes the scenario with the specified world, ego vehicle, and trigger points.
        tick(self, ego_vehicle, traffic_manager=None): Updates the scenario state based on the ego vehicle's position.
        trigger(self): Triggers the scenario.
        destroy(self, client): Destroys all actors spawned for the scenario.
    """
    def __init__(self, world, ego_vehicle, trigger_points=None):
        """
        Initializes the scenario with the specified world, ego vehicle, and trigger points.

        Args:
            world: The Carla world object.
            ego_vehicle: The ego vehicle object. Not needed for this scenario.
            trigger_points (list, optional): List of trigger points defining the trigger area. 
                If not provided, default trigger points will be used.
        """
        self.triggered = False
        if trigger_points is not None:
            self.trigger_points = trigger_points
        else:
            self.trigger_points = [(107.00, 191.80),
                                   (109.00, 197.70)]
        self.trigger_area = self.trigger_points
        self.actor_list = []
        blueprint_library = world.get_blueprint_library()
        bp_ball = blueprint_library.find('static.prop.football')

        ball_transform = carla.Transform(carla.Location(x=79.30, y=177.60, z=2.0), carla.Rotation(pitch=0, yaw=270, roll=0))

        self.football_actor = world.spawn_actor(bp_ball, ball_transform)
        self.actor_list.append(self.football_actor)
        self.football_actor.set_simulate_physics(False)

    def tick(self, ego_vehicle, traffic_manager=None):
        """
        Updates the scenario state each tick based on the ego vehicle's position.

        If the scenario is triggered and the ego vehicle is inside the trigger area,
        the scenario launches a football across the brick wall.

        Args:
            ego_vehicle: The ego vehicle object.
            traffic_manager (optional): The traffic manager object.

        Returns:
            int: 1 if the scenario is completed (either passed or failed), 0 otherwise.
        """
        if self.triggered:
            if ego_vehicle.get_transform().location.x < 52.00:
                print('The football has been successfully avoided, scenario passed!')
                return 1
            elif get_vehicle_speed(ego_vehicle) < 8:
                print('The football poses no real danger to the car, scenario failed!')
                return 1
            else:
                return 0
        elif is_inside_bounding_box(ego_vehicle.get_transform().location, self.trigger_area[0], self.trigger_area[1]):
            self.trigger()
        else:
            self.trigger_area = update_trigger_points(self.trigger_points, get_vehicle_speed(ego_vehicle), add_speed=True, add_to_x=True)
        return 0
    
    def trigger(self):
        """
        Triggers the scenario, used by the tick method.

        Sets the `triggered` attribute to True, sets physics on, launches the ball,
        and prints a message indicating that the scenario has been triggered.
        Can be used to trigger the scenario at a specific point in the simulation.
        """
        self.triggered = True
        self.football_actor.set_simulate_physics(True)
        self.football_actor.add_impulse(carla.Vector3D(x=0.0, y=35.0, z=40.0))
        print('Scenario -Ball on a Highway- has been triggered!')

    def destroy(self, client):
        """
        Destroys all actors spawned for the scenario.

        Args:
            client: The Carla client object.
        """
        print('\nScenario -Ball on a Highway- finished!')
        print('Scenario is destroying %d actors' % len(self.actor_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in self.actor_list])

def handle_collision(event):
    print('Ego vehicle collided with:', event.other_actor.type_id)



def main():
    path = '/home/vlmteam/VLM-Capstone-Project/images/'
    scenario_timer = 600
    vehicles_list = []
    walkers_list = []
    client = carla.Client('127.0.0.1', 2002)
    client.set_timeout(5.0)
    seed = int(time.time())
    random.seed(seed)

    try:
        world = client.get_world()
        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_global_distance_to_leading_vehicle(0.05)
        traffic_manager.set_random_device_seed(seed)
        traffic_manager.set_synchronous_mode(True)

        settings = world.get_settings()
        traffic_manager.set_synchronous_mode(True)
        if not settings.synchronous_mode:
            settings.synchronous_mode = True
            settings.fixed_delta_seconds = 0.05
        world.apply_settings(settings)

        # Create ego vehicle
        blueprint_library = world.get_blueprint_library()
        bp_ego_vehicle = blueprint_library.find('vehicle.dodge.charger_2020')
        bp_ego_vehicle.set_attribute('role_name', 'ego')
        # Spawn ego vehicle
        ego_vehicle_actor = world.spawn_actor(bp_ego_vehicle, carla.Transform(carla.Location(x=229.40, y=91.20, z=0.30), carla.Rotation(pitch=0, yaw=90, roll=0)))
        vehicles_list.append(ego_vehicle_actor)
        # Tick world to update the simulation
        world.tick()
        # Set ego vehicle autopilot, if you have custom ego vehicle controller,
        # you should disable autopilot and use your controller to control the ego vehicle here
        ego_vehicle_actor.set_autopilot(True)
        
        # Set ego vehicle lights on, add camera sensors if selected
        traffic_manager.update_vehicle_lights(ego_vehicle_actor, True)
        # Add collision sensor to ego vehicle
        collision_sensor = world.spawn_actor(blueprint_library.find('sensor.other.collision'), carla.Transform(), attach_to=ego_vehicle_actor)
        vehicles_list.insert(len(vehicles_list)-1,collision_sensor)
        collision_sensor.listen(
            collision_sensor.listen(handle_collision)
        )
        # Create RGB camera for ego vehicle
        bp_camera = blueprint_library.find('sensor.camera.rgb')
        bp_camera.set_attribute("image_size_x",str(1280))
        bp_camera.set_attribute("image_size_y",str(720))
        bp_camera.set_attribute("fov",str(90))
        bp_camera.set_attribute("sensor_tick",str(0.2))
        rgb_camera_transform = carla.Transform(carla.Location(2,0,1), carla.Rotation(0,0,0))
        rgb_camera = world.spawn_actor(bp_camera, rgb_camera_transform, attach_to=ego_vehicle_actor, attachment_type=carla.AttachmentType.Rigid)
        vehicles_list.insert(len(vehicles_list)-1,rgb_camera)
        rgb_camera.listen(lambda image: image.save_to_disk(path + 'rgb/%.6d.png' % image.frame))
        # Create Semantic camera for ego vehicle
        bp_semantic_camera = blueprint_library.find('sensor.camera.semantic_segmentation')
        bp_semantic_camera.set_attribute("image_size_x",str(1280))
        bp_semantic_camera.set_attribute("image_size_y",str(720))
        bp_semantic_camera.set_attribute("fov",str(90))
        bp_semantic_camera.set_attribute("sensor_tick",str(0.2))
        semantic_camera_transform = carla.Transform(carla.Location(2,0,1), carla.Rotation(0,0,0))
        semantic_camera = world.spawn_actor(bp_semantic_camera, semantic_camera_transform, attach_to=ego_vehicle_actor, attachment_type=carla.AttachmentType.Rigid)
        vehicles_list.insert(len(vehicles_list)-1,semantic_camera)
        semantic_camera.listen(lambda image: image.save_to_disk(path + 'semantic/%.6d.png' % image.frame,carla.ColorConverter.CityScapesPalette))
        
        # Tick world to update the simulation
        Scenario = None
        world.tick()

        # Set route for ego vehicle
        vehicle_path = ['Straight', 'Right']
        traffic_manager.set_route(ego_vehicle_actor, vehicle_path)
        #traffic_manager.ignore_lights_percentage(ego_vehicle_actor, 100)
        #traffic_manager.ignore_walkers_percentage(ego_vehicle_actor, 100)
        # If ego vehicle with traffic manager is on the outer lane, force lane change to inner lane
        #traffic_manager.force_lane_change(ego_vehicle_actor, False)
        #traffic_manager.auto_lane_change(ego_vehicle_actor, False)
        traffic_manager.vehicle_percentage_speed_difference(ego_vehicle_actor, -60.0)
        traffic_manager.auto_lane_change(ego_vehicle_actor, False)

        # Main loop
        try:
            while True:
                # Artificial delay for images to be saved
                time.sleep(0.1)
                # Check if a scenario is triggered
                if Scenario is None:
                    Scenario = FootballHighway(world, ego_vehicle_actor)
                else:
                    if scenario_timer > 0:
                        sucess = Scenario.tick(ego_vehicle_actor, traffic_manager)
                        if sucess == 1:
                            scenario_timer = 0
                        else:
                            scenario_timer -= 1
                    else:
                        Scenario.destroy(client)
                        Scenario = None
                        scenario_timer = 600
                        break
                        
                world.tick()
        except KeyboardInterrupt:
            pass

    finally:
        time.sleep(2.0)
        # Stop camera sensors to avoid errors
        collision_sensor.stop()
        rgb_camera.stop()
        semantic_camera.stop()
        world.tick()
        
        # Disable synchronous mode
        settings = world.get_settings()
        settings.synchronous_mode = False
        settings.no_rendering_mode = False
        settings.fixed_delta_seconds = None
        world.apply_settings(settings)

        # Destroy scenario
        if Scenario is not None:
            Scenario.destroy(client)
        # Destroy all actors
        print('\ndestroying %d vehicles' % len(vehicles_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])
        print('\ndestroying %d walkers' % len(walkers_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in walkers_list])

        time.sleep(0.5)
        print('done.')


if __name__ == '__main__':

    main()
