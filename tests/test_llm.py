from loguru import logger
from openai import OpenAI
from vmc_client import VMC, SystemMessage, UserMessage

prompt = "hello"
parameters = {
    "temperature": 0.5,
    "top_p": 0.7,
    "max_tokens": 10,
    "presence_penalty": 0.3,
    "frequency_penalty": 0.5,
}
messages = [
    SystemMessage(content="you are a good assistant named Neptune."),
    UserMessage(content="who are you?"),
]


api_chat_models = []


def test_supported_models(client: VMC):
    global api_chat_models
    assert isinstance(client.supported_models, dict)
    api_chat_models = [
        k for k, v in client.supported_models.items() if "chat" in v.types and not v.is_local
    ]


def test_api_chat_models(client: VMC, oc: OpenAI):
    global api_chat_models

    for model in api_chat_models:
        print(model)
        response = client.generate(prompt, model, parameters=parameters)
        assert response.code == 200
        print(response.generated_text)

    for model in api_chat_models:
        print(model)
        for token in client.stream_chat(prompt, model, parameters=parameters):
            assert token.code == 200
            print(token.token.text, end="")
        print()

    parameters.pop("history", None)
    for model in api_chat_models:
        print(model)
        response = oc.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            **parameters,
        )
        assert len(response.choices) > 0
        print(response.choices[0].message.content)

    for model in api_chat_models:
        print(model)
        for token in oc.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            stream=True,
            **parameters,
        ):
            assert len(token.choices) > 0
            print(token.choices[0].delta.content, end="")
        print()


def test_tool_call(client: VMC):
    test_model = "gpt-4o"
    if test_model not in client.supported_models:
        logger.warning(f"{test_model} not supported")
        return
    tool_calls = [
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "计算器",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "表达式",
                        }
                    },
                    "required": ["expression"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "retrieve_from_knowledge_base",
                "description": "从知识库中检索信息，知识库内容为888空调的维修手册",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "需要检索的内容",
                        }
                    },
                    "required": ["query"],
                },
            },
        },
    ]

    msg = client.generate(
        [UserMessage(content="888^10的结果和777*15的结果哪个更大")],
        model=test_model,
        max_tokens=128,
        tools=tool_calls,
    )
    print(msg)
    assert len(msg.tool_calls) > 0

    messages = [{"role": "user", "content": "888^10的结果和777*15的结果哪个更大"}]
    messages.append(
        {
            "role": "assistant",
            "content": msg.generated_text,
            "tool_calls": [tc.dict() for tc in msg.tool_calls],
        }
    )
    for tool_call in msg.tool_calls:
        import random

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": f"{random.randint(1, 100)}",
            }
        )

    print(messages)

    msg = client.generate(messages, model=test_model, max_tokens=128, tools=tool_calls)

    print(msg)
