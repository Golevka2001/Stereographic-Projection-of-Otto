#!user/bin/env python
# -*- coding:utf-8 -*-
"""Stereographic-Projection-of-Otto:
@File: main.py
@Brief: 通过球极投影的方式得到otto的多种形态。
@Author: Golevka2001<gol3vka@163.com>
@Created Date: 2022/11/29
@Last Modified Date: 2022/12/01
"""

# 开导：
import os
import time

import numpy as np
import pygame
from PIL import Image

# --------------- 参数部分 --------------- #

# 原始图像路径：
path_img = './otto.png'
# 投影图像输出路径：
path_proj = './toot.png'

# 投影图像输出尺寸：
w_proj = 400
h_proj = 300

# 缩放倍数
scale = 1.5

# 坐标轴的旋转角度：
# 注：旋转是为了得到不同的球面投影情况（说的道理/栗子头）
alpha = 0 * np.pi / 180  # 绕x轴旋转角度
beta = 0 * np.pi / 180  # 绕y轴旋转角度（150°左右可得到栗子头）
gamma = 0 * np.pi / 180  # 绕z轴旋转角度

# --------------- 实现 --------------- #


def get_point_on_sphere(point: np.ndarray, r: float) -> np.ndarray:
    """计算z=0平面上一点Q与投影点D连线在球面上的交点P的坐标

    Args:
        point (np.ndarray): 点Q坐标
        r (float): 球半径

    Returns:
        np.ndarray: 球面上交点P的坐标
    """
    [x, y, z] = point
    k = 2 * r**2 / (x**2 + y**2 + r**2)  # 推导、化简得到的系数（推导过程见README.md）
    return np.array([k * x, k * y, (k - 1) * r], dtype=np.float32)


def axis_rotate(point: np.ndarray, rot_mat: np.ndarray) -> np.ndarray:
    """计算坐标系旋转后，点P坐标的变化

    Args:
        point (np.ndarray): 点P坐标
        rot_mat (np.ndarray): 旋转矩阵（推导过程见README.md）

    Returns:
        np.ndarray: 变换后的点P坐标
    """
    return np.dot(rot_mat, point)


def get_pix_on_img(point: np.ndarray, r: float, h_img: int,
                   w_img: int) -> tuple:
    """球面投影的逆过程，计算球面上一点P在原图像上的坐标

    Args:
        point (np.ndarray): 点P坐标
        r (float): 球半径
        h_img (int): 原始图像高度
        w_img (int): 原始图像宽度

    Returns:
        tuple: 对应在原始图像上的像素点坐标
    """
    [x, y, z] = point
    row = np.arccos(z / r) / np.pi
    col = np.arctan2(y, x) / 2 / np.pi + 0.5  # 加0.5是把图像中心移到平面y=0处
    # 坐标范围恢复到原始图像的尺寸：
    row = round(row * h_img) % h_img
    col = round(col * w_img) % w_img
    return (row, col)


def projection(pix_proj: tuple, r: float, h_img: int, w_img: int, h_proj: int,
               w_proj: int) -> tuple:
    """球极投影

    Args:
        pix_proj (tuple): 投影图像上的像素点坐标
        r (float): 球半径
        h_img (int): 原始图像高度
        w_img (int): 原始图像宽度
        h_proj (int): 投影图像高度
        w_proj (int): 投影图像宽度

    Returns:
        tuple: 对应在原始图像上的像素点坐标
    """
    # 投影图像上像素点坐标转为三维坐标：
    (row, col) = pix_proj
    x = row - h_proj / 2
    y = col - w_proj / 2
    z = 0
    Q = np.array([x, y, z], dtype=np.float32)
    P = get_point_on_sphere(Q, r)
    P = axis_rotate(P, rot_mat)
    return get_pix_on_img(P, r, h_img, w_img)


if __name__ == '__main__':
    pygame.mixer.init()
    pygame.mixer.music.load('bgm.wav')
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play()

    path_img = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            path_img)
    path_proj = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                             path_proj)

    arr_img = np.array(Image.open(path_img))
    arr_proj = np.zeros((h_proj, w_proj, 3), dtype=np.uint8)

    h_img = arr_img.shape[0]
    w_img = arr_img.shape[1]

    r = min(h_proj, w_proj) / 10 * scale  # 球的半径会影响到投影图像上呈现内容的多少

    # 这个总是被自动格式化成这样很丑
    rot_mat = np.array([[
        np.cos(gamma) * np.cos(beta),
        np.cos(gamma) * np.sin(beta) * np.sin(alpha) -
        np.sin(gamma) * np.cos(alpha),
        np.cos(gamma) * np.sin(beta) * np.cos(alpha) +
        np.sin(gamma) * np.sin(alpha)
    ],
                        [
                            np.sin(gamma) * np.cos(beta),
                            np.sin(gamma) * np.sin(beta) * np.sin(alpha) +
                            np.cos(gamma) * np.cos(alpha),
                            np.sin(gamma) * np.sin(beta) * np.cos(alpha) -
                            np.cos(gamma) * np.sin(alpha)
                        ],
                        [
                            -np.sin(beta),
                            np.cos(beta) * np.sin(alpha),
                            np.cos(beta) * np.cos(alpha)
                        ]])

    # 即把目标图像平铺在xy平面上（图片中心在O，所以注意坐标的范围）
    # 遍历每一个像素点，得到在球上的交点坐标，再由球面投影的逆变换对应到原图像上的像素点
    for pix_proj in np.ndindex(arr_proj.shape[:2]):
        pix_img = projection(pix_proj, r, h_img, w_img, h_proj, w_proj)
        arr_proj[pix_proj] = arr_img[pix_img]

    Image.fromarray(arr_proj).show()  # 注释掉这行可以不弹出显示
    Image.fromarray(arr_proj).save(path_proj)  # 注释掉这行可以不输出文件

    time.sleep(15)
