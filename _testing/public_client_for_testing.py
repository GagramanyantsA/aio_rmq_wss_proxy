import asyncio
import json
import websockets


async def send_message(ws: websockets.WebSocketCommonProtocol, event: str, room: str):
    message = json.dumps({
        'event': event,
        'room': room
    })

    print(f'Sending Message... {message}')

    await ws.send(message)

    print('Message sent. Waiting Response...')

    response = await ws.recv()

    print(f'Response: {response}')


async def receive(ws: websockets.WebSocketCommonProtocol):
    print('Waiting for test message from RabbitMQ...')

    response = await ws.recv()

    print(f'Response: {response}')


async def test():
    async with websockets.connect('ws://localhost:9001') as ws:

        for i in range(1, 5):
            await send_message(ws, 'subscribe', f'public room {i}')
            await asyncio.sleep(1)

        await receive(ws)

        for i in range(1, 5):
            await send_message(ws, 'unsubscribe', f'public room {i}')
            await asyncio.sleep(1)


if __name__ == '__main__':
    coro = test()
    asyncio.run(coro)
