#-*-coding:GBK -*-
from __future__ import annotations

import argparse
import pathlib
import gradio as gr
import numpy as np

def create_demo_hw1(process, process_compare=None):
    """作业一界面（图像色相/饱和度/亮度/对比度调整工具）。

    模式共 5 种：
      色相/饱和度                ：手写 HSL(HSI)，按课件 p72-p78 的数学定义
      色相/饱和度 (官方cv2 HLS)  ：直接调用 cv2.COLOR_BGR2HLS（L=(max+min)/2）
      自然饱和度 (PS vibrance)   ：PS 风格自然饱和度（复用"饱和度"滑杆作为强度）
      亮度/对比度                ：自定义线性模型
      亮度/对比度 (PS风格)       ：PS 风格非线性模型（S 曲线 + gamma 亮度）

    process_compare 为可选的"进阶①：手写 vs 官方 cv2 HLS 对比实验"函数；
    传入时界面多出对比按钮与结果区，不传时界面与模板行为一致。
    """
    with gr.Blocks() as demo:
        gr.Markdown("## 作业一: 图像色相/饱和度/亮度/对比度调整工具")
        gr.Markdown("说明：手写路径按课件 p72-p78 的 HSL(HSI) 定义"
                    "（亮度 L=(R+G+B)/3）；官方路径直接调用 cv2.COLOR_BGR2HLS"
                    "（亮度 L=(max+min)/2）。两者不是同一个数学模型，可用【对比实验】按钮查看差异。")
        with gr.Row():
            with gr.Column():
                input_image = gr.Image(sources=['upload', 'webcam', 'clipboard'], type='numpy', label='输入图像')
                mode = gr.Radio(["色相/饱和度", "色相/饱和度 (官方cv2 HLS)", "自然饱和度 (PS vibrance)",
                                 "亮度/对比度", "亮度/对比度 (PS风格)"],
                                label="模式（前三项用色相/饱和度/明度滑杆，后两项用亮度/对比度滑杆）",
                                value="色相/饱和度")
                h_slider = gr.Slider(minimum=-1, maximum=1, label="色相", value=0, step=0.01)
                s_slider = gr.Slider(minimum=-1, maximum=1, label="饱和度", value=0, step=0.01)
                l_slider = gr.Slider(minimum=-1, maximum=1, label="明度", value=0, step=0.01)
                brightness = gr.Slider(minimum=-1, maximum=1, label="亮度", value=0, step=0.01, visible=False)
                contrast = gr.Slider(minimum=-1, maximum=1, label="对比度", value=0, step=0.01, visible=False)
                if process_compare is not None:
                    compare_button = gr.Button(value="进阶①：手写 HSL vs 官方 cv2 HLS 对比实验")
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
                if process_compare is not None:
                    compare_image = gr.Image(type='numpy', interactive=False,
                                             label='对比图：原图 | 手写(课件定义) | 官方cv2 HLS | 差异×5')
                    compare_text = gr.Markdown()

        input_image.change(fn=process, 
                           inputs=[input_image, mode, h_slider, s_slider, l_slider, brightness, contrast], 
                           outputs=[output_image, r_channel, g_channel, b_channel, h_channel, s_channel, l_channel])

        def update_mode(mode):
            """按模式显示对应滑杆；自然饱和度模式下"饱和度"滑杆即自然饱和度强度。"""
            if mode == "自然饱和度 (PS vibrance)":
                return (
                    gr.update(visible=False), gr.update(visible=True, label="自然饱和度"), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False)
                )
            if mode in ("亮度/对比度", "亮度/对比度 (PS风格)"):
                return (
                    gr.update(visible=False), gr.update(visible=False, label="饱和度"), gr.update(visible=False),
                    gr.update(visible=True), gr.update(visible=True)
                )
            return (
                gr.update(visible=True), gr.update(visible=True, label="饱和度"), gr.update(visible=True),
                gr.update(visible=False), gr.update(visible=False)
            )
        mode.change(update_mode, inputs=[mode], outputs=[h_slider, s_slider, l_slider, brightness, contrast])

        if process_compare is not None:
            compare_button.click(fn=process_compare,
                                 inputs=[input_image, h_slider, s_slider, l_slider],
                                 outputs=[compare_image, compare_text])

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