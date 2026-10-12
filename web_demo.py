from __future__ import annotations

import argparse
import pathlib
import gradio as gr
import gradio_compat

gradio_compat.install()  # gradio 3.x -> 4.x API shim (see gradio_compat.py)

from UI import *
from functions import *


HTML_DESCRIPTION = '''
<div align=center>
<h1 style="font-weight: 900; margin-bottom: 7px;">
   图像处理网页演示工具</a>
</h1>
<p>使用方式，在浏览器中打开http://127.0.0.1:8088/即可</p>
<p>作者: 图小像</p>
<p>学号: 2400013156</p>
</div>
'''
MD_DESCRIPTION = '''
## 此网页演示提供以下图像处理工具:
- 作业1：图像色相/饱和度/亮度/对比度调整工具
- 作业2：基于GAN的图像生成编辑工具
- 作业3：替换屏幕内容工具 (或基于深度学习的图像超分辨率工具)
- 作业4：图像去噪工具
- 作业5：图像提亮工具
'''

def main():
    with gr.Blocks(css='style.css') as demo:
        gr.Markdown(HTML_DESCRIPTION) 
        gr.Markdown(MD_DESCRIPTION)
        with gr.Tabs():
            with gr.TabItem('作业1: 图像色相/饱和度/亮度/对比度调整工具'):
                create_demo_hw1(function_hw1)          
            with gr.TabItem('作业2: 基于GAN的图像生成编辑工具'):
                create_demo_hw2(function_hw2)   
            with gr.TabItem('作业3: 替换屏幕内容工具'):
                create_demo_hw3(function_hw3)  
            with gr.TabItem('作业4: 图像去噪工具'):
                create_demo_hw4(function_hw4) 
            with gr.TabItem('作业5: 图像提亮工具'):
                create_demo_hw5(function_hw5)                                    

    demo.launch(server_port=8088)

if __name__ == '__main__':
    main()