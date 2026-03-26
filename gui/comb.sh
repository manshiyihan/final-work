#!/bin/bash
# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 如果conda已安装，尝试激活环境（可选）
# source /home/xujiwu/anaconda3/etc/profile.d/conda.sh
# conda activate mfa

# 指定Python解释器版本
PYTHON_EXECUTABLE="python3"

# 定义Python脚本的路径和其他参数（使用相对路径）
PYTHON_SCRIPT="$SCRIPT_DIR/comb.py"
TEST_AUDIO="$SCRIPT_DIR/../wav/rec1.wav"  # 示例路径，请根据实际情况修改

#执行Python脚本
python "$PYTHON_SCRIPT" --audio_path="$TEST_AUDIO"