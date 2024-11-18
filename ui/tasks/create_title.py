from ragkit.agent import PromptAgent, PromptAgentState

from ui.db import db


class CreateTitle(PromptAgent[PromptAgentState]):
    """总结对话形成一个简短的标题
    ## 对话内容
    {question}
    ## 标题"""


async def task_create_title(question: str, conv_id: str):
    res = await CreateTitle(llm_model="glm-4-flash")({"question": question})
    await db.rename_conv(conv_id, res["response"].strip('"'))


if __name__ == "__main__":
    import asyncio

    async def main():
        result = await task_create_title("9.23 lot数量多少", "123")
        print(result)

    asyncio.run(main())
