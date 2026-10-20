import json
import os
import tempfile
from pathlib import Path
from datetime import date, timedelta

APP_NAME = "LifeManager"
VERSION = "2.0.0"

DATA_FILE = Path(__file__).with_name("lifemanager_data.json")
BACKUP_FILE = Path(__file__).with_name("lifemanager_data.json.bak")


def empty_data():
    return {
        "tasks": [],
        "study": {},
        "next_id": 1
    }


def load_data():
    """读取数据，出错时尝试读取备份。"""
    for path in (DATA_FILE, BACKUP_FILE):
        if not path.exists():
            continue

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, dict):
                continue

            tasks = data.get("tasks", [])
            study = data.get("study", {})
            next_id = data.get("next_id", 1)

            if not isinstance(tasks, list) or not isinstance(study, dict):
                continue

            if (
                not isinstance(next_id, int)
                or isinstance(next_id, bool)
                or next_id < 1
            ):
                continue

            valid = True

            for task in tasks:
                if not isinstance(task, dict):
                    valid = False
                    break

                if (
                    not isinstance(task.get("title"), str)
                    or not task["title"].strip()
                    or not isinstance(task.get("done"), bool)
                    or not isinstance(task.get("id"), int)
                    or isinstance(task.get("id"), bool)
                    or task["id"] < 1
                ):
                    valid = False
                    break

            for day, minutes in study.items():
                try:
                    date.fromisoformat(day)
                except (ValueError, TypeError):
                    valid = False
                    break

                if (
                    not isinstance(minutes, int)
                    or isinstance(minutes, bool)
                    or minutes < 0
                ):
                    valid = False
                    break

            if valid:
                if path == BACKUP_FILE:
                    print("已从备份文件读取数据。")
                return {
                    "tasks": tasks,
                    "study": study,
                    "next_id": max(
                        next_id,
                        max(
                            (task["id"] for task in tasks),
                            default=0
                        ) + 1
                    )
                }

        except (OSError, json.JSONDecodeError):
            continue

    if DATA_FILE.exists() or BACKUP_FILE.exists():
        print("错误：数据文件损坏，无法安全读取。")
        print("请检查数据文件，避免覆盖原有数据。")
        raise SystemExit(1)

    return empty_data()


def save_data(data):
    """安全保存数据，并保留上一份有效数据备份。"""
    temp_path = None
    backup_temp = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_FILE.parent,
            delete=False
        ) as file:
            temp_path = Path(file.name)
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        # 备份现有的主文件
        if DATA_FILE.exists():
            try:
                with DATA_FILE.open("r", encoding="utf-8") as file:
                    old_data = json.load(file)

                if isinstance(old_data, dict):
                    with tempfile.NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        dir=DATA_FILE.parent,
                        delete=False
                    ) as file:
                        backup_temp = Path(file.name)
                        json.dump(
                            old_data,
                            file,
                            ensure_ascii=False,
                            indent=2
                        )
                        file.write("\n")
                        file.flush()
                        os.fsync(file.fileno())

                    os.replace(backup_temp, BACKUP_FILE)
                    backup_temp = None

            except (OSError, json.JSONDecodeError):
                print("提示：无法更新备份，保留原有备份。")

        os.replace(temp_path, DATA_FILE)
        temp_path = None
        return True

    except OSError as error:
        print(f"保存失败：{error}")
        return False

    finally:
        for path in (temp_path, backup_temp):
            if path is not None and path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass


def input_number(prompt, minimum, maximum):
    try:
        number = int(input(prompt).strip())

        if minimum <= number <= maximum:
            return number

        print(f"请输入 {minimum} 到 {maximum} 之间的数字。")

    except ValueError:
        print("输入无效，请输入数字。")

    return None


def confirm(prompt):
    return input(prompt + " (y/n)：").strip().lower() == "y"


def show_tasks(data):
    print("\n===== 我的任务 =====")

    if not data["tasks"]:
        print("目前没有任务。")
        return

    for task in data["tasks"]:
        status = "已完成" if task["done"] else "未完成"
        print(
            f'编号 {task["id"]} | '
            f'[{status}] | {task["title"]}'
        )


def add_task(data):
    title = input("请输入任务名称：").strip()

    if not title:
        print("任务名称不能为空。")
        return

    if len(title) > 200:
        print("任务名称不能超过 200 个字符。")
        return

    task = {
        "id": data["next_id"],
        "title": title,
        "done": False,
        "created_at": date.today().isoformat(),
        "completed_at": None
    }

    data["tasks"].append(task)
    data["next_id"] += 1

    if save_data(data):
        print("任务添加成功！")
    else:
        data["tasks"].pop()
        data["next_id"] -= 1


def find_task(data):
    if not data["tasks"]:
        print("目前没有任务。")
        return None

    show_tasks(data)

    task_id = input_number(
        "请输入任务编号：",
        1,
        2147483647
    )

    if task_id is None:
        return None

    for task in data["tasks"]:
        if task["id"] == task_id:
            return task

    print("没有找到这个任务。")
    return None


def complete_task(data):
    task = find_task(data)

    if task is None:
        return

    if task["done"]:
        print("这个任务已经完成。")
        return

    task["done"] = True
    task["completed_at"] = date.today().isoformat()

    if save_data(data):
        print("恭喜你，任务完成！")
    else:
        task["done"] = False
        task["completed_at"] = None


def reopen_task(data):
    task = find_task(data)

    if task is None:
        return

    if not task["done"]:
        print("这个任务还没有完成。")
        return

    task["done"] = False
    old_date = task.get("completed_at")
    task["completed_at"] = None

    if save_data(data):
        print("任务已重新设为未完成。")
    else:
        task["done"] = True
        task["completed_at"] = old_date


def edit_task(data):
    task = find_task(data)

    if task is None:
        return

    title = input("请输入新的任务名称：").strip()

    if not title:
        print("任务名称不能为空。")
        return

    if len(title) > 200:
        print("任务名称不能超过 200 个字符。")
        return

    old_title = task["title"]
    task["title"] = title

    if save_data(data):
        print("修改成功！")
    else:
        task["title"] = old_title


def delete_task(data):
    task = find_task(data)

    if task is None:
        return

    if not confirm(f'确定删除「{task["title"]}」吗？'):
        print("已取消删除。")
        return

    index = data["tasks"].index(task)
    removed = data["tasks"].pop(index)

    if save_data(data):
        print("删除成功！")
    else:
        data["tasks"].insert(index, removed)


def record_study(data):
    minutes = input_number(
        "今天学习了多少分钟？",
        1,
        1440
    )

    if minutes is None:
        return

    today = date.today().isoformat()
    old_minutes = data["study"].get(today, 0)

    data["study"][today] = old_minutes + minutes

    if save_data(data):
        print(
            f"记录成功！今天累计学习 "
            f"{data['study'][today]} 分钟。"
        )
    else:
        data["study"][today] = old_minutes


def study_history(data):
    text = input(
        "请输入日期 YYYY-MM-DD（回车查看今天）："
    ).strip()

    if not text:
        text = date.today().isoformat()

    try:
        selected_date = date.fromisoformat(text)
    except ValueError:
        print("日期格式错误。")
        return

    minutes = data["study"].get(
        selected_date.isoformat(),
        0
    )

    print(
        f"{selected_date.isoformat()} "
        f"学习时间：{minutes} 分钟"
    )


def statistics(data):
    tasks = data["tasks"]

    total = len(tasks)
    completed = sum(task["done"] for task in tasks)
    unfinished = total - completed

    today = date.today().isoformat()
    today_minutes = data["study"].get(today, 0)
    total_minutes = sum(data["study"].values())

    print("\n===== 数据统计 =====")
    print(f"任务总数：{total}")
    print(f"已完成：{completed}")
    print(f"未完成：{unfinished}")

    if total:
        print(f"完成率：{completed / total * 100:.1f}%")
    else:
        print("完成率：暂无任务")

    print(f"今日学习：{today_minutes} 分钟")
    print(f"累计学习：{total_minutes} 分钟")
    print("====================")


def weekly_report(data):
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    total_minutes = 0
    study_days = 0

    print("\n===== 本周学习报告 =====")

    for offset in range((today - monday).days + 1):
        current = monday + timedelta(days=offset)
        minutes = data["study"].get(
            current.isoformat(),
            0
        )

        print(f"{current.isoformat()}：{minutes} 分钟")

        total_minutes += minutes

        if minutes > 0:
            study_days += 1

    days = (today - monday).days + 1

    print("------------------------")
    print(f"本周学习：{total_minutes} 分钟")
    print(f"学习天数：{study_days} 天")
    print(f"每日平均：{total_minutes / days:.1f} 分钟")
    print("========================")


def export_data(data):
    filename = input(
        "导出文件名（回车使用 lifemanager_export.json）："
    ).strip()

    if not filename:
        filename = "lifemanager_export.json"

    path = Path(filename)

    if path.name != filename or path.suffix.lower() != ".json":
        print("请输入当前目录下的 JSON 文件名。")
        return

    try:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        print(f"导出成功：{path.resolve()}")

    except OSError as error:
        print(f"导出失败：{error}")


def main():
    data = load_data()

    while True:
        print(f"\n===== {APP_NAME} V{VERSION} =====")
        print("1. 添加任务")
        print("2. 查看任务")
        print("3. 完成任务")
        print("4. 修改任务")
        print("5. 删除任务")
        print("6. 重新打开已完成任务")
        print("7. 记录学习时间")
        print("8. 查询学习记录")
        print("9. 每周学习报告")
        print("10. 数据统计")
        print("11. 导出数据备份")
        print("0. 退出")

        choice = input("请选择功能：").strip()

        actions = {
            "1": lambda: add_task(data),
            "2": lambda: show_tasks(data),
            "3": lambda: complete_task(data),
            "4": lambda: edit_task(data),
            "5": lambda: delete_task(data),
            "6": lambda: reopen_task(data),
            "7": lambda: record_study(data),
            "8": lambda: study_history(data),
            "9": lambda: weekly_report(data),
            "10": lambda: statistics(data),
            "11": lambda: export_data(data)
        }

        if choice == "0":
            print("感谢使用 LifeManager！")
            break

        action = actions.get(choice)

        if action:
            try:
                action()
            except (KeyboardInterrupt, EOFError):
                print("\n操作已取消。")
        else:
            print("无效选项，请重新输入。")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n程序已退出。")