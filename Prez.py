import os
import re
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class PrezGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Générateur de Prez BBCode - TMDb Edition")
        self.root.geometry("900x900")

        # Clé par défaut (optionnelle)
        self.default_api_key = "Votre clé API"
        self.setup_ui()

    def setup_ui(self):
        file_frame = ttk.LabelFrame(self.root, text=" 1. Sélection du fichier ", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(file_frame, text="Parcourir", command=self.browse_file).pack(side="right")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_general = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_general, text="Général (API)")
        self.tab_release = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_release, text="Technique (Fichier)")
        self.tab_bbcode = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_bbcode, text="Résultat BBCode")

        self.setup_tab_general()
        self.setup_tab_release()
        self.setup_tab_bbcode()

    def setup_tab_general(self)
        api_frame = ttk.Frame(self.tab_general)
        api_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(api_frame, text="Clé API TMDb :", font=("Arial", 9, "bold")).pack(side="left")
        self.api_key_var = tk.StringVar(value=self.default_api_key)
        self.api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=45)
        self.api_entry.pack(side="left", padx=5)

        self.btn_show_api = ttk.Button(api_frame, text="👁", width=3, command=self.toggle_api_visibility)
        self.btn_show_api.pack(side="left")

        ttk.Separator(self.tab_general, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)

        self.api_vars = {
            "Titre": tk.StringVar(), "Titre Original": tk.StringVar(), "Année": tk.StringVar(),
            "Réalisateur": tk.StringVar(), "Acteurs": tk.StringVar(), "Genres": tk.StringVar(),
            "Durée": tk.StringVar(), "Note": tk.StringVar(), "Lien TMDb": tk.StringVar(), "Poster": tk.StringVar()
        }

        for i, (label, var) in enumerate(self.api_vars.items()):
            if label == "Poster": continue
            ttk.Label(self.tab_general, text=f"{label} :").grid(row=i+2, column=0, sticky="w", pady=3)
            ttk.Entry(self.tab_general, textvariable=var, width=70).grid(row=i+2, column=1, padx=10, pady=3)

        ttk.Label(self.tab_general, text="Synopsis :").grid(row=11, column=0, sticky="nw", pady=3)
        self.synopsis_text = tk.Text(self.tab_general, height=8, width=52, font=("Arial", 9))
        self.synopsis_text.grid(row=11, column=1, padx=10, pady=3)

        ttk.Button(self.tab_general, text="🔍 RÉCUPÉRER & GÉNÉRER LE BBCODE", command=self.fetch_tmdb_data).grid(row=12, column=0, columnspan=2, pady=15)

    def toggle_api_visibility(self):
        if self.api_entry.cget('show') == '*':
            self.api_entry.config(show='')
        else:
            self.api_entry.config(show='*')

    def setup_tab_release(self):
        self.rel_vars = {
            "Source": tk.StringVar(), "Codec": tk.StringVar(), "Langue": tk.StringVar(),
            "Team": tk.StringVar(), "Resolution": tk.StringVar()
        }
        self.is_multi = tk.BooleanVar()
        for i, (name, var) in enumerate(self.rel_vars.items()):
            ttk.Label(self.tab_release, text=f"{name} :").grid(row=i, column=0, sticky="w", pady=5)
            ttk.Entry(self.tab_release, textvariable=var, width=40).grid(row=i, column=1, padx=10, pady=5)
        ttk.Checkbutton(self.tab_release, text="Option MULTi (FR/EN)", variable=self.is_multi).grid(row=5, column=1, sticky="w", pady=10)

    def setup_tab_bbcode(self):
        self.output_text = tk.Text(self.tab_bbcode, font=("Consolas", 10), bg="#f8f9fa")
        self.output_text.pack(fill="both", expand=True)
        ttk.Button(self.tab_bbcode, text="Copier le BBCode", command=self.copy_to_clipboard).pack(pady=10)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Video files", "*.mkv *.mp4 *.avi")])
        if filename:
            base = os.path.basename(filename)
            self.file_path.set(filename)
            self.auto_detect(base)

    def auto_detect(self, filename):
        fn = filename.upper()
        year_match = re.search(r'[\. \((](19\d{2}|20\d{2})[\. \))]', filename)
        if year_match:
            self.api_vars["Année"].set(year_match.group(1))
            self.api_vars["Titre"].set(filename[:year_match.start()].replace('.', ' ').strip().title())
        else:
            self.api_vars["Titre"].set(os.path.splitext(filename)[0].replace('.', ' ').strip().title())

        if "VOSTFR" in fn:
            self.rel_vars["Langue"].set("VOSTFR")
        elif "MULTI" in fn:
            self.rel_vars["Langue"].set("MULTi (VFF/EN)")
        else:
            self.rel_vars["Langue"].set("FRENCH")

        self.is_multi.set("MULTI" in fn)
        source_m = re.search(r"(BD-?RIP|BR-?RIP|BLURAY|WEB-?DL|WEB|HDTV|DVD)", fn)
        self.rel_vars["Source"].set(source_m.group(0) if source_m else "BluRay")
        codec_m = re.search(r"(X264|X265|H264|H265|HEVC|XVID)", fn)
        self.rel_vars["Codec"].set(codec_m.group(0).lower() if codec_m else "x264")
        res_m = re.search(r"(720P|1080P|2160P|4K)", fn)
        self.rel_vars["Resolution"].set(res_m.group(0).lower() if res_m else "1080p")

        if "-" in filename:
            team = filename.split("-")[-1].split('.')[0].strip()
            self.rel_vars["Team"].set(team)
        else:
            self.rel_vars["Team"].set("UNKNOWN")

    def fetch_tmdb_data(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Erreur", "Veuillez saisir une clé API TMDb.")
            return

        title = self.api_vars["Titre"].get()
        year = self.api_vars["Année"].get()
        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title}&year={year}&language=fr-FR"
        try:
            res = requests.get(url).json()
            if res.get('results'):
                m_id = res['results'][0]['id']
                data = requests.get(f"https://api.themoviedb.org/3/movie/{m_id}?api_key={api_key}&language=fr-FR&append_to_response=credits").json()
                self.fill_ui_from_api(data)
                self.generate_bbcode()
                self.notebook.select(2)
            else:
                messagebox.showwarning("TMDb", "Film non trouvé.")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def fill_ui_from_api(self, data):
        self.api_vars["Titre"].set(data.get('title', ''))
        self.api_vars["Titre Original"].set(data.get('original_title', ''))
        self.api_vars["Année"].set(data.get('release_date', '')[:4])
        self.api_vars["Durée"].set(f"{data.get('runtime', '?')} minutes")
        self.api_vars["Note"].set(f"{data.get('vote_average', '0')}/10")
        self.api_vars["Lien TMDb"].set(f"https://www.themoviedb.org/movie/{data.get('id')}")
        self.api_vars["Genres"].set(", ".join([g['name'] for g in data.get('genres', [])]))
        crew = data.get('credits', {}).get('crew', [])
        self.api_vars["Réalisateur"].set(next((m['name'] for m in crew if m['job'] == 'Director'), "Inconnu"))
        cast = data.get('credits', {}).get('cast', [])
        self.api_vars["Acteurs"].set(", ".join([a['name'] for a in cast[:5]]))
        self.api_vars["Poster"].set(f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}")
        self.synopsis_text.delete(1.0, tk.END)
        self.synopsis_text.insert(tk.END, data.get('overview', ''))

    def generate_bbcode(self):
        multi = " [b][color=#FF0000][MULTi][/color][/b]" if self.is_multi.get() else ""
        bbcode = f"""[center]
[img]{self.api_vars['Poster'].get()}[/img]

[b][size=22]{self.api_vars['Titre'].get().upper()}{multi}[/size][/b]
[b][i]{self.api_vars['Titre Original'].get()} ({self.api_vars['Année'].get()})[/i][/b]

[b]Réalisateur :[/b] {self.api_vars['Réalisateur'].get()}
[b]Acteurs :[/b] {self.api_vars['Acteurs'].get()}
[b]Genre :[/b] {self.api_vars['Genres'].get()}
[b]Durée :[/b] {self.api_vars['Durée'].get()}
[b]Note :[/b] {self.api_vars['Note'].get()}

[quote][b]Synopsis :[/b]
{self.synopsis_text.get(1.0, tk.END).strip()}[/quote]

[b][color=#0000ff]Infos Release[/color][/b]
[b]Source :[/b] {self.rel_vars['Source'].get()}
[b]Qualité :[/b] {self.rel_vars['Resolution'].get()}
[b]Codec :[/b] {self.rel_vars['Codec'].get()}
[b]Langue :[/b] {self.rel_vars['Langue'].get()}
[b]Team :[/b] {self.rel_vars['Team'].get()}

[b]Lien TMDb :[/b] [url]{self.api_vars['Lien TMDb'].get()}[/url]
[/center]"""
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, bbcode.strip())

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output_text.get(1.0, tk.END).strip())
        messagebox.showinfo("Succès", "BBCode copié !")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrezGenerator(root)
    root.mainloop()
