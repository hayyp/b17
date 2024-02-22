import os
import modal
import uuid
import config
import io
import re
from openai import OpenAI
from typing import List, Optional, Union, Tuple

stub = modal.Stub("bot17")
image = modal.Image.debian_slim().pip_install("openai", "modal")
volume = modal.NetworkFileSystem.persisted("job_storage")

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

@stub.function(
    image=image,
    secrets=[modal.Secret.from_name("b17")]
)
def client_msg_wrapper(
    chapter_w_prompt: Tuple[str, Optional[str]]
) -> Optional[bytes]:
    try:
        chapter, prompt = chapter_w_prompt
        
        client = OpenAI(
            api_key=os.environ["b17_openai_token"],
            base_url=f"https://{os.environ['b17_mirror_url']}/v1"
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
                tries = tries + 1
                completion = client.chat.completions.create(
                        model=config.PROMPT_BOT,
                        messages=[{
                                "role": "user",
                                "content": translation_prompt + res_text
                        }]
                ) 

        if completion.choices[0].message.content is not None:
               res_text: str = completion.choices[0].message.content
        else:
              return None

        print(f"first prompt {translation_prompt} '\n' {chapter}\n")
        print(f"first completion {completion}\n")

        if count_paragraphs(res_text) < 6:
            completion = client.chat.completions.create(
                model=config.PROMPT_BOT,
                messages=[{
                    "role": "user",
                    "content": config.SYSTEM_PROMPT_2 + res_text
                }]
            )   
            print(f"second prompt [SPLIT] {config.SYSTEM_PROMPT_2 + res_text}\n")
            print(f"second completion [SPLIT] {completion}\n")

        if completion.choices[0].message.content is not None:
               res_text = normalize_linebreak(completion.choices[0].message.content)
        else:
              return None

        return res_text.encode('utf-8')
    except Exception as e:
        print(f"An error occurred in client_msg_wrapper: {e}")
        raise

@stub.function(
    image=image
)
def translate(content: str, prompt: Optional[str] = None) -> List[Optional[Union[str, None]]]:
    volume = modal.NetworkFileSystem.lookup("job_storage")
    job_id: uuid.UUID = uuid.uuid4()
    output: List[Optional[Union[str, None]]] = []
    output.append(str(job_id))
    try:
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
        for index, translation_res in enumerate(translations, start=1):
            file_name = f"{job_id}_{index}"
            if not isinstance(translation_res, bytes):
                raise TypeError(f"Expected bytes, got {type(translation_res)}")
            volume.write_file(f"/res/{file_name}", io.BytesIO(translation_res))

            translation_text: str = translation_res.decode('utf-8')
            output.append(translation_text)
        
    except FileNotFoundError as fnf_error:
        print(f"Error: The file {file_name} was not found: {fnf_error}")
    except Exception as e:
        print(f"An error occurred in translate: {e}")
        raise
    return output


@stub.function(
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
        
        chapters_w_prompt: List[Tuple[str, Optional[str]]] = [
            # should be able to fetch old prompt
            (chapter, None) for chapter in chapters
        ]

        # currently redone files will be re-arranged
        translations = client_msg_wrapper.map(chapters_w_prompt)
        for index, translation_res in enumerate(translations, start=1):
            file_name = f"{job_id}_{index}"
            if not isinstance(translation_res, bytes):
                raise TypeError(f"Expected bytes, got {type(translation_res)}")
            volume.write_file(f"/res/{file_name}", io.BytesIO(translation_res))

            translation_text: str = translation_res.decode('utf-8')
            output.append(translation_text)
        
    except FileNotFoundError as fnf_error:
        print(f"Error: The file {file_name} was not found: {fnf_error}")
    except Exception as e:
        print(f"An error occurred in translate: {e}")
        raise
    return output
