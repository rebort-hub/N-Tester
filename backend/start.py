#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动脚本
"""
import sys
import os

# 设置环境变量编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 启动应用
if __name__ == '__main__':
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8100,
        reload=False,
        log_level="info"
    )
