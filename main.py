tasks = []


def show_tasks():
    print("\n===== 我的待办事项 =====")

    if not tasks:
        print("目前没有任务。")
        return

    for i, task in enumerate(tasks, start=1):
        print(f"{i}. {task}")


def main():
    while True:
        print("\n===== LifeManager =====")
        print("1. 添加任务")
        print("2. 查看任务")
        print("0. 退出")

        choice = input("请选择功能：")

        if choice == "1":
            task = input("请输入任务名称：").strip()

            if task:
                tasks.append(task)
                print("任务添加成功！")
            else:
                print("任务名称不能为空。")

        elif choice == "2":
            show_tasks()

        elif choice == "0":
            print("感谢使用 LifeManager！")
            break

        else:
            print("无效选项，请重新输入。")


if __name__ == "__main__":
    main()