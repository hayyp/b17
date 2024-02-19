import modal
import argparse
from typing import Tuple, List, Union, Optional

translate = modal.Function.lookup("bot17", "translate")
redo_translate = modal.Function.lookup("bot17", "redo_translate")


def main():
    print("translation job initialized...")

    parser = argparse.ArgumentParser(description="A command-line helper for batching translation jobs.")
    parser.add_argument('-t', '--translate', 
                        type=str, 
                        metavar='source_file',
                        help='Translate the content of a local file. Usage: -t [source_file]')

    parser.add_argument('-c', '--custom', 
                        nargs=2, 
                        metavar=('custom_prompt_file', 'source_file'),
                        help='Use your own instruction for the translation. Usage: -c [custom_prompt_file] [source_file]')

    parser.add_argument('-r', '--redo', 
                        nargs='+', 
                        type=str, 
                        metavar=('job_id', 'chapter_indexes'),
                        help='Get new translations based on an ID and chapter indices. Usage: -r [job_id] [chapter_index_1] [chapter_index_2] ...')

    args = parser.parse_args()
    print("translation job initialized...")

    if args.translate:
        file_name = args.translate
        file_name_without_ext = file_name.rsplit(".", 1)[0]
        with open(args.translate, 'r', encoding='utf-8') as source_file:
            with open(file_name_without_ext+"_en.txt", 'w') as destination_content:
                results: List[Optional[Union[str, None]]] = translate.remote(source_file.read()) # string
                index = 0
                for result in results:
                    if index == 0:
                        print("Job ID: " + result)
                        index = index + 1
                    elif isinstance(result, str):
                        destination_content.write(result + '\n\n')
    elif args.custom:
        file_name = args.custom[1]
        file_name_without_ext = file_name.rsplit(".", 1)[0]
        with open(args.custom[0], 'r', encoding='utf-8') as prompt_text:
            with open(args.custom[1], 'r', encoding='utf-8') as source_file:
                with open(file_name_without_ext+"_en.txt", 'w') as destination_content:
                    prompt_txt_content: str = prompt_text.read()
                    source_file_content: str = source_file.read()
                    results: List[Optional[Union[str, None]]] = translate.remote(
                        source_file_content, prompt_txt_content
                    )
                    index = 0
                    for result in results:
                        if index == 0:
                            print("Job ID: " + result)
                            index = index + 1
                        elif isinstance(result, str):
                            destination_content.write(result + '\n\n')
    elif args.redo:
        id = args.redo[0]
        indexes =  [int(index) for index in args.redo[1:]]
        ext = "_".join(str(index) for index in indexes)

        with open(f"fixed_result_{ext}.txt", 'w') as destination_content:
            results: List[Optional[Union[str, None]]] = redo_translate.remote(id, indexes) # string
            index = 0
            for result in results:
                if index == 0:
                    print("Job ID: " + result)
                    index = index + 1
                elif isinstance(result, str):
                    destination_content.write(result + '\n\n')
    else:
        parser.print_help()

if __name__ == "__main__":
    main()