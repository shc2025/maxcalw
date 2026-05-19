#!/bin/bash
# 一次性设置两个周报cron + 确认脚本权限

set -e

SCRIPT="/workspace/scripts/send_weekly.py"
CHMOD_SCRIPT="/usr/bin/python3 $SCRIPT"

echo "=== 设置执行权限 ==="
chmod +x "$SCRIPT"

echo "=== 删除旧有周报cron ==="
for id in $(openclaw cron list --json 2>/dev/null | python3 -c "
import json,sys
data = json.load(sys.stdin)
for j in data if isinstance(data,list) else []:
    if '周报' in j.get('name',''):
        print(j['id'])
" 2>/dev/null); do
    echo "删除: $id"
    openclaw cron rm "$id" 2>/dev/null || true
done

echo "=== 创建cron1: 周六12:00 UTC = 北京时间20:00 ==="
openclaw cron add \
  --name "周六周报预览+复核" \
  --cron "0 12 * * 6" \
  --session isolated \
  --timeout-seconds 180 \
  --no-deliver \
  --message "Execute: python3 /workspace/scripts/send_weekly.py preview" \
  2>&1 || echo "cron1创建失败，尝试备用方式"

echo "=== 创建cron2: 周六12:30 UTC = 北京时间20:30 ==="
openclaw cron add \
  --name "周六周报自动发送" \
  --cron "30 12 * * 6" \
  --session isolated \
  --timeout-seconds 120 \
  --no-deliver \
  --message "Execute: python3 /workspace/scripts/send_weekly.py send" \
  2>&1 || echo "cron2创建失败，尝试备用方式"

echo "=== 验证cron列表 ==="
openclaw cron list 2>&1 | grep -E "周报|预览|发送" || echo "验证：无周报cron（可能已合并或命名不同）"

echo "=== 完成 ==="
