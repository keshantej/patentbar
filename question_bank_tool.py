import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
import time # Import time for potential future use or just note the date

class QuestionBankEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Question Bank Editor")
        # Increased height slightly again for the new button row
        self.master.geometry("900x680")

        # Data storage
        self.questions_data = []
        self.current_csv_path = None
        self.selected_data_index = None
        self.listbox_to_data_map = []
        self.original_questions = {}

        # --- GUI Setup ---
        self.main_frame = ttk.Frame(master, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.rowconfigure(2, weight=1) # Listbox/Details row

        # --- Top Controls (Row 0) ---
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.load_button = ttk.Button(self.control_frame, text="Load CSV", command=self.load_csv)
        self.load_button.pack(side=tk.LEFT, padx=5)
        # Renamed for clarity
        self.save_all_button = ttk.Button(self.control_frame, text="Save All to CSV", command=self.save_csv_file, state=tk.DISABLED)
        self.save_all_button.pack(side=tk.LEFT, padx=5)
        self.add_button = ttk.Button(self.control_frame, text="Add Question", command=self.add_question, state=tk.DISABLED)
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(self.control_frame, text="Delete Question", command=self.delete_question, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(self.control_frame, text="Load a CSV file to begin.")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # --- Search Frame (Row 1, Column 0) ---
        self.search_frame = ttk.Frame(self.main_frame)
        self.search_frame.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        ttk.Label(self.search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_var.trace_add("write", self.filter_questions_event)

        # --- Left Pane: Question List (Row 2, Column 0) ---
        self.listbox_frame = ttk.Frame(self.main_frame)
        self.listbox_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        self.listbox_frame.rowconfigure(0, weight=1)
        self.listbox_frame.columnconfigure(0, weight=1)
        self.listbox_scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL)
        self.question_listbox = tk.Listbox(
            self.listbox_frame, yscrollcommand=self.listbox_scrollbar.set, exportselection=False
        )
        self.listbox_scrollbar.config(command=self.question_listbox.yview)
        self.question_listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox_scrollbar.grid(row=0, column=1, sticky="ns")
        self.question_listbox.bind('<<ListboxSelect>>', self.on_question_select)

        # --- Right Pane: Details View (Row 2, Column 1) ---
        self.details_frame = ttk.Frame(self.main_frame)
        self.details_frame.grid(row=2, column=1, sticky="nsew")
        self.details_frame.columnconfigure(1, weight=1)

        # (Detail widgets setup: Question, Answer, Explanation, Chapter)
        ttk.Label(self.details_frame, text="Question:").grid(row=0, column=0, sticky="nw", pady=2, padx=5)
        self.question_text = tk.Text(self.details_frame, height=8, width=60, wrap=tk.WORD)
        self.question_text.grid(row=0, column=1, sticky="ew", pady=2, padx=5)
        self.question_text_scrollbar = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL, command=self.question_text.yview)
        self.question_text['yscrollcommand'] = self.question_text_scrollbar.set
        self.question_text_scrollbar.grid(row=0, column=2, sticky="ns")

        ttk.Label(self.details_frame, text="Answer:").grid(row=1, column=0, sticky="nw", pady=2, padx=5)
        self.answer_var = tk.BooleanVar()
        self.answer_frame = ttk.Frame(self.details_frame)
        self.answer_frame.grid(row=1, column=1, sticky="w", pady=2, padx=5)
        self.true_radio = ttk.Radiobutton(self.answer_frame, text="True", variable=self.answer_var, value=True)
        self.false_radio = ttk.Radiobutton(self.answer_frame, text="False", variable=self.answer_var, value=False)
        self.true_radio.pack(side=tk.LEFT)
        self.false_radio.pack(side=tk.LEFT, padx=10)

        ttk.Label(self.details_frame, text="Explanation:").grid(row=2, column=0, sticky="nw", pady=2, padx=5)
        self.explanation_text = tk.Text(self.details_frame, height=10, width=60, wrap=tk.WORD)
        self.explanation_text.grid(row=2, column=1, sticky="ew", pady=2, padx=5)
        self.explanation_text_scrollbar = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL, command=self.explanation_text.yview)
        self.explanation_text['yscrollcommand'] = self.explanation_text_scrollbar.set
        self.explanation_text_scrollbar.grid(row=2, column=2, sticky="ns")

        ttk.Label(self.details_frame, text="Chapter:").grid(row=3, column=0, sticky="nw", pady=2, padx=5)
        self.chapter_entry = ttk.Entry(self.details_frame, width=60)
        self.chapter_entry.grid(row=3, column=1, sticky="ew", pady=2, padx=5)

        # --- *** NEW: Button Row in Details Frame *** ---
        self.detail_button_frame = ttk.Frame(self.details_frame)
        self.detail_button_frame.grid(row=4, column=1, sticky="w", pady=(10, 2), padx=5)

        # New button to explicitly save current question's edits to memory
        self.save_this_q_button = ttk.Button(
            self.detail_button_frame,
            text="Save This Question (in Session)", # Clarify it's not writing file yet
            command=self.save_this_question, # Link to new method
            state=tk.DISABLED
        )
        self.save_this_q_button.pack(side=tk.LEFT, padx=(0, 10))

        # Existing button
        self.copy_prompt_button = ttk.Button(
            self.detail_button_frame,
            text="Copy Prompt for LLM",
            command=self.copy_llm_prompt,
            state=tk.DISABLED
        )
        self.copy_prompt_button.pack(side=tk.LEFT)
        # --- *** END NEW *** ---

        # Disable detail fields initially
        self.set_details_state(tk.DISABLED)

    # --- Core Logic Methods ---

    def set_details_state(self, state):
        """Enable or disable all detail view widgets."""
        widgets = [
            self.question_text, self.explanation_text, self.chapter_entry,
            self.true_radio, self.false_radio,
            self.copy_prompt_button,
            self.save_this_q_button # Include the new button
        ]
        button_state = state if state == tk.NORMAL else tk.DISABLED
        for widget in widgets:
            if isinstance(widget, tk.Text):
                widget.config(state=state)
            else:
                # Ensure buttons use proper disabled state constant
                widget.config(state=button_state)


    def update_status(self, message):
        """Update the status bar label."""
        # Optional: Add timestamp to status
        # timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        # self.status_label.config(text=f"[{timestamp}] {message}")
        self.status_label.config(text=message)
        self.master.update_idletasks()

    def filter_questions(self):
        """Filters the listbox based on the search entry."""
        search_term = self.search_var.get().lower().strip()
        # Store current selection before clearing listbox
        selected_data_index_before_filter = self.selected_data_index

        self.question_listbox.delete(0, tk.END)
        self.listbox_to_data_map = []

        new_listbox_index_for_selected = None # Track if selected item reappears

        for original_index, q_data in enumerate(self.questions_data):
            question_text = q_data.get("question", "").lower()
            if not search_term or search_term in question_text:
                prefix = "* " if q_data.get("modified", False) else ""
                display_q_text = q_data.get('question', '<New Question>')
                display_text = f"{prefix}{display_q_text[:80]}"
                if len(display_q_text) > 80: display_text += "..."

                current_listbox_pos = self.question_listbox.size() # Index where it will be inserted
                self.question_listbox.insert(tk.END, display_text)
                self.listbox_to_data_map.append(original_index)

                # Check if this is the item that was selected before filtering
                if original_index == selected_data_index_before_filter:
                    new_listbox_index_for_selected = current_listbox_pos

        # After filtering, clear details IF the previously selected item is NOT visible anymore
        if selected_data_index_before_filter is not None and new_listbox_index_for_selected is None:
             self.clear_details() # Clears selection and disables fields
             self.update_status(f"Filtered list. Previous selection no longer visible.")
        elif new_listbox_index_for_selected is not None:
             # Reselect the item in its new position, but don't reload details unless needed
             self.question_listbox.selection_set(new_listbox_index_for_selected)
             self.question_listbox.activate(new_listbox_index_for_selected)


    def filter_questions_event(self, *args):
        """Callback wrapper for search_var trace."""
        self.filter_questions()

    def load_csv(self):
        """Open a file dialog to select and load a CSV file."""
        # Ask to save unsaved changes before loading new file
        if any(q.get("modified", False) for q in self.questions_data):
            if messagebox.askyesno("Unsaved Changes", "There are unsaved changes. Save them to the current file before loading a new one?"):
                self.save_csv_file() # Attempt to save current file first
            # If user chooses No, proceed to load without saving

        # --- Proceed with loading ---
        filepath = filedialog.askopenfilename(
            title="Open Question Bank CSV", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath: return

        try:
            # Reset state
            self.questions_data = []
            self.original_questions = {}
            self.selected_data_index = None
            self.listbox_to_data_map = []

            expected_headers = ["question", "answer", "explanation", "chapter"]
            with open(filepath, mode='r', newline='', encoding='utf-8') as csvfile:
                first_line = csvfile.readline()
                if first_line.startswith('\ufeff'): first_line = first_line[1:]
                csvfile.seek(0)
                reader = csv.DictReader(csvfile)
                if not reader.fieldnames or [h.lower().strip() for h in reader.fieldnames] != [h.lower().strip() for h in expected_headers]:
                    raise ValueError(f"CSV headers mismatch. Expected: {expected_headers}. Found: {reader.fieldnames}")
                for i, row in enumerate(reader):
                    # Convert boolean-like strings explicitly
                    answer_str = row.get("answer", "").strip().capitalize()
                    if answer_str not in ["True", "False"]:
                        print(f"Warning: Row {i+1}: Invalid answer '{row.get('answer')}', defaulting to False.")
                        answer_str = "False"

                    cleaned_row = {
                        "question": row.get("question", "").strip(),
                        "answer": answer_str,
                        "explanation": row.get("explanation", "").strip(),
                        "chapter": row.get("chapter", "").strip(),
                        "modified": False # Reset modified flag on load
                    }
                    self.questions_data.append(cleaned_row)
                    self.original_questions[i] = cleaned_row.copy()

            self.current_csv_path = filepath
            self.master.title(f"Question Bank Editor - {os.path.basename(filepath)}")
            self.search_var.set("") # Clear search field
            self.filter_questions() # Populate listbox using filter
            self.clear_details()
            self.set_details_state(tk.DISABLED)
            self.save_all_button.config(state=tk.NORMAL) # Enable "Save All" button
            self.add_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.DISABLED)
            self.update_status(f"Loaded {len(self.questions_data)} questions from {os.path.basename(filepath)}")

        except Exception as e:
            messagebox.showerror("Error Loading CSV", f"An error occurred: {e}")
            self.update_status("Error loading file.")


    def clear_details(self):
        """Clear the detail view fields and disable them."""
        self.set_details_state(tk.NORMAL)
        self.question_text.delete("1.0", tk.END)
        self.explanation_text.delete("1.0", tk.END)
        self.chapter_entry.delete(0, tk.END)
        self.answer_var.set(False)
        self.set_details_state(tk.DISABLED) # Disable fields AND buttons in details pane
        self.selected_data_index = None
        self.delete_button.config(state=tk.DISABLED)


    def on_question_select(self, event=None):
        """Handle selection change in the listbox."""
        selection = self.question_listbox.curselection()
        if not selection: return

        listbox_index = selection[0]

        if not (0 <= listbox_index < len(self.listbox_to_data_map)):
            print(f"Warning: Listbox index {listbox_index} out of range for map.")
            return
        new_data_index = self.listbox_to_data_map[listbox_index]

        # --- Keep the auto-save-on-navigate for now ---
        # User can rely on explicit button OR this fallback
        if self.selected_data_index is not None and self.selected_data_index != new_data_index:
            if not self.update_current_question_in_memory(explicit_save=False): # Pass flag
                # Reselect previous item visually if update failed/cancelled
                try:
                    prev_listbox_index = self.listbox_to_data_map.index(self.selected_data_index)
                    self.question_listbox.selection_clear(0, tk.END)
                    self.question_listbox.selection_set(prev_listbox_index)
                    self.question_listbox.activate(prev_listbox_index)
                except ValueError: pass
                return
        # --- End auto-save block ---

        self.selected_data_index = new_data_index

        if 0 <= self.selected_data_index < len(self.questions_data):
            q_data = self.questions_data[self.selected_data_index]
            self.set_details_state(tk.NORMAL) # Enable fields

            self.question_text.delete("1.0", tk.END)
            self.question_text.insert("1.0", q_data.get("question", ""))
            self.explanation_text.delete("1.0", tk.END)
            self.explanation_text.insert("1.0", q_data.get("explanation", ""))
            self.chapter_entry.delete(0, tk.END)
            self.chapter_entry.insert(0, q_data.get("chapter", ""))
            self.answer_var.set(q_data.get("answer", "False") == "True")

            self.delete_button.config(state=tk.NORMAL)
            self.update_status(f"Displaying question {listbox_index + 1} (of filtered list). Original index: {self.selected_data_index + 1}")
        else:
            self.clear_details()
            self.update_status("Error: Invalid data index.")


    # --- *** NEW: Method for the explicit save button *** ---
    def save_this_question(self):
        """Explicitly saves the current question's edits to memory."""
        # --- *** Store the index BEFORE calling update *** ---
        index_being_saved = self.selected_data_index

        if index_being_saved is None:
             messagebox.showwarning("Save Warning", "No question selected to save.")
             return

        # Call the update function
        update_successful = self.update_current_question_in_memory(explicit_save=True)

        # --- *** Use the stored index for the status message *** ---
        if update_successful:
             # Check if the selection was cleared during the update (meaning it vanished from filter)
             if self.selected_data_index is None:
                  self.update_status(f"Question (original index {index_being_saved + 1}) updated, but no longer matches filter.")
             else:
                  # Use the original index in the success message
                  self.update_status(f"Question (original index {index_being_saved + 1}) updated in session.")
        else:
             # Update function already shows error message, provide generic status
             self.update_status(f"Failed to update question (original index {index_being_saved + 1}).")
     


    # Modified update function to accept a flag
    def update_current_question_in_memory(self, explicit_save=False):
        """
        Read data from detail widgets and update the in-memory list.
        If explicit_save is True, called by button. If False, called by navigation.
        Returns True on success, False on failure.
        """
        if self.selected_data_index is None or not (0 <= self.selected_data_index < len(self.questions_data)):
            # Don't show error if called implicitly by navigation away from nothing
            if explicit_save:
                 messagebox.showerror("Error", "Cannot save, no valid question selected.")
            return False # Nothing selected or index invalid

        if self.question_text.cget('state') == tk.DISABLED:
             # This shouldn't happen if button state is managed correctly, but check anyway
             if explicit_save:
                  messagebox.showerror("Error", "Cannot save, detail fields are not editable.")
             return False

        try:
            current_data = self.questions_data[self.selected_data_index]

            # Get data from widgets
            new_question = self.question_text.get("1.0", tk.END).strip()
            new_answer_str = "True" if self.answer_var.get() else "False"
            new_explanation = self.explanation_text.get("1.0", tk.END).strip()
            new_chapter = self.chapter_entry.get().strip()

            # Check if anything actually changed
            changed = (
                new_question != current_data.get("question", "") or
                new_answer_str != current_data.get("answer", "") or
                new_explanation != current_data.get("explanation", "") or
                new_chapter != current_data.get("chapter", "")
            )

            if changed:
                current_data["question"] = new_question
                current_data["answer"] = new_answer_str
                current_data["explanation"] = new_explanation
                current_data["chapter"] = new_chapter
                current_data["modified"] = True # Mark as modified

                # --- Refresh filter to update asterisk and text immediately ---
                current_data_index_to_reselect = self.selected_data_index
                self.filter_questions()

                # Try to re-select the item
                try:
                    new_listbox_index = self.listbox_to_data_map.index(current_data_index_to_reselect)
                    self.question_listbox.selection_set(new_listbox_index)
                    self.question_listbox.activate(new_listbox_index)
                    self.question_listbox.see(new_listbox_index)
                    # Ensure state is correct after re-selection
                    self.selected_data_index = current_data_index_to_reselect
                    self.set_details_state(tk.NORMAL)
                    self.delete_button.config(state=tk.NORMAL)
                except ValueError:
                    self.selected_data_index = None
                    self.clear_details()
                    self.update_status("Question updated. No longer matches filter.")

            elif explicit_save: # If save button was pressed but nothing changed
                 self.update_status("No changes detected to save for this question.")

            return True # Indicate success (even if nothing changed)

        except tk.TclError as e:
            print(f"Warning: TclError during update: {e}")
            if explicit_save: messagebox.showerror("Error", f"Failed to read details: {e}")
            return False
        except Exception as e:
             messagebox.showerror("Error", f"Failed to update question data in memory:\n{e}")
             return False


    # Renamed method for clarity
    def save_csv_file(self):
        """Saves the entire current state of questions_data back to a CSV file."""
        if not self.current_csv_path:
            messagebox.showwarning("Warning", "No CSV file loaded or specified to save to.")
            return

        # Ensure the currently displayed question's edits are captured before final save
        if self.selected_data_index is not None:
            if not self.update_current_question_in_memory(explicit_save=False): # Save implicitly before full save
                self.update_status("Save cancelled due to error updating current question.")
                return

        # Confirm saving to the *original* path
        confirm_msg = f"Save all changes ({sum(1 for q in self.questions_data if q.get('modified'))} modified, {len(self.questions_data)} total) to:\n{self.current_csv_path}?"
        if not messagebox.askyesno("Confirm Save All", confirm_msg):
            self.update_status("Save cancelled by user.")
            return

        save_path = self.current_csv_path # Use the loaded path

        try:
            # Write data (excluding 'modified' key)
            headers = ["question", "answer", "explanation", "chapter"]
            with open(save_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                for row_data in self.questions_data:
                    row_to_write = {k: v for k, v in row_data.items() if k in headers}
                    writer.writerow(row_to_write)

            # Reset modification markers
            for item in self.questions_data: item['modified'] = False
            self.original_questions = {i: data.copy() for i, data in enumerate(self.questions_data)}

            self.master.title(f"Question Bank Editor - {os.path.basename(save_path)}") # Ensure title is correct

            # Refresh filter and reselect
            current_data_index_to_reselect = self.selected_data_index
            self.filter_questions() # Refresh listbox to remove '*'
            if current_data_index_to_reselect is not None:
                try:
                    new_listbox_index = self.listbox_to_data_map.index(current_data_index_to_reselect)
                    self.question_listbox.selection_set(new_listbox_index)
                    self.question_listbox.activate(new_listbox_index)
                    self.selected_data_index = current_data_index_to_reselect
                    self.set_details_state(tk.NORMAL)
                    self.delete_button.config(state=tk.NORMAL)
                except ValueError:
                    self.selected_data_index = None
                    self.clear_details()

            self.update_status(f"Question bank saved successfully to {os.path.basename(save_path)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV file:\n{e}")
            self.update_status("Error saving file.")

    # Add/Delete/Copy methods remain largely the same, using selected_data_index
    # and calling filter_questions() after data modification.

    def add_question(self):
        """Add a new, blank question entry."""
        if self.selected_data_index is not None:
            if not self.update_current_question_in_memory(explicit_save=False):
                self.update_status("Add cancelled: error updating current question.")
                return

        new_question_data = { "question": "", "answer": "False", "explanation": "", "chapter": "", "modified": True }
        self.questions_data.append(new_question_data)
        new_data_index = len(self.questions_data) - 1

        self.filter_questions() # Refresh list based on current search
        try:
            new_listbox_index = self.listbox_to_data_map.index(new_data_index)
            self.question_listbox.selection_clear(0, tk.END)
            self.question_listbox.selection_set(new_listbox_index)
            self.question_listbox.activate(new_listbox_index)
            self.question_listbox.see(new_listbox_index)
            self.on_question_select() # Load empty details
            self.question_text.focus_set()
            self.update_status(f"Added new question. Fill details and save.")
        except ValueError:
             self.update_status(f"Added new question (original index {new_data_index + 1}). Not visible with current filter.")


    def delete_question(self):
        """Delete the currently selected question."""
        if self.selected_data_index is None:
            messagebox.showwarning("Warning", "No question selected to delete.")
            return

        q_data = self.questions_data[self.selected_data_index]
        question_text = q_data.get("question", "this question")[:50]
        if len(question_text) == 50: question_text += "..."

        # Add check if modified, warn differently? Optional.
        # modified_status = " (unsaved changes)" if q_data.get("modified") else ""
        # confirm_msg = f"Delete '{question_text}'{modified_status}?"

        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this question?\n\n'{question_text}'"):
            return

        data_index_to_delete = self.selected_data_index
        del self.questions_data[data_index_to_delete]

        # Mark the overall dataset as modified if deleting something previously saved
        # This isn't strictly necessary with the current model but good practice
        # We might need a general 'session_modified' flag if we want fine-grained control

        current_listbox_selection = self.question_listbox.curselection()
        listbox_index_before_delete = current_listbox_selection[0] if current_listbox_selection else 0

        self.filter_questions() # Refresh listbox based on current search
        self.clear_details() # Clear details pane

        # Try re-selecting
        if self.question_listbox.size() > 0:
            new_selection_index = min(listbox_index_before_delete, self.question_listbox.size() - 1)
            self.question_listbox.selection_set(new_selection_index)
            self.question_listbox.activate(new_selection_index)
            self.on_question_select()
        else:
             self.selected_data_index = None # Ensure index is cleared if list empty

        self.update_status(f"Question deleted. {len(self.questions_data)} questions remaining.")

    def copy_llm_prompt(self):
        """Formats the current question details into an LLM prompt and copies to clipboard."""
        if self.selected_data_index is None:
            messagebox.showwarning("Warning", "No question selected.")
            return
        # (Rest of the copy logic is unchanged)
        try:
            question = self.question_text.get("1.0", tk.END).strip()
            answer_bool = self.answer_var.get()
            answer = "True" if answer_bool else "False"
            explanation = self.explanation_text.get("1.0", tk.END).strip()
            chapter = self.chapter_entry.get().strip()
        except tk.TclError as e:
             messagebox.showerror("Error", f"Could not retrieve text from input fields. Are they enabled?\n{e}")
             return
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred retrieving details:\n{e}")
             return

        if not question and not explanation:
            if not messagebox.askyesno("Empty Fields", "The question and explanation fields are empty. Still generate prompt?"):
                return

        prompt = f"""Please review the following question bank item for accuracy, clarity, and correctness.

Context: This is a True/False question related to chapter/topic "{chapter if chapter else 'Not Specified'}".

--- Question ---
{question}

--- Provided Answer ---
{answer}

--- Provided Explanation ---
{explanation}

---
Please provide feedback on:
1.  The clarity and accuracy of the **Question**. Is it well-phrased and unambiguous?
2.  The correctness of the **Provided Answer**. Is it definitively True or False based on the question?
3.  The accuracy, clarity, and helpfulness of the **Provided Explanation**. Does it correctly justify the answer? Is it easy to understand?

Suggest corrections or improvements if necessary.
"""
        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(prompt)
            self.update_status("LLM prompt copied to clipboard.")
        except tk.TclError:
             messagebox.showerror("Clipboard Error", "Could not access the system clipboard.")
             self.update_status("Failed to copy prompt.")
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred copying to clipboard:\n{e}")
             self.update_status("Failed to copy prompt.")


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = QuestionBankEditor(root)
    root.mainloop()
