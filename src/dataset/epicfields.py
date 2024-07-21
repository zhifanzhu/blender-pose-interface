from collections import namedtuple
from typing import List
import numpy as np
import json
from src.math_utils import qvec2rotmat


def load_sfm(vid: str, frames: List[int]) -> namedtuple:
    """
    Args:
        frames: List[int], list of frame indices to load

    Returns:
        camera: {
            "id": 1, "model": "OPENCV", "width": 456, "height": 256,
            "params": [fx, fy, cx, cy, k1, k2, p1, p2] },
        points: (N, 3)
        colors: (N, 3) 0-1
    """
    retVal = namedtuple('SFM', 'camera c2w points colors')
    path = f'./data/{vid}.json'
    with open(path) as f:
        sfm = json.load(f)

    # Camera
    camera = sfm['camera']

    points = sfm['points']
    points = np.array(points)
    points, colors = points[:, :3], points[:, 3:]/255.
    colors = np.hstack([colors, np.ones((colors.shape[0], 1))])  # Add alpha channel

    c2ws = dict()
    if frames is not None:
        for f in frames:
            key = f'frame_{f:010d}.jpg'
            param = sfm['images'][key]
            c2w = get_c2w(param)
            c2ws[f] = c2w
    else:
        for key, param in sfm['images'].items():
            frame = int(key.split('_')[-1].split('.')[0])
            c2w = get_c2w(param)
            c2ws[key] = c2w

    return retVal(camera, c2ws, points, colors)


def get_c2w(img_data: list) -> np.ndarray:
    """
    Args:
        img_data: list, [qvec, tvec] of w2c
    
    Returns:
        c2w: np.ndarray, 4x4 camera-to-world matrix
    """
    w2c = np.eye(4)
    w2c[:3, :3] = qvec2rotmat(img_data[:4])
    w2c[:3, -1] = img_data[4:7]
    c2w = np.linalg.inv(w2c)
    return c2w