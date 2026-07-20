import time
import threading
import asyncio
from datetime import datetime

# 模拟推理任务：阻塞等待1秒
def simulate_infer_sync(task_id):
    time.sleep(1)
    return f"任务{task_id}推理完成"

# 异步模拟推理
async def simulate_infer_async(task_id):
    await asyncio.sleep(1)
    return f"任务{task_id}推理完成"

# 1. 串行执行
def run_serial():
    print("===== 1. 串行执行 =====")
    start = datetime.now()
    for i in range(5):
        res = simulate_infer_sync(i)
        print(res)
    end = datetime.now()
    cost = (end - start).total_seconds()
    print(f"串行总耗时：{cost:.2f}s\n")

# 2. 多线程执行
def run_thread():
    print("===== 2. 多线程执行 =====")
    start = datetime.now()
    threads = []
    for i in range(5):
        t = threading.Thread(target=simulate_infer_sync, args=(i,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    end = datetime.now()
    cost = (end - start).total_seconds()
    print(f"多线程总耗时：{cost:.2f}s\n")

# 3. 异步并发执行
async def run_async():
    print("===== 3. 异步并发执行 =====")
    start = datetime.now()
    tasks = [simulate_infer_async(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    for r in results:
        print(r)
    end = datetime.now()
    cost = (end - start).total_seconds()
    print(f"异步并发总耗时：{cost:.2f}s\n")

if __name__ == "__main__":
    run_serial()
    run_thread()
    asyncio.run(run_async())