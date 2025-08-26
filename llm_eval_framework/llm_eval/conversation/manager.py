"""
Conversation and multi-turn dialogue management for LLM evaluations.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from ..providers.base import BaseProvider, Message, ProviderResponse
from ..config.models import TestCase, Assertion


class ConversationTurn(BaseModel):
    """Represents a single turn in a conversation."""
    
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Dict[str, Any] = {}


class ConversationState(BaseModel):
    """Tracks the state of a conversation."""
    
    conversation_id: str
    turns: List[ConversationTurn] = []
    context: Dict[str, Any] = {}
    
    def add_turn(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a turn to the conversation."""
        turn = ConversationTurn(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.turns.append(turn)
    
    def get_messages(self) -> List[Message]:
        """Convert conversation turns to provider messages."""
        messages = []
        for turn in self.turns:
            message = Message(
                role=turn.role,
                content=turn.content
            )
            messages.append(message)
        return messages
    
    def get_last_assistant_response(self) -> Optional[str]:
        """Get the last assistant response."""
        for turn in reversed(self.turns):
            if turn.role == "assistant":
                return turn.content
        return None


class ConversationManager:
    """Manages multi-turn conversations and evaluations."""
    
    def __init__(self, providers: Dict[str, BaseProvider]):
        """Initialize conversation manager.
        
        Args:
            providers: Dictionary of available providers
        """
        self.providers = providers
        self.conversations: Dict[str, ConversationState] = {}
    
    async def run_conversation_test(
        self,
        test_config: Dict[str, Any],
        provider_id: str
    ) -> Dict[str, Any]:
        """Run a multi-turn conversation test.
        
        Args:
            test_config: Conversation test configuration
            provider_id: Provider to use for the conversation
            
        Returns:
            Conversation test results
        """
        if provider_id not in self.providers:
            raise ValueError(f"Provider {provider_id} not found")
        
        provider = self.providers[provider_id]
        conversation_id = test_config.get("conversation_id", f"conv_{id(test_config)}")
        
        # Initialize conversation
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationState(
                conversation_id=conversation_id
            )
        
        conversation = self.conversations[conversation_id]
        
        # Add system message if provided
        system_message = test_config.get("system")
        if system_message:
            conversation.add_turn("system", system_message)
        
        # Process conversation turns
        turns_config = test_config.get("turns", [])
        results = []
        
        for i, turn_config in enumerate(turns_config):
            turn_result = await self._process_conversation_turn(
                conversation, turn_config, provider, i
            )
            results.append(turn_result)
            
            # Stop if there was an error
            if not turn_result.get("success", True):
                break
        
        return {
            "conversation_id": conversation_id,
            "provider_id": provider_id,
            "turn_results": results,
            "final_conversation": conversation.dict(),
            "success": all(r.get("success", True) for r in results)
        }
    
    async def _process_conversation_turn(
        self,
        conversation: ConversationState,
        turn_config: Dict[str, Any],
        provider: BaseProvider,
        turn_index: int
    ) -> Dict[str, Any]:
        """Process a single conversation turn.
        
        Args:
            conversation: Current conversation state
            turn_config: Turn configuration
            provider: LLM provider
            turn_index: Index of this turn
            
        Returns:
            Turn processing result
        """
        try:
            # Get user message (with variable substitution)
            user_message = turn_config.get("user", turn_config.get("message"))
            if user_message:
                # Apply variable substitution
                user_message = self._apply_variables(
                    user_message, 
                    turn_config.get("vars", {}),
                    conversation.context
                )
                conversation.add_turn("user", user_message)
            
            # Generate assistant response
            messages = conversation.get_messages()
            provider_response = await provider.generate(messages)
            
            # Add assistant response to conversation
            conversation.add_turn(
                "assistant", 
                provider_response.content,
                {
                    "cost": provider_response.cost,
                    "latency": provider_response.latency,
                    "token_usage": provider_response.token_usage,
                }
            )
            
            # Update conversation context
            conversation.context.update({
                f"turn_{turn_index}_user": user_message,
                f"turn_{turn_index}_assistant": provider_response.content,
                "last_response": provider_response.content,
            })
            
            # Run turn-specific assertions
            assertion_results = []
            assertions = turn_config.get("assert", [])
            
            for assertion_config in assertions:
                assertion_result = await self._run_conversation_assertion(
                    assertion_config, 
                    conversation, 
                    provider_response
                )
                assertion_results.append(assertion_result)
            
            # Determine turn success
            turn_success = all(r.get("passed", False) for r in assertion_results)
            
            return {
                "turn_index": turn_index,
                "user_message": user_message,
                "assistant_response": provider_response.content,
                "cost": provider_response.cost,
                "latency": provider_response.latency,
                "assertion_results": assertion_results,
                "success": turn_success,
            }
            
        except Exception as e:
            return {
                "turn_index": turn_index,
                "success": False,
                "error": str(e),
            }
    
    async def _run_conversation_assertion(
        self,
        assertion_config: Dict[str, Any],
        conversation: ConversationState,
        provider_response: ProviderResponse
    ) -> Dict[str, Any]:
        """Run an assertion in the context of a conversation.
        
        Args:
            assertion_config: Assertion configuration
            conversation: Current conversation state
            provider_response: Latest provider response
            
        Returns:
            Assertion result
        """
        from ..evaluation.assertions.registry import assertion_registry
        
        # Create assertion object
        assertion = Assertion(**assertion_config)
        
        # Get assertion function
        assertion_func = assertion_registry.get_assertion(assertion.type)
        if not assertion_func:
            return {
                "type": assertion.type,
                "passed": False,
                "error": f"Unknown assertion type: {assertion.type}"
            }
        
        # For conversation-aware assertions, we might need special handling
        response_text = provider_response.content
        
        # Special handling for conversation-specific assertions
        if assertion.type == "conversation-length":
            # Check conversation length
            expected_length = assertion.value
            actual_length = len([t for t in conversation.turns if t.role in ["user", "assistant"]])
            return {
                "type": assertion.type,
                "passed": actual_length == expected_length,
                "message": f"Expected {expected_length} turns, got {actual_length}",
                "metadata": {"expected": expected_length, "actual": actual_length}
            }
        
        elif assertion.type == "conversation-context":
            # Check if response references earlier conversation
            context_keywords = assertion.value if isinstance(assertion.value, list) else [assertion.value]
            
            # Check if any context keywords appear in the response
            contains_context = any(
                keyword.lower() in response_text.lower() 
                for keyword in context_keywords
            )
            
            return {
                "type": assertion.type,
                "passed": contains_context,
                "message": f"Response {'does' if contains_context else 'does not'} reference conversation context",
                "metadata": {"keywords": context_keywords}
            }
        
        else:
            # Use standard assertion
            return await assertion_func(assertion, response_text, provider_response)
    
    def _apply_variables(
        self, 
        template: str, 
        turn_vars: Dict[str, Any],
        conversation_context: Dict[str, Any]
    ) -> str:
        """Apply variable substitution to a message template.
        
        Args:
            template: Message template
            turn_vars: Variables specific to this turn
            conversation_context: Variables from conversation history
            
        Returns:
            Rendered message
        """
        from jinja2 import Template
        
        # Combine variables (turn vars take precedence)
        variables = {**conversation_context, **turn_vars}
        
        jinja_template = Template(template)
        return jinja_template.render(**variables)
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get a conversation by ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation state or None if not found
        """
        return self.conversations.get(conversation_id)
    
    def clear_conversation(self, conversation_id: str):
        """Clear a conversation.
        
        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def clear_all_conversations(self):
        """Clear all conversations."""
        self.conversations.clear()
    
    def export_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Export conversation to dictionary format.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation data or None if not found
        """
        conversation = self.conversations.get(conversation_id)
        if conversation:
            return conversation.dict()
        return None