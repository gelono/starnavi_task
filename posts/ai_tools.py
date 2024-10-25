import os
import time

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("API_GEMINI"))
model = genai.GenerativeModel("gemini-1.5-flash")

def moderate_content_with_ai(text):
    """
    The function checks the text for inappropriate content.
    :param text: str
    :return: Bool, str
    """
    response = None
    safety_categories = {
        7: "HARM_CATEGORY_HARASSMENT",
        8: "HARM_CATEGORY_HATE_SPEECH",
        9: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        10: "HARM_CATEGORY_DANGEROUS_CONTENT"
    }
    text_proc = f'Please check the following text for obscene language and insults: "{text}"'

    count = 0
    while count <= 3 and not response:
        count += 1
        try:
            response = model.generate_content(text_proc)
        except Exception as e:  # I don't know what type of error can be received from the AI-service
            print("Error while AI text proceeds: ", str(e))
            time.sleep(5)

    if not response:
        print("Content has been blocked because of AI-moderation is not available")
        return True, "Error while AI text proceeds"
    else:
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                for rating in candidate.safety_ratings:
                    category_name = safety_categories.get(rating.category, "UNKNOWN_CATEGORY")
                    if rating.probability >= 2:
                        return True, category_name

                return False, ""
        else:
            return False, ""



def generate_relevant_reply(post, comment):
    """
    The function generates a relevant response to a comment using AI
    :param post: Post instance
    :param comment: Comment instance
    :return: str
    """

    prompt = f"Generate a relevant response to this comment: '{comment.content}' based on the post: '{post.content}'"
    reply = model.generate_content(prompt)

    return reply.text
