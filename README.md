# SJTU - 从教学信息服务网提取课表

本项目用于从教学信息服务网 (i.sjtu.edu.cn) 提取课表信息，并制作 ics 文件. 

使用方式:

1. 下载本项目
2. 安装依赖: `pip install -r requirements.txt`
3. 在 `main.py` 中填写需要读取的学年与学期

    示例: 如要获取 2024-2025-2 学期的课表，请填写
    ```python
    year = 2024
    term = 2
    ```

4. 运行 `python main.py`，若是首次运行，需要扫描命令行中的二维码登录，登录后会在 `scripts/` 目录下生成 `cookies.json` 文件，存储用于登录 jAccount 认证的 `JAAuthCooike` 信息
5. 程序会在当前目录下生成 `cal.ics` 文件，导入到日历软件（如 Apple 日历）中即可

## 待更新 - 调休

初步设计

1. 调休日期获取:

    - 从校历中获取调休日期: from Date1 to Date2
    - 日期转换 (date) -> (week, weekday)

2. 事件表修改

    1. 先识别 weekday
    2. 识别周数是否覆盖

        - 单次课程: 直接匹配周数
        - 每周课程: start <= week <= end
        - 单双周课程: start <= week <= end && (week - start) % interval == 0

    3. 调整日程

        - 单次课程: 直接修改日期
        - 每周课程: 修改当次日期，切割前后事件
        - 单双周课程: 修改当次日期，切割前后事件（注意周数换算）