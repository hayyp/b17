import modal
import argparse
from typing import Tuple, List, Union, Optional

translate = modal.Function.lookup("bot17", "translate")
translate_w_example = modal.Function.lookup("bot17", "translate_w_example")
redo_translate = modal.Function.lookup("bot17", "redo_translate")


def main():
    print("translation job initialized...")

    parser = argparse.ArgumentParser(description="A command-line helper for batching translation jobs.")
    parser.add_argument('-t', '--translate', 
                        type=str, 
                        metavar='source_file',
                        help='Translate the content of a local file. Usage: -t [source_file]')

    parser.add_argument('-m', '--mimic', 
                        nargs=2, 
                        metavar=('sample_file', 'source_file'),
                        help='Study a sample file before translation. Usage: -m [sample_file] [source_file]')

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
    elif args.mimic:
        with open(args.mimic[0], 'r', encoding='utf-8') as sample_text:
            with open(args.mimic[1], 'r', encoding='utf-8') as source_file:
                with open("result.txt", 'w') as destination_content:
                    sample_txt_content: str = sample_text.read()
                    source_file_content: str = source_file.read()
                    results: List[Optional[Union[str, None]]] = translate_w_example.remote(
                        sample_txt_content, source_file_content
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