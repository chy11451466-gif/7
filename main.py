import json
from pathlib import Path
from datetime import date

DATA_FILE = Path(__file__).with_name("lifemanager_data.json")


def load_data():
    """读取保存的数据"""
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                tasks = data.get("tasks", [])
                study = data.get("study", {})

                if (
                    isinstance(tasks, list)
                    and all(
                        isinstance(task, dict)
                        and isinstance(task.get("title"), str)
                        and isinstance(task.get("done"), bool)
                        for task in tasks
                    )
                    and isinstance(study, dict)
                    and all(
                        isinstance(key, str)
                        and isinstance(value, (int, float))
                        and not isinstance(value, bool)
                        and value >= 0
                        for key, value in study.items()
                    )
                ):
                    return {"tasks": tasks, "study": study}

        except (OSError, json.JSONDecodeError):
            pass

    return {"tasks": [], "study": {}}


def save_data(data):
    """永久保存任务和学习记录"""
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def add_task(data):
    title = input("请输入任务名称：").strip()

    if not title:
        print("任务名称不能为空！")
        return

    data["tasks"].append({
        "title": title,
        "done": False,
        "created_at": date.today().isoformat()
    })

    save_data(data)
    print("任务添加成功！")


def show_tasks(data):
    tasks = data["tasks"]

    print("\n===== 我的任务 =====")

    if not tasks:
        print("目前没有任务。")
        return

    for i, task in enumerate(tasks, start=1):
        status = "已完成" if task["done"] else "未完成"
        print(f'{i}. [{status}] {task["title"]}')


def complete_task(data):
    show_tasks(data)

    tasks = data["tasks"]

    if not tasks:
        return

    try:
        number = int(input("请输入已完成的任务编号："))

        if 1 <= number <= len(tasks):
            tasks[number - 1]["done"] = True
            save_data(data)
            print("任务已完成！")
        else:
            print("编号不存在。")

    except ValueError:
        print("请输入有效的数字。")


def record_study(data):
    """记录今天的学习时间"""
    try:
        minutes = int(input("今天学习了多少分钟？"))

        if minutes <= 0:
            print("请输入大于 0 的分钟数。")
            return

        today = date.today().isoformat()
        study = data["study"]

        study[today] = study.get(today, 0) + minutes

        save_data(data)

        print(f"记录成功！今天累计学习 {study[today]} 分钟。")

    except ValueError:
        print("请输入整数分钟数。")


def show_statistics(data):
    """显示任务和学习统计"""
    tasks = data["tasks"]

    total = len(tasks)
    completed = sum(task["done"] for task in tasks)
    unfinished = total - completed

    rate = completed / total * 100 if total else 0

    today = date.today().isoformat()
    today_minutes = data["study"].get(today, 0)

    total_minutes = sum(data["study"].values())

    print("\n===== 每日统计 =====")
    print(f"任务总数：{total}")
    print(f"已完成：{completed}")
    print(f"未完成：{unfinished}")
    print(f"任务完成率：{rate:.1f}%")
    print(f"今日学习：{today_minutes} 分钟")
    print(f"累计学习：{total_minutes} 分钟")
    print("====================")


def main():
    data = load_data()

    while True:
        print("\n===== LifeManager =====")
        print("1. 添加任务")
        print("2. 查看任务")
        print("3. 完成任务")
        print("4. 记录学习时间")
        print("5. 查看统计")
        print("0. 退出程序")

        choice = input("请选择功能：").strip()

        if choice == "1":
            add_task(data)

        elif choice == "2":
            show_tasks(data)

        elif choice == "3":
            complete_task(data)

        elif choice == "4":
            record_study(data)

        elif choice == "5":
            show_statistics(data)

        elif choice == "0":
            print("感谢使用 LifeManager！")
            break

        else:
            print("无效选项，请重新输入。")


if __name__ == "__main__":
    main()