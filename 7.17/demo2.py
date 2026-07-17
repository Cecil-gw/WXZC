
import asyncio

async def get_user():

    await asyncio.sleep(3)

    return "用户信息"



async def get_order():

    await asyncio.sleep(5)

    return "订单信息"



user = asyncio.run(get_user())

order = asyncio.run(get_order())

async def main():

    user, order = await asyncio.gather(
        get_user(),
        get_order()
    )

    print(user, order)



asyncio.run(main())