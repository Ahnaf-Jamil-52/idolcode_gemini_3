"""
Gemini Integration Usage Examples

This file demonstrates how to use the enhanced coach-engine with Gemini AI.
"""

import os
from coach_engine import FusionEngine, ResponseSelector, GeminiCoachAnalyzer

def basic_gemini_setup():
    """Basic setup with Gemini API support."""
    
    # Set API key (or set GEMINI_API_KEY environment variable)
    api_key = os.getenv('GEMINI_API_KEY') or "your-api-key-here"
    
    # Initialize with Gemini support
    engine = FusionEngine(use_gemini=True, gemini_api_key=api_key)
    response_selector = ResponseSelector(use_gemini=True, gemini_api_key=api_key)
    
    return engine, response_selector

def demonstrate_enhanced_analysis():
    """Show how Gemini enhances psychological analysis."""
    
    engine, response_selector = basic_gemini_setup()
    engine.start_session("user123", "session_1")
    
    # Simulate concerning behavior + masked text
    engine.process_event("wrong_answer")
    engine.process_event("wrong_answer") 
    engine.process_event("wrong_answer")
    engine.process_event("ghost_race_result", {"won": False})
    engine.process_event("ghost_race_result", {"won": False})
    
    # User says they're fine but behavior suggests otherwise
    sentiment = engine.process_message("I'm fine, just need to focus more")
    
    # Gemini will detect the masking behavior
    fusion_result = engine.analyze()
    
    print("=== Enhanced Analysis Results ===")
    print(f"Composite score: {fusion_result.composite_score:.3f}")
    print(f"Alignment: {fusion_result.alignment.value}")
    print(f"Gemini insights available: {hasattr(fusion_result, 'gemini_insights')}")
    
    # Generate personalized response
    response = response_selector.generate_response(fusion_result)
    if response:
        print(f"Coach response: {response.message}")
        print(f"Strategy: {response.strategy.value}")

def demonstrate_caching():
    """Show how response caching works."""
    
    analyzer = GeminiCoachAnalyzer(use_cache=True) 
    
    if not analyzer.enabled:
        print("Gemini not enabled - set GEMINI_API_KEY environment variable")
        return
    
    # Same analysis will be cached
    context = {
        'burnout_score': 0.7,
        'recent_signals': ['ghost_loss_streak', 'rapid_wa_burst'],
        'emotional_indicators': ['frustration']
    }
    
    # First call - hits API
    result1 = analyzer.analyze_burnout_context(
        chat_message="This is impossible, I keep failing",
        burnout_score=0.7,
        recent_signals=['ghost_loss_streak'],
        session_context={'session_minutes': 45}
    )
    
    # Second identical call - uses cache
    result2 = analyzer.analyze_burnout_context(
        chat_message="This is impossible, I keep failing", 
        burnout_score=0.7,
        recent_signals=['ghost_loss_streak'],
        session_context={'session_minutes': 45}
    )
    
    print("=== Caching Demo ===")
    print(f"First result: {result1}")
    print(f"Second result identical: {result1 == result2}")

if __name__ == "__main__":
    print("Gemini Integration Examples")
    print("=" * 40)
    
    # Check if API key is available
    if not os.getenv('GEMINI_API_KEY'):
        print("Set GEMINI_API_KEY environment variable to run examples")
        print("export GEMINI_API_KEY='your-api-key'")
    else:
        demonstrate_enhanced_analysis()
        print() 
        demonstrate_caching()