#-*-coding:GBK -*-
import numpy as np
import gradio as gr


def function_hw1(input_image, mode, h_slider, s_slider, l_slider, brightness, contrast):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)    
    
    # 请补充作业1的图像处理代码
    if mode == "色相/饱和度":
        pass
    else:
        pass
    output_image = input_image

    return [output_image] * 7


def function_hw2(input_image):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)    
    output_image = input_image
    # 请补充作业2的图像处理代码
    return output_image

def function_hw3(bg_image, fg_image, mode):
    if bg_image["background"]is None:
        raise gr.Error('输入错误：在处理之前请先输入一张背景图像', duration=5)  
    if fg_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张前景图像', duration=5)     
    background = bg_image["background"]
    mask_layer = bg_image["layers"][0][:, :, 0]
    import cv2
    _, binary = cv2.threshold(mask_layer, 127, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
    centers = [tuple(centroids[i]) for i in range(1, num_labels)]
    if len(centers) != 4:
        raise gr.Error("输入错误：请提供屏幕的四个顶点位置!")
    
    output_image = background
    # 请补充作业3的图像处理代码
    return output_image

def function_hw4(input_image):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)
    output_image = input_image
    # 请补充作业4的图像处理代码
    return output_image

def function_hw5(input_image):
    if input_image is None:
        raise gr.Error('输入错误：在处理之前请先输入一张图像', duration=5)
    output_image = input_image
    # 请补充作业5的图像处理代码
    return output_image