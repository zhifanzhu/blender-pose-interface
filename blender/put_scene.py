import sys
import mathutils
import numpy as np
import bpy

from src.dataset.epicfields import load_sfm
from blender.creation import create_point_cloud


"""Usage
Blender --python put_scene.py -- <args>

This script needs: vrs, slam_traj, [pinhole-mp4]

This script is tested with Blender 4.1.1 on MacOS
"""

def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:]  # get all args after "--"
    start = int(argv[0])
    end = int(argv[1])
    return start, end


def main():
    f_start, f_end = parse_args()
    T_opencv_to_blender = np.array([
        [1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, 0],
        [0, 0, 0, 1]])

    """ Remove the default cube """
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()


    frames = list(range(int(f_start), int(f_end)))
    sfm = load_sfm('P22_07', frames)
    focal_x = sfm.camera['params'][0]
    reso_x, reso_y = sfm.camera['width'], sfm.camera['height']
    c2ws = sfm.c2w

    # Need 'Cycle' render engine to see the color
    bpy.context.scene.render.engine = 'CYCLES'

    # pts = reader.load_filtered_points(threshold_dep=0.05, threshold_invdep=0.001, as_open3d=False)
    pcd_mesh = create_point_cloud(
        sfm.points, name='PointCloud', colors=sfm.colors,
        collection_name='Collection', point_size=0.005)

    # Set camera extrinsics
    Camera = bpy.data.objects['Camera']
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_start = f_start
    # Blender can do at most 1e6 frames -- 4 Hours for 60FPS
    bpy.context.scene.frame_end = f_end  
    Camera.rotation_mode = 'QUATERNION'
    for f, pose in c2ws.items():
        if pose is not None:
            matrix_world = pose @ T_opencv_to_blender
            matrix = mathutils.Matrix(matrix_world)
            Camera.location = matrix.to_translation()
            Camera.keyframe_insert(data_path='location', frame=f)
            Camera.rotation_quaternion = matrix.to_quaternion()
            Camera.keyframe_insert(data_path='rotation_quaternion', frame=f)

    # Set camera intrinsics
    Camera.data.type = 'PERSP'
    Camera.data.sensor_width = 32  # Default by Blender
    Camera.data.lens = focal_x / reso_x * Camera.data.sensor_width  # Hypothesis: focal_x/reso_x == lens/sensor_width
    bpy.context.scene.render.resolution_x = reso_x
    bpy.context.scene.render.resolution_y = reso_y

    # Add a reference Video overlaid onto the Camera
    # create_video_to_camera(mp4_path=mp4_path,
    #                        Camera=Camera, 
    #                        frame_duration=len(pinholecw90_poses),
    #                        name='RefVideo')

"""Notes
# Blender read col-major! Hence transpose
matrix_world = pinholecw90_poses[frame] @ T_opencv_to_blender
Camera.matrix_world = matrix_world.T  
"""


if __name__ == '__main__':
    main()
    # Uncomment to save the scene into a .blend file
    # bpy.ops.wm.save_as_mainfile(filepath='/Users/ms21614/Desktop/try.blend')
    # print('Saved!')