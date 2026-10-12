#-*-coding:GBK -*-
from __future__ import annotations

import argparse
import pathlib
import gradio as gr
import numpy as np

def create_demo_hw1(process):
    with gr.Blocks() as demo:
        gr.Markdown("## 作业一: 图像色相/饱和度/亮度/对比度调整工具")
        with gr.Row():
            with gr.Column():
                input_image = gr.Image(sources=['upload', 'webcam', 'clipboard'], type='numpy', label='输入图像')
                mode = gr.Radio(["色相/饱和度", "亮度/对比度"], label="模式", value="色相/饱和度")
                h_slider = gr.Slider(minimum=-1, maximum=1, label="色相", value=0, step=0.01)
                s_slider = gr.Slider(minimum=-1, maximum=1, label="饱和度", value=0, step=0.01)
                l_slider = gr.Slider(minimum=-1, maximum=1, label="明度", value=0, step=0.01)
                brightness = gr.Slider(minimum=-1, maximum=1, label="亮度", value=0, step=0.01, visible=False)
                contrast = gr.Slider(minimum=-1, maximum=1, label="对比度", value=0, step=0.01, visible=False)
            with gr.Column():
                with gr.Row():
                    output_image = gr.Image(type='numpy', label='输出图像', interactive=False)
                with gr.Row():
                    r_channel = gr.Image(type='numpy', label='R通道', interactive=False)
                    g_channel = gr.Image(type='numpy', label='G通道', interactive=False)
                    b_channel = gr.Image(type='numpy', label='B通道', interactive=False)
                with gr.Row():
                    h_channel = gr.Image(type='numpy', label='H通道', interactive=False)
                    s_channel = gr.Image(type='numpy', label='S通道', interactive=False)
                    l_channel = gr.Image(type='numpy', label='L通道', interactive=False)

        input_image.change(fn=process, 
                           inputs=[input_image, mode, h_slider, s_slider, l_slider, brightness, contrast], 
                           outputs=[output_image, r_channel, g_channel, b_channel, h_channel, s_channel, l_channel])

        def update_mode(mode):
            if mode == "色相/饱和度":
                return (
                    gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), 
                    gr.update(visible=False), gr.update(visible=False)
                )
            else:
                return (
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), 
                    gr.update(visible=True), gr.update(visible=True)
                )
        mode.change(update_mode, inputs=[mode], outputs=[h_slider, s_slider, l_slider, brightness, contrast])

        def slider_update(slider):
            return slider.release(
                fn=process, 
                inputs=[input_image, mode, h_slider, s_slider, l_slider, brightness, contrast], 
                outputs=[output_image, r_channel, g_channel, b_channel, h_channel, s_channel, l_channel]
            )

        slider_update(h_slider)
        slider_update(s_slider)
        slider_update(l_slider)
        slider_update(brightness)
        slider_update(contrast)

    return demo

def create_demo_hw2(process):
    with gr.Blocks() as demo:
        gr.Markdown('## 作业二: 基于GAN的图像生成编辑工具') 
        with gr.Row():
            with gr.Column():
                input_image = gr.Image(sources=['upload', 'webcam', 'clipboard'], type='numpy', label='输入图像')  
            with gr.Column():
                output_image = gr.Image(type='numpy', label='输出图像', interactive=False)
                run_button = gr.Button(value='运行')

        run_button.click(fn=process,
                        inputs=[input_image],
                        outputs=[output_image])
    return demo

def create_demo_hw3(process):
    with gr.Blocks() as demo:
        gr.Markdown("## 作业三: 替换屏幕内容工具")
        with gr.Row():
            with gr.Column():
                bg_img = gr.ImageEditor(sources=['upload', 'webcam', 'clipboard'], type='numpy', label='背景图像', 
                                        brush=gr.Brush(default_size=4, colors=["#FF0000"], color_mode="fixed"), eraser=False, layers=False)
                reset_btn = gr.Button('重新选择屏幕的4个顶点位置')
                fg_img = gr.Image(sources=['upload', 'webcam', 'clipboard'], type='numpy', label='前景图像')
                mode = gr.Radio(choices=['Nearest', 'Bilinear', 'Bicubic'], value='Nearest', label='插值方法')
            with gr.Column():
                output_image = gr.Image(type='numpy', label='输出图像', interactive=False)
                run_btn = gr.Button('替换屏幕内容为前景图像')

        def reset_points(bg_img):
            return bg_img["background"]
            
        reset_btn.click(fn=reset_points, inputs=[bg_img], outputs=[bg_img])
        run_btn.click(fn=process, inputs=[bg_img, fg_img, mode], outputs=[output_image])

    return demo

def create_demo_hw4(process):
    with gr.Blocks() as demo:
        gr.Markdown('## 作业四: 图像去噪工具') 
        with gr.Row():
            with gr.Column():
                input_image = gr.Image(sources=['upload', 'webcam', 'clipboard'], type='numpy', label='输入图像')  
            with gr.Column():
                output_image = gr.Image(type='numpy', label='输出图像', interactive=False)
                run_button = gr.Button(value='运行')

        run_button.click(fn=process,
                        inputs=[input_image],
                        outputs=[output_image])
    return demo

def create_demo_hw5(process):
    with gr.Blocks() as demo:
        gr.Markdown('## 作业五: 图像提亮工具') 
        with gr.Row():
            with gr.Column():
                input_image = gr.Image(sources=['upload', 'webcam', 'clipboard'], type='numpy', label='输入图像')  
            with gr.Column():
                output_image = gr.Image(type='numpy', label='输出图像', interactive=False)
                run_button = gr.Button(value='运行')

        run_button.click(fn=process,
                        inputs=[input_image],
                        outputs=[output_image])
    return demo