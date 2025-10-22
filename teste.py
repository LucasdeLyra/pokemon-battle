# First, install the library:
# pip install streamlit-extras

import streamlit as st
from streamlit_extras.grid import grid

# Create a grid with a 2x2 layout (2 columns, 2 rows)
# Each number specifies the relative width of the columns.
my_grid = grid(2, 2, vertical_align="center")

# Add content to the grid cells. The order of the cells matters.
my_grid.text("Cell (0, 0)")
my_grid.text("Cell (0, 1)")
my_grid.text("Cell (1, 0)")
my_grid.text("Cell (1, 1)")