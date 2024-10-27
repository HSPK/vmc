from openai import OpenAI
from vmcc import VMC


def test_bge_m3(client: VMC, oc: OpenAI):
    print("bge-m3")
    client.embedding("hello", "bge-m3")
    oc.embeddings.create(input=["hello", "world"], model="bge-m3")
    client.embedding("hello", "bge-m3", parameters={"return_sparse": True})


def test_m3e_large(client: VMC, oc: OpenAI):
    print("bge-m3")
    client.embedding("hello", "m3e-large")
    oc.embeddings.create(input=["hello", "world"], model="bge-m3")


def test_reranker(client: VMC):
    client.rerank("hello", ["hello", "world"], model="bge-reranker-v2-m3")
    client.rerank("hello", ["hello", "world"], model="bge-reranker-base")
