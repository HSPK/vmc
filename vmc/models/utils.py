from vmc.types._types import NOT_GIVEN
from vmc.types.generation import GenerationCost
from vmc.types.pricing import Pricing


def compute_cost(pricing: Pricing, input_tokens: int, output_tokens: int) -> GenerationCost:
    if not pricing:
        return None
    prompt_cost = pricing.input * input_tokens
    generated_cost = pricing.output * output_tokens
    total_cost = prompt_cost + generated_cost
    return GenerationCost(
        currency=pricing.currency,
        multiplier=pricing.multiplier,
        prompt_tokens=input_tokens,
        prompt_cost=prompt_cost,
        generated_tokens=output_tokens,
        generated_cost=generated_cost,
        total_cost=total_cost,
        total_tokens=input_tokens + output_tokens,
    )
    
def filter_notgiven(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not NOT_GIVEN}

