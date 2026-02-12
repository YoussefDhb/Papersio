"""LLM Provider Abstraction Layer"""

import os
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate text from a prompt"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used"""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini models (google.genai SDK)"""
    
    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        """
        Initialize Gemini provider
        
        Args:
            model: Model name (e.g., 'gemini-2.5-flash', 'gemini-2.5-pro')
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError("Google GenAI library not installed. Run: pip install google-genai")
        
        self.model_name = model
        if self.model_name.startswith("models/"):
            self.model_name = self.model_name.replace("models/", "", 1)

        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables or parameters")
        
        self.client = genai.Client(api_key=self.api_key)
        self.types = types
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate text using Gemini API"""
        try:
            config = {"temperature": temperature}
            if max_tokens:
                config["max_output_tokens"] = max_tokens

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.types.GenerateContentConfig(**config)
            )

            if hasattr(response, "text") and response.text:
                return response.text

            raise Exception("Empty response from Gemini API")
        
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def get_model_name(self) -> str:
        return f"Gemini/{self.model_name}"


class ModelFactory:
    """Factory for creating LLM providers"""
    
    SUPPORTED_PROVIDERS = {
        'gemini': GeminiProvider,
    }
    
    MODEL_ALIASES = {
        'gemini-flash': ('gemini', 'gemini-2.5-flash'),
        'gemini-pro': ('gemini', 'gemini-2.5-pro'),
        'gemini-2.5-flash': ('gemini', 'gemini-2.5-flash'),
        'gemini-2.5-pro': ('gemini', 'gemini-2.5-pro'),
        'gemini-2.0-flash': ('gemini', 'gemini-2.0-flash'),
        'gemini-2.0-pro': ('gemini', 'gemini-2.0-pro'),
        'gemini-1.5-flash': ('gemini', 'gemini-1.5-flash'),
        'gemini-1.5-pro': ('gemini', 'gemini-1.5-pro'),
    }
    
    @classmethod
    def create(cls, provider: str = None, model: str = None, **kwargs) -> LLMProvider:
        """
        Create an LLM provider instance
        
        Args:
            provider: Provider name ('gemini')
            model: Model name or alias
            **kwargs: Additional provider-specific arguments
        
        Returns:
            LLMProvider instance
        
        Examples:
            factory.create()  # Uses DEFAULT_PROVIDER env var
        """
        
        if not provider and not model:
            provider = os.getenv('DEFAULT_PROVIDER', 'gemini')
            model = os.getenv('DEFAULT_MODEL')
        
        if model and model in cls.MODEL_ALIASES:
            provider, model = cls.MODEL_ALIASES[model]
        
        if not provider:
            raise ValueError("Provider must be specified or set DEFAULT_PROVIDER environment variable")
        
        if provider not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {', '.join(cls.SUPPORTED_PROVIDERS.keys())}"
            )
        
        provider_class = cls.SUPPORTED_PROVIDERS[provider]
        
        if model:
            kwargs['model'] = model
        
        return provider_class(**kwargs)
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> LLMProvider:
        """
        Create provider from configuration dictionary
        
        Args:
            config: Dict with 'provider', 'model', and optional parameters
        
        Example:
            config = {
                'provider': 'gemini',
                'model': 'gemini-2.5-flash',
                'api_key': 'your_key'
            }
        """
        provider = config.pop('provider', None)
        model = config.pop('model', None)
        return cls.create(provider=provider, model=model, **config)
