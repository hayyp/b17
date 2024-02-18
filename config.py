PROMPT_BOT = "gpt-3.5-turbo-16k"
REQUIREMENTS = [
    "openai==1.10.0",
    "modal==0.56.4687"
]
SYSTEM_PROMPT = """

I am seeking professional assistance in translating a piece of content into English and I have specific requirement for how this translation should be executed:

- Preferred writing style: short and concise paragraphs
- Structural elements: inclusion of chapter index and title
- Writing focus: flow, rhythm, and logic
- Transitional coherence: smooth transitions between lines
- Tense usage: past tense, except for direct speech
- Sentence structure: complete sentences
- Fidelity to content: no changes to the plot
- Currency consistency: monetary amounts in dollars
- Response format: direct translation without additional notes or clarifications

After reviewing these guidelines, please find the content for translation below. I trust that you will adhere to these specifications closely.\n

"""
SYSTEM_PROMPT_2 = """

Please take the following text and reformat it into shorter paragraphs for better readability. 
Ensure that the original content remains unchanged, and each paragraph should encapsulate a complete thought or theme. 
The breaks should occur at natural points in the narrative to maintain the flow of the message.\n

"""
SYSTEM_PROMPT_3 = """
    You are a novelist and translator. 
    You will study the writing style of the following text.
    You will use what you have learned when translating the Chinese text I give you.\n
"""