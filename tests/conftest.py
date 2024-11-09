import os

import openai
import pytest
from dotenv import find_dotenv, load_dotenv
from vmc_client import VMC

load_dotenv(find_dotenv())

PORT = os.getenv("TEST_PORT", 5678)


@pytest.fixture
def client():
    client = VMC()
    return client


@pytest.fixture
def oc():
    oc = openai.Client()
    return oc
