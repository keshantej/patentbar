# Patent Bar Drilling Tool

This project offers an interactive way to practice true/false questions while preparing for the U.S. Patent Bar. The web interface runs completely in the browser and tracks progress locally, so no server is required. Features such as dark mode, keyboard shortcuts, and responsive design make the tool convenient on both desktop and mobile.

The companion `question_bank_tool.py` is a small Tkinter application for editing the CSV-based question bank. You can load an existing file, search and filter questions, update explanations, and export your revised dataset.

A public deployment is available at <https://keshantej.github.io/patentbar> using the sample question bank provided here.

## Running Locally

Simply open `index.html` in a browser or serve the directory with any static file server. To customize the questions, run `python question_bank_tool.py` and edit the CSV to your liking.

## License and Attribution

This repository is a non-commercial, open-source study aid. The sample questions are included only to illustrate how the tool works. You are encouraged to adapt the data or replace it entirely with your own. If you believe any content infringes on your rights, please contact me so that I can address the issue.
