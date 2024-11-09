import asyncio

from vmc_client import VMC

vmc = VMC("http://localhost:8000")


async def test():
    print(vmc.generate("hello who are you?", model="glm-4-flash", max_tokens=100))
    print(await vmc.agenerate("hello who are you?", model="glm-4-flash", max_tokens=100))
    print(vmc.tokenize("who are you", model="gpt-4o"))
    print(await vmc.atokenize("who are you", model="gpt-4o"))
    for t in vmc.stream("What's the date today?", model="glm-4-flash", max_tokens=100):
        print(t.token, end="")
    async for t in vmc.astream("What's the date today?", model="glm-4-flash", max_tokens=100):
        print(t.token, end="")
    print(vmc.embedding("hello", model="text-embedding-3-small"))
    print(await vmc.aembedding("hello", model="text-embedding-3-small"))
    # vmc.rerank([["hello", "world"], ["hello", "nihao"]], model="lm")
    # await vmc.arerank([["hello", "world"], ["hello", "nihao"]], model="lm")


if __name__ == "__main__":
    asyncio.run(test())
