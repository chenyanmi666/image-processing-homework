# 图像处理作业四

使用 Python 3.9 安装 requirements.txt，运行 python web_demo.py 并打开作业4页面。基础区比较手写导向滤波和双边滤波的去噪及锐化。进阶区展示积分图导向滤波和 BM3D 的硬阈值、维纳估计。程序生成的示例使用标准差15的高斯噪声。

BM3D 使用正交 DCT 和共享亮度匹配，界面支持长边不超过512像素的图像。

参考资料：

- [Guided Image Filtering](https://people.csail.mit.edu/kaiming/publications/pami12guidedfilter.pdf)
- [Image Denoising by Sparse 3-D Transform-Domain Collaborative Filtering](https://webpages.tuni.fi/foi/GCF-BM3D/BM3D_TIP_2007.pdf)
