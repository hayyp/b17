PROMPT_BOT = "gpt-3.5-turbo-0125"
REQUIREMENTS = [
    "openai==1.10.0",
    "modal==0.56.4687",
    "tiktoken==0.6.0"
]
SYSTEM_PROMPT = """

I am seeking professional assistance in translating a piece of content into English with the following requirements:

- Preferred writing style: Short and concise paragraphs, with a narrative tone that reads smoothly and sometimes even poetic like a story.
- Structural elements: Include chapter index and title where relevant, and chapter indices should all be Arabic numerals.
- Writing focus: Ensure the translation flows with a focus on rhythm and logic, maintaining a narrative style throughout, with a preference for literal translations of key descriptive terms.
- Transitional coherence: Craft smooth transitions between lines and paragraphs for seamless reading.
- Tense usage: Use past tense for narration, except for direct speech which should remain in the original tense.
- Sentence structure: Favor complete sentences that contribute to a narrative voice, and specifically emphasize physical descriptions when referring to characters.
- Fidelity to content: No changes to the original plot or content, but allow for adjustments in sentence structure to suit English narrative style, including a preference for direct and precise language that accurately reflects the source text's descriptions.
- Currency consistency: Convert all monetary amounts to dollars where necessary.
- Response format: Provide a direct translation without additional notes or clarifications, ensuring the text reads like an English-language story, with particular attention to the literal and descriptive aspects of character portrayals.

After reviewing these guidelines, please find the content for translation below. I trust that you will adhere to these specifications closely.\n

"""
SYSTEM_PROMPT_2 = """

Please take the following text and reformat it into shorter paragraphs for better readability. 
Ensure that the original content remains unchanged, and each paragraph should encapsulate a complete thought or theme. 
The breaks should occur at natural points in the narrative to maintain the flow of the message.\n

"""