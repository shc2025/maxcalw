#!/usr/bin/env python3
"""
手动确认发送周报
用法: python3 /workspace/scripts/confirm_weekly.py
或当你回复"确认"时，由主session调用此脚本
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from send_weekly import manual_confirm, STATE_FILE, read_state

if __name__ == "__main__":
    state = read_state()
    if state.get("phase") == "sent":
        print("周报已经发送过了，无需重复确认。")
    elif state.get("phase") == "waiting":
        print("正在确认并发送完整周报...")
        ok = manual_confirm()
        print("发送成功!" if ok else "发送失败，请检查日志。")
    else:
        print(f"当前状态: {state.get('phase', 'unknown')}")
        print("请先运行第一阶: python3 /workspace/scripts/send_weekly.py preview")
