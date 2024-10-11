from escpos.printer import Network
import asyncio
from prisma import Prisma
from datetime import datetime, timedelta


async def print_orders(prisma, receipt):
    three_minutes_ago = datetime.utcnow() - timedelta(minutes=0)

    # Ensure the Prisma client is connected
    if not prisma.is_connected():
        await prisma.connect()

    # Fetch orders where printed is false
    orders = await prisma.order.find_many(
        where={
            'printed': False,
            "createdOn": {
                'lt': three_minutes_ago.isoformat() + "Z"
            }
        },
        include={
            "user": True,
            "table": True,
            'orderedMenus': {
                'include': {
                    'menuOrder': {
                        'include': {
                            'menu': True,
                        }
                    }
                }
            },
            'orderedDrinks': {
                'include': {
                    'drinkOrder': {
                        'include': {
                            'drink': True,
                        }
                    }
                }
            }
        }
    )
    try:
        for order in orders:
            adjusted_created_on = order.createdOn + timedelta(hours=2)
            formatted_time = adjusted_created_on.strftime("%H:%M")

            if len(order.orderedMenus.menuOrder) > 0:
                receipt.set(align='center')
                receipt.image("./logo.png")

                receipt.text(f"\nBestellung Nr {order.id}\n")
                receipt.text(f"Bedienung: {order.user.username}\n")
                receipt.text(f"Zeit: {formatted_time}")

                receipt.text(
                    f"\n\nTisch: {order.table.name}")
                if order.name:
                    receipt.text(f"\nfür {order.name}")

                receipt.ln(2)
                receipt.text("Menus:\n")
                totalPrice = 0
                for menuOrder in order.orderedMenus.menuOrder:
                    receipt.text(f"{menuOrder.amount} x ")
                    receipt.text(f"{menuOrder.menu.name}")
                    receipt.text(f" à CHF {menuOrder.menu.price}")
                    if menuOrder.amount > 1:
                        receipt.text(
                            f" / CHF {menuOrder.amount * menuOrder.menu.price}\n")
                    else:
                        receipt.text(f"\n")
                    totalPrice += menuOrder.menu.price*menuOrder.amount

                receipt.text(f"\nTotal: CHF {totalPrice}")

                receipt.cut()

            if len(order.orderedDrinks.drinkOrder) > 0:
                receipt.set(align='center')
                receipt.image("./logo.png")

                receipt.text(f"\nBestellung Nr {order.id}\n")
                receipt.text(f"Bedienung: {order.user.username}\n")
                receipt.text(f"Zeit: {formatted_time}")

                receipt.text(
                    f"\n\nTisch: {order.table.name}")
                if order.name:
                    receipt.text(f"\nfür {order.name}")

                totalPrice = 0
                receipt.ln(2)
                receipt.text("Getränke:\n")
                for drinkOrder in order.orderedDrinks.drinkOrder:
                    receipt.text(f"{drinkOrder.amount} x ")
                    receipt.text(f"{drinkOrder.drink.name}")
                    receipt.text(f" à CHF {drinkOrder.drink.price}")
                    if drinkOrder.amount > 1:
                        receipt.text(
                            f" / CHF {drinkOrder.amount * drinkOrder.drink.price}\n")
                    else:
                        receipt.text(f"\n")
                    totalPrice += drinkOrder.drink.price*drinkOrder.amount

                receipt.text(f"\nTotal: CHF {totalPrice}")

                receipt.cut()

            # Update the printed status to true
            await prisma.order.update(
                where={
                    'id': order.id
                },
                data={
                    'printed': True
                }
            )

    except Exception as e:
        print(e)

    await prisma.disconnect()


async def main() -> None:
    prisma = Prisma()
    await prisma.connect()
    receipt = Network("192.168.1.148", profile='TM-T20II')

    try:
        while True:
            await print_orders(prisma, receipt)
            await asyncio.sleep(5)
    finally:
        await prisma.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
