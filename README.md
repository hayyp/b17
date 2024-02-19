# B17

B17 is an efficient command line tool crafted for batching translation jobs. It harnesses the power of several concurrent features offered by Modal, such as `NetworkFileSystem` and `map`, which allow us to initiate multiple OpenAI completion requests in parallel and thus perform numerous translation jobs at the same time.

## Usage
```
usage: local.py [-h] [-t source_file] [-c source_file custom_prompt_file] [-r job_id [chapter_indexes ...]]

A command-line helper for batching translation jobs.

options:
  -h, --help            show this help message and exit
  -t source_file, --translate source_file
                        Translate the content of a local file. Usage: -t [source_file]
  -c source_file custom_prompt_file, --custom source_file custom_prompt_file
                        Use your own instruction for the translation. Usage: -c [source_file] [custom_prompt_file]
  -r job_id [chapter_indexes ...], --redo job_id [chapter_indexes ...]
                        Get new translations based on an ID and chapter indices. Usage: -r [job_id] [chapter_index_1]
                        [chapter_index_2] ...
```

## How to deploy and how to run


1. install openai module with `pip`
```shell
pip install openai
```
2. install and setup `modal`
```shell
pip install modal
modal setup
```
3. deploy `remote.py` to modal
```shell
modal deploy remote
```
4. run the local script with python
```shell
python local.py -t source_file.txt
```
5. you will see a `result.txt` file once the translation is done
