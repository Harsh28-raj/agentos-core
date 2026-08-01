import os
import base64
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

@tool
def analyze_image(image_path: str, prompt: str = "Extract and summarize the text and visual content of this image.") -> str:
    """Useful to extract text, summarize or analyze visual content from an image file."""
    if not os.path.exists(image_path):
        return f"Error: File not found at {image_path}"
        
    try:
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Determine MIME type based on extension
        mime_type = "image/jpeg"
        if image_path.lower().endswith(".png"):
            mime_type = "image/png"
        elif image_path.lower().endswith(".webp"):
            mime_type = "image/webp"

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return "Error: GROQ_API_KEY environment variable is missing."

        vision_llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"), max_retries=2, temperature=0.2, timeout=60.0)
        
        msg = vision_llm.invoke(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                    ]
                }
            ]
        )
        return msg.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"
