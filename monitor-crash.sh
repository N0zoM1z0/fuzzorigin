#!/bin/bash

BASE_DIR="tests"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
GREY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}=== Fuzzing Crash Monitor ===${NC}"
printf "%-20s | %-10s | %s\n" "Directory" "Status" "Count"
echo -e "${GREY}----------------------------------------${NC}"

total_crashes=0

# 遍历目录，使用 sort -V 进行自然数字排序
for dir in $(ls $BASE_DIR | grep "output_" | sort -V); do
    crash_dir="$BASE_DIR/$dir/crash"
    
    if [ -d "$crash_dir" ]; then
        # 统计文件数量
        count=$(ls -1 "$crash_dir" 2>/dev/null | wc -l)
        
        if [ "$count" -gt 0 ]; then
            total_crashes=$((total_crashes + count))
            printf "${GREEN}%-20s${NC} | ${RED}%-10s${NC} | ${RED}%s files${NC}\n" "$dir" "💥 CRASH" "$count"
        else
            printf "${GREY}%-20s | %-10s | %s${NC}\n" "$dir" "✓ Clean" "$count"
        fi
    fi
done

echo -e "${GREY}----------------------------------------${NC}"
if [ "$total_crashes" -gt 0 ]; then
    echo -e "${RED}Total Crashes Found: $total_crashes${NC}\n"
else
    echo -e "${GREEN}No crashes found.${NC}\n"
fi
