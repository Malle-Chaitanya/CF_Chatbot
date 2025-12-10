"""
LLM Factory - Create LLM instances based on provider configuration
Supports OpenAI (GPT-4o-mini) and Google Gemini (2.5 Flash Lite)
"""

from config import LLM_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY
from typing import Optional


def get_llm(model_name: Optional[str] = None, temperature: float = 0.7, streaming: bool = False, max_tokens: Optional[int] = None):
    """
    Factory function to create an LLM instance based on LLM_PROVIDER configuration.
    
    Args:
        model_name: Optional model name override. If not provided, uses defaults based on provider.
        temperature: Temperature for response generation (0.0-1.0)
        streaming: Whether to enable streaming responses
        max_tokens: Maximum tokens in response
        
    Returns:
        LLM instance (ChatOpenAI or ChatGoogleGenerativeAI)
        
    Raises:
        ValueError: If provider is invalid or API key is missing
    """
    
    if LLM_PROVIDER == "openai":
        return _get_openai_llm(model_name, temperature, streaming, max_tokens)
    elif LLM_PROVIDER == "gemini":
        return _get_gemini_llm(model_name, temperature, streaming, max_tokens)
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


def _get_openai_llm(model_name: Optional[str] = None, temperature: float = 0.7, streaming: bool = False, max_tokens: Optional[int] = None):
    """Create OpenAI ChatGPT LLM instance"""
    from langchain_openai import ChatOpenAI
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set. Cannot initialize OpenAI LLM.")
    
    # Default to gpt-4o-mini if no model specified
    if model_name is None:
        model_name = "gpt-4o-mini"
    
    kwargs = {
        "model_name": model_name,
        "temperature": temperature,
        "api_key": OPENAI_API_KEY
    }
    
    if streaming:
        kwargs["streaming"] = True
    
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    
    return ChatOpenAI(**kwargs)


def _get_gemini_llm(model_name: Optional[str] = None, temperature: float = 0.7, streaming: bool = False, max_tokens: Optional[int] = None):
    """Create Google Gemini LLM instance (using 2.5 Flash Lite by default)"""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Cannot initialize Gemini LLM.")
    
    # Default to gemini-2.5-flash-lite if no model specified
    if model_name is None:
        model_name = "gemini-2.5-flash-lite"
    
    kwargs = {
        "model": model_name,
        "temperature": temperature,
        "api_key": GEMINI_API_KEY
    }
    
    # Note: Gemini streaming is handled differently than OpenAI
    # For now, we'll set streaming in the invoke call if needed
    # But we can still set it here for some implementations
    if streaming:
        kwargs["streaming"] = True
    
    if max_tokens is not None:
        kwargs["max_output_tokens"] = max_tokens
    
    return ChatGoogleGenerativeAI(**kwargs)


def get_llm_provider_info() -> dict:
    """Get current LLM provider information for logging/debugging"""
    return {
        "provider": LLM_PROVIDER,
        "model": "gpt-4o-mini" if LLM_PROVIDER == "openai" else "gemini-2.5-flash-lite",
        "has_openai_key": bool(OPENAI_API_KEY),
        "has_gemini_key": bool(GEMINI_API_KEY)
    }

