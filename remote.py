import os
import modal
import uuid
import config
import io
import re
import tiktoken
from openai import OpenAI
from typing import List, Optional, Union, Tuple


app = modal.App("pr1")
id_prompt_dict = modal.Dict.from_name("pr_prompt_dict", create_if_missing=True)
image = modal.Image.debian_slim()\
    .pip_install("openai", "modal", "tiktoken")\
    .run_commands(
        "python -c \"import tiktoken; tiktoken.encoding_for_model('gpt-3.5-turbo-0125')\""
)
volume = modal.NetworkFileSystem.from_name("job_storage", create_if_missing=True)

def count_paragraphs(text: str) -> int:
    paragraphs = re.split(r'\n+', text.strip())
    return len(paragraphs)
    
def normalize_linebreak(text: str) -> str:
    lines = text.splitlines()
    normalized_text = ''
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line:
            normalized_text += stripped_line + '\n'
            if i < len(lines) - 1 and lines[i + 1].strip():
                normalized_text += '\n'
        elif normalized_text and not normalized_text.endswith('\n\n'):
            normalized_text += '\n'
    return normalized_text
    
    
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("pr1")],
    timeout=600
)
def last_shot(chapter_w_prompt: Tuple[str, Optional[str]]) -> str:
    try:
        print("LAST SHOT MODE IS ON")
        print("LAST SHOT MODE IS ON")       
        chapters_w_prompt = [chapter_w_prompt] * 10
        translations = client_msg_wrapper.map(chapters_w_prompt)
        
        current_longest_version = b""
        current_record_len = 0
        
        for index, translation in enumerate(translations, start=1):
            current_len = len(translation) 
            print(f"counting len of ver {index}")
            if current_len > current_record_len:
                current_record_len = current_len
                current_longest_version = translation
        
        return current_longest_version.decode('utf-8')
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "Stopped by error"
        
        
        
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("pr1")],
    timeout=600
)
def client_msg_wrapper(
    chapter_w_prompt: Tuple[str, Optional[str]]
) -> Optional[bytes]:
    try:
        chapter, prompt = chapter_w_prompt
        
        client = OpenAI(
            api_key=os.environ["ds"],
            base_url=f"{os.environ['url_ds']}"
        )
        
        translation_prompt = prompt if prompt is not None else config.SYSTEM_PROMPT
        
        completion = client.chat.completions.create(
            model=config.PROMPT_BOT,
            messages=[{
                "role": "user",
                "content": translation_prompt + '\n' + chapter
            }]
        )
        
        tries = 1
        retry_lim = 3
        while completion.choices[0].message.content is None and tries < retry_lim:
            print("invalid response from openai server...")
            tries = tries + 1
            completion = client.chat.completions.create(
                    model=config.PROMPT_BOT,
                    messages=[{
                            "role": "user",
                            "content": translation_prompt+ '\n' + chapter
                    }]
            ) 

        if completion.choices[0].message.content is not None:
               res_text: str = completion.choices[0].message.content
        else:
            print("invalid response after retries...")
            return None

        # print(f"first prompt {translation_prompt}\n{chapter}\n")
        # print(f"first completion {completion}\n")

        if count_paragraphs(res_text) < 6 and count_paragraphs(res_text) > 2:
            completion = client.chat.completions.create(
                model=config.PROMPT_BOT,
                messages=[{
                    "role": "user",
                    "content": config.SYSTEM_PROMPT_2 + res_text
                }]
            )   
            print(f"second prompt [SPLIT]\n")
            print(f"second completion [SPLIT] {completion}\n")

        if completion.choices[0].message.content is not None:
            res_text = normalize_linebreak(completion.choices[0].message.content)
        else:
            return None

        return res_text.encode('utf-8')
    except Exception as e:
        print(f"An error occurred in client_msg_wrapper: {e}")
        error_msg = "[ Skipped due to an error ]"
        return error_msg.encode("utf-8")
        
        
@app.function(
    image=image,
    timeout=600
)
def translate(content: str, prompt: Optional[str] = None) -> List[Optional[Union[str, None]]]:
    try:
        volume = modal.NetworkFileSystem.lookup("job_storage")
        job_id: uuid.UUID = uuid.uuid4()
        id_prompt_dict.put(str(job_id), prompt)
        output: List[Optional[Union[str, None]]] = []
        output.append(str(job_id))
        chapters: List[str] = content.split('#####')[1:]
        chapters = [chapter.strip() for chapter in chapters]

        
        for index, chapter in enumerate(chapters, start=1):
            file_name = f"{job_id}_{index}"
            chapter_obj = io.BytesIO(chapter.encode('utf-8'))
            volume.write_file(f"/src/{file_name}", chapter_obj)
        
        chapters_w_prompt: List[Tuple[str, Optional[str]]] = [
            (chapter, prompt) for chapter in chapters
        ]
        
        # translate
        translations = client_msg_wrapper.map(chapters_w_prompt)
        short_chapters: List[Tuple[str, Optional[str]]] = []
        short_chapter_indexes: List[int] = []
        for index, translation_res in enumerate(translations, start=1):
            file_name = f"{job_id}_{index}"
            if not isinstance(translation_res, bytes):
                raise TypeError(f"Expected bytes, got {type(translation_res)}")
            volume.write_file(f"/res/{file_name}", io.BytesIO(translation_res))

            translation_text: str = translation_res.decode('utf-8')

            enc = tiktoken.encoding_for_model("gpt-3.5-turbo-0125")
            encoded_translation =enc.encode(translation_text)
            encoded_source = enc.encode(chapters[index-1])

            if len(encoded_translation) < 0.5 * len(encoded_source):
                print(f"LAST SHOT MODE IS STARTING: translation token {len(encoded_translation)}")
                print(f"LAST SHOT MODE IS STARTING: source_token {len(encoded_source)}")
                short_chapters.append((chapters[index-1], prompt))
                short_chapter_indexes.append(index)
                output.append(None)
            else:
                print("translation size test passed")
                print(f"translation token size: {len(encoded_translation)}")
                print(f"source token size: {len(encoded_source)}")
                output.append(translation_text)


        if short_chapters:
            print(f"LAST SHOT MODE IS ON")
            new_translations = last_shot.map(short_chapters)
            for index, translation in enumerate(new_translations, start=0):
                chapter_index = short_chapter_indexes[index]
                output[chapter_index] = translation
        
    except FileNotFoundError as fnf_error:
        print(f"Error: The file {file_name} was not found: {fnf_error}")
    except Exception as e:
        print(f"An error occurred in translate: {e}")
    return output
        
        
@app.function(
    image=image
)
def redo_translate(prev_id: str, indexes: List[int]):
    try:
        volume = modal.NetworkFileSystem.lookup("job_storage")
        job_id: uuid.UUID = uuid.uuid4()
        chapters = []
        output: List[Optional[Union[str, None]]] = []
        output.append(str(job_id))
        for index in indexes:
            file = volume.read_file(f"/src/{prev_id}_{index}")
            file_obj = b''.join(file)
            file_content = file_obj.decode('utf-8')
            chapters.append(file_content)
        prompt = id_prompt_dict.get(prev_id)
        
        if prompt is not None:
            print("custom prompt retrieved...")

        chapters_w_prompt: List[Tuple[str, Optional[str]]] = [
            # should be able to fetch old prompt
            (chapter, prompt) for chapter in chapters
        ]

        # currently redone files will be re-arranged
        translations = client_msg_wrapper.map(chapters_w_prompt)
        short_chapters: List[Tuple[str, Optional[str]]] = []
        short_chapter_indexes: List[int] = []
        for index, translation_res in enumerate(translations, start=1):
            file_name = f"{job_id}_{index}"
            if not isinstance(translation_res, bytes):
                raise TypeError(f"Expected bytes, got {type(translation_res)}")
            volume.write_file(f"/res/{file_name}", io.BytesIO(translation_res))

            translation_text: str = translation_res.decode('utf-8')
            enc = tiktoken.encoding_for_model("gpt-3.5-turbo-0125")
            encoded_translation =enc.encode(translation_text)
            encoded_source = enc.encode(chapters[index-1])
            if len(encoded_translation) < 0.5 * len(encoded_source):
                print(f"LAST SHOT MODE IS STARTING: translation token {len(encoded_translation)}")
                print(f"LAST SHOT MODE IS STARTING: source_token {len(encoded_source)}")
                short_chapters.append((chapters[index-1], prompt))
                short_chapter_indexes.append(index)
                output.append(None)

            else:
                print("translation size test passed")
                print(f"translation token size: {len(encoded_translation)}")
                print(f"source token size: {len(encoded_source)}")
                output.append(translation_text)

        if short_chapters:
            print(f"LAST SHOT MODE IS ON")
            new_translations = last_shot.map(short_chapters)
            for index, translation in enumerate(new_translations, start=0):
                chapter_index = short_chapter_indexes[index]
                output[chapter_index] = translation
        
    except FileNotFoundError as fnf_error:
        print(f"Error: The file {file_name} was not found: {fnf_error}")
    except Exception as e:
        print(f"An error occurred in translate: {e}")
    return output
        
        

    
