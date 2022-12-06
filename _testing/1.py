import asyncio
import websockets


async def test():
    async with websockets.connect('ws://localhost:9001') as ws:
        print('Sending Message...')
        await ws.send('Sosi')
        print('Message sent. Waiting Response...')
        response = await ws.recv()
        print('Response: ' + response)

if __name__ == '__main__':
    coro = test()
    asyncio.run(coro)