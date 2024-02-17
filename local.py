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
                        help='-t [source_file] to translate the content of a local file.')
    parser.add_argument('-m', '--mimic', 
                        nargs=2, 
                        help='-m [sample_file] [source_file] to study sample_file before translation.')
    parser.add_argument('-r', '--redo', 
                        nargs='+', 
                        type=str, 
                        help='-r [id] [chapter_index_1] [chapter_index2] ... to get new translations')

    args = parser.parse_args()
    print("translation job initialized...")

    if args.translate:
        with open(args.translate, 'r', encoding='utf-8') as source_file:
            with open("result.txt", 'w') as destination_content:
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

        with open("fixed_result.txt", 'w') as destination_content:
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