import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")  # Verwende TkAgg Backend für Matplotlib
import matplotlib.pyplot as plt
import numpy as np
import chardet
import os
import mplcursors


df = None
last_filepath = None
last_fileext = None
available_sheets = []

root = tk.Tk()
root.title("DataPlot")
root.geometry("500x400")

# --- GUI-Elemente ---

top_frame = tk.Frame(root)
top_frame.pack(fill=tk.BOTH, pady=10)

open_btn = tk.Button(top_frame, text="Datei laden", command=lambda: open_file())
open_btn.pack(side=tk.LEFT, padx=15)

# Delimiter-Auswahl (für CSV)
delimiter_label = tk.Label(top_frame, text="Trennzeichen:")
delimiter_var = tk.StringVar(value=";")
delimiter_combo = ttk.Combobox(top_frame, textvariable=delimiter_var, values=[",", ";", "\t", "|"], width=5)
# delimiter_combo.pack(side=tk.LEFT, padx=5)

# Sheet-Auswahl (für Excel)
sheet_label = tk.Label(top_frame, text="Tabellenblatt:")
sheet_var = tk.StringVar()
sheet_combo = ttk.Combobox(top_frame, textvariable=sheet_var, state="readonly", width=20)
sheet_combo.bind("<<ComboboxSelected>>", lambda e: load_excel_sheet())  # Sheet-Wechsel neu laden

# X-Achse Auswahl
xaxis_frame = tk.Frame(root)
xaxis_frame.pack(pady=5)

xaxis_label = tk.Label(xaxis_frame, text="Abszisse:")
xaxis_var = tk.StringVar()
xaxis_combo = ttk.Combobox(xaxis_frame, textvariable=xaxis_var, state="readonly", width=20)
opt_btn = tk.Button(xaxis_frame, text="...", command=lambda: open_option_dialog())

# Listbox für Spaltenauswahl
middle_frame = tk.Frame(root)
middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=0)

middle_frame.grid_rowconfigure(0, weight=1)
middle_frame.grid_columnconfigure(0, weight=1)

col_listbox = tk.Listbox(middle_frame, selectmode=tk.MULTIPLE, width=40)
col_listbox.grid(row=0, column=0, sticky="nsew")

bottom_frame = tk.Frame(root)
bottom_frame.pack(fill=tk.BOTH, padx=5, pady=10)

plot_btn = tk.Button(bottom_frame, text="Plotten", command=lambda: plot_columns())
plot_btn.pack(side=tk.RIGHT, padx=10)

show_btn = tk.Button(bottom_frame, text="Anzeigen", command=lambda: show_columns())
show_btn.pack(side=tk.LEFT, padx=10)

col_listbox_values = []
selected_y_indices = []

def save_y_selection(event):
    global selected_y_indices
    selected_y_indices = col_listbox.curselection()

def restore_y_selection(event):
    global selected_y_indices
    col_listbox.selection_clear(0, tk.END)
    for idx in selected_y_indices:
        col_listbox.selection_set(idx)

# Bind für X-Achsen-Auswahl
xaxis_combo.bind("<FocusIn>", save_y_selection)
xaxis_combo.bind("<<ComboboxSelected>>", restore_y_selection)

# --- Funktionen ---

show_grid = tk.BooleanVar(value=True)
mplcursor_active = tk.BooleanVar(value=True)
show_legend_var = tk.BooleanVar(value=True)
plot_mode = tk.StringVar(value="Linie")

def open_option_dialog():
    global show_grid, mplcursor_active, show_legend_var
    save_y_selection(None)  # aktuelle Auswahl sichern

    opt_win = tk.Toplevel(root)
    opt_win.title("Optionen")
    opt_win.geometry("320x210")

    grid_frame = tk.Frame(opt_win)
    grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Linke Spalte: Beschriftungen
    tk.Label(grid_frame, text="Netz:", anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    tk.Label(grid_frame, text="Zeige Werte:", anchor="w").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    tk.Label(grid_frame, text="Legende anzeigen:", anchor="w").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    tk.Label(grid_frame, text="Datenpunkte:", anchor="w").grid(row=3, column=0, sticky="w", padx=10, pady=5)

    def on_change(*args):
        restore_y_selection(None)

    # Rechte Spalte: Checkbuttons
    tk.Checkbutton(grid_frame, variable=show_grid).grid(row=0, column=1, sticky="w", padx=10, pady=5)
    tk.Checkbutton(grid_frame, variable=mplcursor_active).grid(row=1, column=1, sticky="w", padx=10, pady=5)
    tk.Checkbutton(grid_frame, variable=show_legend_var).grid(row=2, column=1, sticky="w", padx=10, pady=5)
    # tk.OptionMenu(grid_frame, plot_mode, "Linie", "Punkte", "Linie mit Punkten", "Kreuze").grid(row=3, column=1, sticky="w", padx=10, pady=5)
    # ttk.Combobox(grid_frame, textvariable=plot_mode, values=["Linie", "Punkte", "Linie mit Punkten", "Kreuze"], state="readonly", width=12).grid(row=3, column=1, sticky="w", padx=10, pady=5)
    # Combobox mit Bindung
    cb = ttk.Combobox(grid_frame, textvariable=plot_mode,
                      values=["Linie", "Punkte", "Linie mit Punkten", "Kreuze"],
                      state="readonly", width=12)
    cb.grid(row=3, column=1, sticky="w", padx=10, pady=5)
    cb.bind("<<ComboboxSelected>>", on_change)

    close_btn = tk.Button(opt_win, text="Schließen", command=opt_win.destroy)
    close_btn.pack(side=tk.BOTTOM, pady=10)

def detect_encoding(filepath, n_lines=10000):
    with open(filepath, 'rb') as f:
        rawdata = f.read(n_lines)
    result = chardet.detect(rawdata)
    return result['encoding']

def update_ui_visibility():
    if last_fileext == '.csv' or last_fileext == '.txt':
        # open_btn.pack(side=tk.LEFT, padx=5)
        delimiter_combo.pack(side=tk.RIGHT, padx=5)
        delimiter_label.pack(side=tk.RIGHT)
        xaxis_label.pack(side=tk.LEFT)
        xaxis_combo.pack(side=tk.LEFT, padx=5)
        opt_btn.pack(side=tk.RIGHT, padx=5)
        sheet_label.pack_forget()
        sheet_combo.pack_forget()
    elif last_fileext == '.lvm':
        # open_btn.pack(side=tk.TOP, padx=5)
        xaxis_label.pack(side=tk.LEFT)
        xaxis_combo.pack(side=tk.LEFT, padx=5)
        opt_btn.pack(side=tk.RIGHT, padx=5)
        delimiter_label.pack_forget()
        delimiter_combo.pack_forget()
        sheet_label.pack_forget()
        sheet_combo.pack_forget()
    elif last_fileext in ['.xlsx', '.xls']:
        # open_btn.pack(side=tk.LEFT, padx=5)
        sheet_combo.pack(side=tk.RIGHT, padx=15)
        sheet_label.pack(side=tk.RIGHT)
        xaxis_label.pack(side=tk.LEFT)
        xaxis_combo.pack(side=tk.LEFT, padx=5)
        opt_btn.pack(side=tk.RIGHT, padx=5)
        delimiter_label.pack_forget()
        delimiter_combo.pack_forget()
    else:
        # open_btn.pack(side=tk.TOP, padx=5)
        xaxis_label.pack_forget()
        xaxis_combo.pack_forget()
        opt_btn.pack_forget()
        delimiter_label.pack_forget()
        delimiter_combo.pack_forget()
        sheet_label.pack_forget()
        sheet_combo.pack_forget()

def load_data(filepath=None):
    global df, last_filepath, last_fileext, available_sheets
    if filepath:
        last_filepath = filepath
        root.title("DataPlot" + " (" + os.path.basename(last_filepath) + ")")

    if not last_filepath:
        return

    try:
        ext = os.path.splitext(last_filepath)[1].lower()
        last_fileext = ext
        encoding = detect_encoding(last_filepath)
        delimiter = delimiter_var.get()
        update_ui_visibility()

        if ext == '.csv' or ext == '.txt':
            df = pd.read_csv(last_filepath, sep=delimiter, encoding=encoding, quotechar='"', on_bad_lines='warn')

        elif ext == '.lvm':
            df = pd.read_csv(last_filepath, sep='	', encoding=encoding, quotechar='"', on_bad_lines='warn')

        elif ext in ['.xlsx', '.xls']:
            available_sheets = pd.ExcelFile(last_filepath).sheet_names
            sheet_combo['values'] = available_sheets
            sheet_var.set(available_sheets[0])
            df = pd.read_excel(last_filepath, sheet_name=available_sheets[0], engine='openpyxl')

        else:
            messagebox.showerror("Dateifehler", f"Dateiformat {ext} wird nicht unterstützt.")
            return

        process_loaded_dataframe()

    except Exception as e:
        messagebox.showerror("Ladefehler", str(e))

def load_excel_sheet():
    global df
    try:
        selected_sheet = sheet_var.get()
        df = pd.read_excel(last_filepath, sheet_name=selected_sheet) #, engine='openpyxl')
        process_loaded_dataframe()
    except Exception as e:
        messagebox.showerror("Excel-Ladefehler", str(e))

def process_loaded_dataframe():
    global col_listbox_values
    col_listbox.delete(0, tk.END)
    col_listbox_values.clear()

    # Konvertiere Stringspalten mit Komma-Dezimaltrennung in float
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

    non_empty_cols = []
    for col in df.columns:
        if df[col].notna().any():
            col_listbox.insert(tk.END, col)
            col_listbox_values.append(col)
            non_empty_cols.append(col)
        else:
            col_listbox.insert(tk.END, f"{col} [NaN]")
            col_listbox_values.append(col)

    xaxis_combo['values'] = ["[Index verwenden]"] + non_empty_cols
    xaxis_var.set("[Index verwenden]")


def on_delimiter_change(event):
    if last_filepath:
        load_data()

def open_file():
    filepath = filedialog.askopenfilename(
        filetypes=[("Daten-Dateien", "*.csv *.txt *.xlsx *.xls *.lvm"), ("Alle Dateien", "*.*")]
    )
    if filepath:
        load_data(filepath)

def plot_columns():
    if df is None:
        messagebox.showerror("Fehler", "Keine Datei geladen.")
        return

    selected = col_listbox.curselection()
    if not selected:
        messagebox.showinfo("Hinweis", "Bitte Spalten zum Plotten auswählen.")
        return

    selected_cols = [col_listbox_values[i] for i in selected]
    numeric_cols = [col for col in selected_cols if np.issubdtype(df[col].dtype, np.number)]

    if not numeric_cols:
        messagebox.showerror("Fehler", "Keine numerischen Spalten ausgewählt.")
        return

    x_col = xaxis_var.get()
    use_index = (x_col == "[Index verwenden]" or x_col not in df.columns)

    try:
        plt.figure(figsize=(8, 5))
        # style = plot_style_var.get()

        for col in numeric_cols:
            y = df[col].dropna()
            if use_index:
                x = y.index
            else:
                if not np.issubdtype(df[x_col].dtype, np.number) and not np.issubdtype(df[x_col].dtype, np.datetime64):
                    continue  # Ungültige X-Achse
                x = df.loc[y.index, x_col]  # Stelle sicher, dass Index passt

            if plot_mode.get() == "Linie":
                plt.plot(x, y, "-", label=col)
            elif plot_mode.get() == "Punkte":
                plt.plot(x, y, 'o', label=col)
            elif plot_mode.get() == "Linie mit Punkten":
                plt.plot(x, y, 'o-', label=col)
            elif plot_mode.get() == "Kreuze":
                plt.plot(x, y, 'x', label=col)

        title_y = ", ".join(numeric_cols)
        title_x = x_col if not use_index else "Index"
        plt.xlabel(title_x)
        # plt.ylabel("Werte")
        plt.title(f"{title_y} über {title_x}")
        plt.grid(show_grid.get())

        if not show_legend_var.get() or len(numeric_cols) <= 1:
            plt.legend().set_visible(False)
        else:
            plt.legend()
        plt.tight_layout()
        mplcursors.cursor(hover=mplcursor_active.get())
        plt.show()

    except Exception as e:
        messagebox.showerror("Plot-Fehler", str(e))


def show_columns():
    if df is None:
        messagebox.showerror("Fehler", "Keine Datei geladen.")
        return

    selected = col_listbox.curselection()
    if not selected:
        messagebox.showinfo("Hinweis", "Bitte Spalten zum Anzeigen auswählen.")
        return

    # Echte Spaltennamen holen
    selected_cols = [col_listbox_values[i] for i in selected]
    sub_df = df[selected_cols].copy()

    # Indexspalte "Idx" hinzufügen (1-basiert, nur ganze Zahlen)
    sub_df.insert(0, "Idx", range(1, len(sub_df) + 1))

    # Neues Fenster erzeugen
    view_win = tk.Toplevel(root)
    view_win.title("Ausgewählte Spalten")

    # Treeview-Widget vorbereiten
    columns = ["Idx"] + selected_cols
    tree = ttk.Treeview(
        view_win,
        columns=columns,
        show='headings',
    )
    tree.pack(fill=tk.BOTH, expand=True)

    # Spaltenüberschriften und Format
    for col in columns:
        tree.heading(col, text=col)
        if col == "Idx":
            tree.column(col, width=50, anchor="center")  # Schmalere Indexspalte
        else:
            tree.column(col, width=100, anchor="center")

    # Daten einfügen (max. 1000 Zeilen zur Sicherheit)
    max_rows = 1000
    for idx, row in sub_df.iterrows():
        values = [int(row["Idx"])] + [row[col] for col in selected_cols]
        tree.insert('', tk.END, values=values)
        if idx >= max_rows:
            break

# Bind Delimiter-Auswahl
delimiter_combo.bind("<<ComboboxSelected>>", on_delimiter_change)

# Starte GUI
root.mainloop()
