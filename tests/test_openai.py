import asyncio

from openai import AsyncOpenAI, OpenAI


async def test_openai():
    openai = OpenAI(base_url="http://localhost:8000/v1", api_key="sk_test_123")
    async_openai = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="sk_test_123")
    messages = [{"role": "user", "content": "hello"}]
    openai.chat.completions.create(messages=messages, model="glm-4-flash", max_tokens=100)
    print(
        await async_openai.chat.completions.create(
            messages=messages, model="glm-4-flash", max_tokens=100
        )
    )
    for t in openai.chat.completions.create(
        messages=messages, model="glm-4-flash", max_tokens=100, stream=True
    ):
        print(t)
    async for t in await async_openai.chat.completions.create(
        messages=messages, model="glm-4-flash", max_tokens=100, stream=True
    ):
        print(t)
    print(openai.embeddings.create(input="hello", model="text-embedding-3-small"))
    print(await async_openai.embeddings.create(input="hello", model="text-embedding-3-small"))
    # openai.rerank([["hello", "world"], ["hello", "nihao"]], model="lm")
    # async_openai.arerank([["hello", "world"], ["hello", "nihao"]], model="lm")


if __name__ == "__main__":
    asyncio.run(test_openai())
