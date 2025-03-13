import nbformat
from nbformat import v4 as nbf
import os

class NotebookManager:
    """
    A class to manage Jupyter notebooks programmatically.
    Provides functionality to create, read, update, and execute notebook cells.
    """
    
    def __init__(self, notebook_path=None):
        """
        Initialize the NotebookManager with an optional notebook path.
        
        Args:
            notebook_path (str, optional): Path to an existing notebook or where a new one will be created.
        """
        self.notebook_path = notebook_path
        self.notebook = None
        
        if notebook_path and os.path.exists(notebook_path):
            self.load_notebook()
    
    def load_notebook(self):
        """Load an existing notebook from the specified path."""
        with open(self.notebook_path, 'r', encoding='utf-8') as f:
            self.notebook = nbformat.read(f, as_version=4)
        print(f"Loaded notebook from '{self.notebook_path}'.")
        
    def create_notebook(self, notebook_path=None, initial_code=None):
        """
        Create a new notebook with an optional initial code cell.
        
        Args:
            notebook_path (str, optional): Path where the notebook will be saved.
                                          If None, uses the path from initialization.
            initial_code (str, optional): Code to include in the first cell.
        """
        if notebook_path:
            self.notebook_path = notebook_path
            
        self.notebook = nbf.new_notebook()
        # Initialize metadata to avoid validation errors
        self.notebook.metadata = {}
        
        if initial_code:
            self.append_cell(initial_code)
            
        self.save_notebook()
        print(f"Created new notebook at '{self.notebook_path}'.")
    
    def save_notebook(self):
        """Save the notebook to the specified path."""
        if not self.notebook_path:
            raise ValueError("No notebook path specified.")
            
        with open(self.notebook_path, 'w', encoding='utf-8') as f:
            nbformat.write(self.notebook, f)
        print(f"Saved notebook to '{self.notebook_path}'.")
    
    def append_cell(self, source, cell_type='code'):
        """
        Append a new cell to the notebook.
        
        Args:
            source (str): The content of the cell.
            cell_type (str): Type of cell ('code', 'markdown', or 'raw').
        
        Returns:
            int: Index of the newly added cell.
        """
        if not self.notebook:
            raise ValueError("No notebook loaded or created.")
            
        if cell_type == 'code':
            cell = nbf.new_code_cell(source=source)
        elif cell_type == 'markdown':
            cell = nbf.new_markdown_cell(source=source)
        elif cell_type == 'raw':
            cell = nbf.new_raw_cell(source=source)
        else:
            raise ValueError(f"Invalid cell type: {cell_type}")
            
        self.notebook.cells.append(cell)
        return len(self.notebook.cells) - 1
    
    def update_cell(self, index, source=None, cell_type=None):
        """
        Update an existing cell at the specified index.
        
        Args:
            index (int): Index of the cell to update.
            source (str, optional): New content for the cell.
            cell_type (str, optional): New type for the cell.
        """
        if not self.notebook:
            raise ValueError("No notebook loaded or created.")
            
        if index < 0 or index >= len(self.notebook.cells):
            raise IndexError(f"Index {index} out of range for notebook with {len(self.notebook.cells)} cells.")
        
        cell = self.notebook.cells[index]
        
        if source is not None:
            cell.source = source
            
        if cell_type is not None and cell_type != cell.cell_type:
            # Create a new cell of the desired type
            if cell_type == 'code':
                new_cell = nbf.new_code_cell(source=cell.source)
            elif cell_type == 'markdown':
                new_cell = nbf.new_markdown_cell(source=cell.source)
            elif cell_type == 'raw':
                new_cell = nbf.new_raw_cell(source=cell.source)
            else:
                raise ValueError(f"Invalid cell type: {cell_type}")
                
            self.notebook.cells[index] = new_cell
    
    def delete_cell(self, index):
        """
        Delete a cell at the specified index.
        
        Args:
            index (int): Index of the cell to delete.
        """
        if not self.notebook:
            raise ValueError("No notebook loaded or created.")
            
        if index < 0 or index >= len(self.notebook.cells):
            raise IndexError(f"Index {index} out of range for notebook with {len(self.notebook.cells)} cells.")
            
        del self.notebook.cells[index]
    
    def get_cell(self, index):
        """
        Get a cell at the specified index.
        
        Args:
            index (int): Index of the cell to retrieve.
            
        Returns:
            NotebookNode: The cell at the specified index.
        """
        if not self.notebook:
            raise ValueError("No notebook loaded or created.")
            
        if index < 0 or index >= len(self.notebook.cells):
            raise IndexError(f"Index {index} out of range for notebook with {len(self.notebook.cells)} cells.")
            
        return self.notebook.cells[index]
    
    def get_cell_count(self):
        """
        Get the number of cells in the notebook.
        
        Returns:
            int: Number of cells in the notebook.
        """
        if not self.notebook:
            raise ValueError("No notebook loaded or created.")
            
        return len(self.notebook.cells)
    
    def execute_cell(self, index, globals_dict=None):
        """
        Execute a code cell at the specified index.
        
        Args:
            index (int): Index of the cell to execute.
            globals_dict (dict, optional): Global variables dictionary.
        """
        if not self.notebook:
            raise ValueError("No notebook loaded or created.")
            
        if index < 0 or index >= len(self.notebook.cells):
            raise IndexError(f"Index {index} out of range for notebook with {len(self.notebook.cells)} cells.")
            
        cell = self.notebook.cells[index]
        
        if cell.cell_type != 'code':
            print(f"Cell at index {index} is not a code cell (type: {cell.cell_type}).")
            return
        
        if globals_dict is None:
            globals_dict = globals()
            
        print(f"Executing cell {index}:")
        exec(cell.source, globals_dict)
    
    def execute_all_cells(self, globals_dict=None):
        """
        Execute all code cells in the notebook.
        
        Args:
            globals_dict (dict, optional): Global variables dictionary.
        """
        if not self.notebook:
            raise ValueError("No notebook loaded or created.")
            
        if globals_dict is None:
            globals_dict = globals()
            
        for i, cell in enumerate(self.notebook.cells):
            if cell.cell_type == 'code':
                print(f"Executing cell {i}:")
                exec(cell.source, globals_dict)

# Example usage
if __name__ == "__main__":
    # Create a new notebook manager
    nb_manager = NotebookManager()
    
    # Create a new notebook with an initial code cell
    nb_manager.create_notebook("my_notebook.ipynb", "# Initial cell\nprint('Hello, world!')")
    
    # Append a markdown cell
    nb_manager.append_cell("## This is a markdown heading", cell_type='markdown')
    
    # Append another code cell
    nb_manager.append_cell("import numpy as np\nx = np.array([1, 2, 3])\nprint(x)")
    
    # Update a cell
    nb_manager.update_cell(2, "## Updated markdown heading", cell_type='markdown')
    
    # Save the notebook
    nb_manager.save_notebook()
    
    # Execute all code cells
    nb_manager.execute_all_cells()