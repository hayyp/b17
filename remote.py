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
    enum_chapter: List[Optional[Union[str, None]]]
) -> Tuple[int, bytes]:
    try:
        index, chapter = enum_chapter
        
        client = OpenAI(
            api_key=os.environ["b17_openai_token"],
            base_url=f"https://{os.environ['b17_mirror_url']}/v1"
        )
        
        completion = client.chat.completions.create(
            model=config.PROMPT_BOT,
            messages=[{

                "role": "user",
                "content": config.SYSTEM_PROMPT + chapter
            }]
        )
        
        # if completion.choices[0].message.content is not None:
        res_text: str = completion.choices[0].message.content
        print(f"Working on INDEX {index}\n")
        print(f"first prompt {config.SYSTEM_PROMPT + chapter}\n")
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

        #if completion.choices[0].message.content is not None:
        res_text = normalize_linebreak(completion.choices[0].message.content)

        return (index, res_text.encode('utf-8'))
    except Exception as e:
        print(f"An error occurred in client_msg_wrapper: {e}")
        raise

@stub.function(
    image=image
)
def translate(content: str) -> List[Optional[Union[str, None]]]:
    volume = modal.NetworkFileSystem.lookup("job_storage")
    job_id: uuid.UUID = uuid.uuid4()
    output: List[Optional[Union[str, None]]] = [None] * 101  # maximum capacity = 100 so far
    output[0] = str(job_id)
    try:
        chapters: List[str] = content.split('#####')[1:]
        chapters = [chapter.strip() for chapter in chapters]
        enum_chapters: List[Tuple[int, str]] = list(enumerate(chapters, start=1))
        
        for index, chapter in enum_chapters:
            file_name = f"{job_id}_{index}"
            chapter_obj = io.BytesIO(chapter.encode('utf-8'))
            volume.write_file(f"/src/{file_name}", chapter_obj)
        
        # translate
        for index, translation_res in client_msg_wrapper.map(enum_chapters):
            # client_msg_wrapper.map -> List[Tuple[int, bytes]]:
            file_name = f"{job_id}_{index}"
            if not isinstance(translation_res, bytes):
                raise TypeError(f"Expected bytes, got {type(translation_res)}")
            volume.write_file(f"/res/{file_name}", io.BytesIO(translation_res))

            translation_text: str = translation_res.decode('utf-8')
            output[index] = translation_text
        
    except FileNotFoundError as fnf_error:
        print(f"Error: The file {file_name} was not found: {fnf_error}")
    except Exception as e:
        print(f"An error occurred in translate: {e}")
        raise
    return output

def count_asian_characters_and_punctuation(text):
    pattern = r'[\u4e00-\u9fff\u3000-\u303F\u2000-\u206F\uFF00-\uFFEF【】：；“”‘’，。·￥……《》？（）]+'
    matches = re.findall(pattern, text)
    return sum(len(match) for match in matches)

def split_into_segments(chapter_content):
    chapter_word_count = count_asian_characters_and_punctuation(chapter_content)
    print("Ch. Word Count: ", chapter_word_count)
    x = chapter_word_count // config.TOKEN_LIMIT_FOR_TWE
    y: int
    if x == 0:
        return [chapter_content]
    else:
        y = chapter_word_count // (x + 1)
    
    segments = []
    current_segment = ""
    current_word_count = 0
    
    for line in chapter_content.split('\n'):
        line_word_count = count_asian_characters_and_punctuation(line)
        
        if ((current_word_count > y and current_segment) 
            or current_word_count + line_word_count > config.TOKEN_LIMIT_FOR_TWE):
            segments.append(current_segment)
            current_segment = line + '\n'
            current_word_count = line_word_count
        else:
            current_segment += line + '\n'
            current_word_count += line_word_count
    
    # Append the last segment if it's not empty
    if current_segment:
        segments.append(current_segment)
    
    print("SEG Count: ", len(segments))
    
    return segments

@stub.function(
    image=image,
    secrets=[modal.Secret.from_name("b17")]
)
def twe_client_msg_wrapper(
    sample: str,
    enum_chapter: List[Optional[Union[str, None]]]
) -> Tuple[int, bytes]:
    try:
        index, chapter = enum_chapter
        
        client = OpenAI(
            api_key=os.environ["b17_openai_token"],
            base_url=f"https://{os.environ['b17_mirror_url']}/v1"
        )
        
        segments: List[str] = split_into_segments(chapter)
        res_text: str = ""
        for segment in segments:
            completion = client.chat.completions.create(
                model=config.PROMPT_BOT,
                messages=[{
                    "role": "system",
                    "content": config.SYSTEM_PROMPT_3 + sample
                }, {
                    "role": "user",
                    "content": config.SYSTEM_PROMPT + segment
                }]
            )
            if count_paragraphs(completion.choices[0].message.content) < 3:
                completion = client.chat.completions.create(
                    model=config.PROMPT_BOT,
                    messages=[{
                        "role": "system",
                        "content": config.SYSTEM_PROMPT_2
                    }, {
                        "role": "user",
                        "content": res_text
                    }]
                )
            res_text = res_text + completion.choices[0].message.content + '\n'

        res_text = normalize_linebreak(res_text)

        return (index, res_text.encode('utf-8'))
    except Exception as e:
        print(f"An error occurred in client_msg_wrapper: {e}")
        raise

@stub.function(
    image=image
)
def translate_w_example(sample_file_content: str, source_file: str):
    volume = modal.NetworkFileSystem.lookup("job_storage")
    job_id: uuid.UUID = uuid.uuid4()
    output: List[Optional[Union[str, None]]] = [None] * 101  # maximum capacity = 100 so far
    output[0] = str(job_id)
    try:
        chapters: List[str] = source_file.split('#####')[1:]
        chapters = [chapter.strip() for chapter in chapters]
        enum_chapters: List[Tuple[int, str]] = list(enumerate(chapters, start=1))
        
        for index, chapter in enum_chapters:
            file_name = f"{job_id}_{index}"
            chapter_obj = io.BytesIO(chapter.encode('utf-8'))
            volume.write_file(f"/src/{file_name}", chapter_obj)
        
        # translate
        for index, translation_res in twe_client_msg_wrapper.map(
                sample_file_content,
                enum_chapters
            ):
            # client_msg_wrapper.map -> List[Tuple[int, bytes]]:
            file_name = f"{job_id}_{index}"
            if not isinstance(translation_res, bytes):
                raise TypeError(f"Expected bytes, got {type(translation_res)}")
            volume.write_file(f"/res/{file_name}", io.BytesIO(translation_res))

            translation_text: str = translation_res.decode('utf-8')
            output[index] = translation_text
        
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
        output: List[Optional[Union[str, None]]] = [None] * 101
        output[0] = str(job_id)
        for index in indexes:
            file = volume.read_file(f"/src/{prev_id}_{index}")
            file_obj = b''.join(file)
            file_content = file_obj.decode('utf-8')
            chapters.append(file_content)

        enum_chapters: List[Tuple[int, str]] = list(enumerate(chapters, start=1))

        # currently redone files will be re-arranged
        for index, translation_res in client_msg_wrapper.map(enum_chapters):
            file_name = f"{job_id}_{index}"
            if not isinstance(translation_res, bytes):
                raise TypeError(f"Expected bytes, got {type(translation_res)}")
            volume.write_file(f"/res/{file_name}", io.BytesIO(translation_res))

            translation_text: str = translation_res.decode('utf-8')
            output[index] = translation_text
        
    except FileNotFoundError as fnf_error:
        print(f"Error: The file {file_name} was not found: {fnf_error}")
    except Exception as e:
        print(f"An error occurred in translate: {e}")
        raise
    return output
