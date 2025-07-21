import google.generativeai as genai
import os

# --- Configure API Key (Choose one method from previous instructions) ---
# Option 1: Using Environment Variable (Recommended)
# export GOOGLE_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY" before running the script
#
# Option 2: Hardcoding API key (For quick testing ONLY, not recommended for production)
genai.configure(api_key="AIzaSyDqVlOh_Ot5sjPDpWjLJwHt6t4bOGKOilk") # Replace with your actual key

try:
    # --- First, let's list the available models ---
    print("Listing available Gemini models:")
    for m in genai.list_models():
        # Only show models that support text generation, which is what we need for chat
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name} (DisplayName: {m.display_name})")
            # print(f"  Supported methods: {m.supported_generation_methods}") # Uncomment for more details

    print("\n--- Attempting to use a model for content generation ---")

    # --- IMPORTANT: Replace 'gemini-pro' with one of the *actual* model names from the list above ---
    # Look for models like 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash', etc.
    # The exact name might vary. Choose one that supports 'generateContent'.
    # For general text generation, 'gemini-1.5-flash' or 'gemini-1.5-pro' are common choices.
    # If those don't work, try others from the list.
    
    # Example: If 'gemini-1.5-flash' appears in your list, use it:
    model_to_use = 'gemini-1.5-flash' 
    # Or, if 'gemini-1.5-pro' appears:
    # model_to_use = 'gemini-1.5-pro'
    # Or 'gemini-2.5-flash' if you see it and it's available

    model = genai.GenerativeModel(model_to_use)

    # Make your request
    prompt = "What are the key ingredients in Hyderabadi biryani?"
    print(f"Sending prompt to Gemini using model '{model_to_use}': '{prompt}'")
    response = model.generate_content(prompt)

    # Print the response
    print("\nGemini's Response:")
    print(response.text)

except Exception as e:
    print(f"\nAn error occurred: {e}")
    print("Please check the model name you are using. It must be one from the list of available models.")
    print("Also ensure your API key is correctly configured.")