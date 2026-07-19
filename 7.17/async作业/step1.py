import asyncio
import time as t

async def greet(name, delay):
  await asyncio.sleep(delay)
  print(f'Hello, {name}!')

async def main():
  start = t.time()
  await asyncio.gather(greet('Alice', 1), 
                 greet('Bob', 2), 
                 greet('Charlie', 3))  # 并发执行
  end = t.time()
  print(f'Execution time: {end - start} seconds')

if __name__ == '__main__':
  asyncio.run(main())
