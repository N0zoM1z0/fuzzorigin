import subprocess
import time
import signal
import sys
import os

# ================= 配置区域 =================
# 你的 Chrome 路径 (注意检查路径是否正确)
CHROME_PATH = "chrome/143.0.7499.109_1536376/chrome"

# 并行数量：建议设置为 CPU 核心数的 50% - 80%
# 比如 64 核机器，可以先试 30 个
NUM_INSTANCES = 40 

# 起始 IDX：如果你有多台机器，可以改这个，防止冲突
START_IDX = 0 
# ===========================================

processes = []

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def signal_handler(sig, frame):
    print(f"\n[!] 正在停止所有 {len(processes)} 个 Fuzzer 进程...")
    for p in processes:
        try:
            p.terminate()  # 发送 SIGTERM
            # p.kill()     # 如果关不掉，可以用 kill 强制杀
        except Exception:
            pass
    print("[+] 所有进程已停止。")
    sys.exit(0)

def main():
    # 捕获 Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建日志目录
    ensure_dir("fuzzer_logs")

    print(f"[+] 准备启动 {NUM_INSTANCES} 个 Fuzzer 实例...")
    print(f"[+] Chrome 路径: {CHROME_PATH}")

    for i in range(NUM_INSTANCES):
        idx = START_IDX + i
        
        # 构造命令: python3 -m src.fuzzer.fuzzer chrome [path] [idx]
        cmd = [
            "python3", 
            "-m", "src.fuzzer.fuzzer", 
            "chrome", 
            CHROME_PATH, 
            str(idx)
        ]
        
        # 日志重定向到 fuzzer_logs/fuzzer_0.log 等
        log_file_path = os.path.join("fuzzer_logs", f"fuzzer_{idx}.log")
        log_file = open(log_file_path, "w")
        
        # 启动子进程
        p = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
        processes.append(p)
        
        print(f"[*] 启动实例 IDX={idx} (PID: {p.pid}) -> 日志: {log_file_path}")
        
        # 稍微等待一下，错峰启动，避免瞬间 CPU 100% 卡死
        time.sleep(1) 

    print(f"\n[+] 成功启动 {NUM_INSTANCES} 个实例。")
    print(f"[+] 请使用 'tail -f fuzzer_logs/fuzzer_0.log' 查看状态。")
    print(f"[+] 按 Ctrl+C 可以一键停止所有任务。\n")

    # 保持主进程活着，监控子进程
    while True:
        # 检查有没有子进程意外退出的（可选逻辑）
        for p in processes:
            if p.poll() is not None:
                # 这里可以加逻辑重启挂掉的 fuzzer，或者只是忽略
                pass
        time.sleep(5)

if __name__ == "__main__":
    main()
