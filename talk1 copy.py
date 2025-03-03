import os
import nbformat

def read_and_concatenate_notebooks(directory):
    """
    Reads all .ipynb files in the specified directory, extracts the code cells,
    and concatenates them in alphabetical order of filenames.
    """
    notebook_files = [f for f in os.listdir(directory) if f.endswith('.ipynb')]
    notebook_files.sort()  # Sort files alphabetically

    concatenated_code = ""

    for notebook_file in notebook_files:
        notebook_path = os.path.join(directory, notebook_file)
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
            for cell in notebook.cells:
                if cell.cell_type == 'code':
                    concatenated_code += cell.source + "\n\n"

    return concatenated_code

# Example usage
directory_path = './build-ai-agents-and-chatbots-with-langgraph-2021112'  # Specify the directory containing the .ipynb files
all_code = read_and_concatenate_notebooks(directory_path)
print(all_code)
