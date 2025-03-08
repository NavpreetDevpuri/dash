import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel



class LLMManager:
    """
    A manager class for handling different LLM providers and models.
    Provides a centralized way to create and configure LLM instances.
    """
    
    @staticmethod
    def get_openai_model(
        model_name: str = "gpt-4o",
        temperature: float = 0,
        **kwargs: Any
    ) -> ChatOpenAI:
        """
        Create and return an OpenAI chat model instance.
        
        Args:
            model_name: The name of the OpenAI model (default: "gpt-4o")
            temperature: The temperature setting for generation (default: 0)
            **kwargs: Additional parameters to pass to the ChatOpenAI constructor
            
        Returns:
            A configured ChatOpenAI instance
        """
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            **kwargs
        )
    
    @staticmethod
    def get_anthropic_model(
        model_name: str = "claude-3-opus-20240229",
        temperature: float = 0,
        **kwargs: Any
    ) -> ChatAnthropic:
        """
        Create and return an Anthropic Claude model instance.
        
        Args:
            model_name: The name of the Anthropic model (default: "claude-3-opus-20240229")
            temperature: The temperature setting for generation (default: 0)
            **kwargs: Additional parameters to pass to the ChatAnthropic constructor
            
        Returns:
            A configured ChatAnthropic instance
        """
        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            **kwargs
        )
    
    @staticmethod
    def get_gemini_model(
        model_name: str = "gemini-pro",
        temperature: float = 0,
        **kwargs: Any
    ) -> ChatGoogleGenerativeAI:
        """
        Create and return a Google Gemini model instance.
        
        Args:
            model_name: The name of the Gemini model (default: "gemini-pro")
            temperature: The temperature setting for generation (default: 0)
            **kwargs: Additional parameters to pass to the ChatGoogleGenerativeAI constructor
            
        Returns:
            A configured ChatGoogleGenerativeAI instance
        """
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            **kwargs
        )
    
    @classmethod
    def get_model(
        cls,
        provider: str,
        model_name: Optional[str] = None,
        temperature: float = 0,
        **kwargs: Any
    ) -> BaseChatModel:
        """
        Factory method to get an LLM instance based on provider.
        
        Args:
            provider: The LLM provider ("openai", "anthropic", "google")
            model_name: The specific model name (if None, uses provider default)
            temperature: The temperature setting for generation (default: 0)
            **kwargs: Additional parameters to pass to the model constructor
            
        Returns:
            A configured LLM instance
            
        Raises:
            ValueError: If an unsupported provider is specified
        """
        provider = provider.lower()
        
        if provider == "openai":
            model_name = model_name or "gpt-4o"
            return cls.get_openai_model(model_name, temperature, **kwargs)
        
        elif provider == "anthropic":
            model_name = model_name or "claude-3-opus-20240229"
            return cls.get_anthropic_model(model_name, temperature, **kwargs)
        
        elif provider == "google":
            model_name = model_name or "gemini-pro"
            return cls.get_gemini_model(model_name, temperature, **kwargs)
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
