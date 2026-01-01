import os
import re
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class PrezGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Générateur de Prez BBCode - TMDb Edition")
        self.root.geometry("850x950")

        # /!\ REMPLACEZ PAR VOTRE CLÉ API TMDB VALIDE /!\
        self.api_key = "Clé API"

        self.setup_ui()

    def setup_ui(self):
        file_frame = ttk.LabelFrame(self.root, text=" 1. Sélection du fichier ", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(file_frame, text="Parcourir", command=self.browse_file).pack(side="right")

        info_frame = ttk.LabelFrame(self.root, text=" 2. Informations détectées & Manuel ", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)

        labels = ["Titre", "Année", "Langue", "Source", "Codec", "Team"]
        self.vars = {name: tk.StringVar() for name in labels}
        self.is_multi = tk.BooleanVar()

        for i, name in enumerate(labels):
            ttk.Label(info_frame, text=f"{name} :").grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(info_frame, textvariable=self.vars[name], width=50).grid(row=i, column=1, padx=5, pady=2, columnspan=2)

        ttk.Label(info_frame, text="ID ou Lien TMDb :", font=("Arial", 9, "bold")).grid(row=6, column=0, sticky="w", pady=10)
        self.manual_tmdb = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.manual_tmdb, width=50).grid(row=6, column=1, padx=5, pady=10, columnspan=2)

        ttk.Checkbutton(info_frame, text="MULTi (FR/EN)", variable=self.is_multi).grid(row=7, column=1, sticky="w", pady=5)

        btn_search = ttk.Button(info_frame, text="🔍 GÉNÉRER LA PRÉSENTATION", command=self.fetch_tmdb_data)
        btn_search.grid(row=8, column=1, pady=15, sticky="we")

        res_frame = ttk.LabelFrame(self.root, text=" 3. Résultat BBCode ", padding=10)
        res_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.output_text = tk.Text(res_frame, height=15, font=("Consolas", 10))
        self.output_text.pack(fill="both", expand=True)
        ttk.Button(res_frame, text="Copier le BBCode", command=self.copy_to_clipboard).pack(pady=5)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Video files", "*.mkv *.mp4 *.avi")])
        if filename:
            self.file_path.set(filename)
            self.auto_detect(os.path.basename(filename))

    def auto_detect(self, filename):
        name_no_ext = os.path.splitext(filename)[0]

        if "-" in name_no_ext:
            self.vars["Team"].set(name_no_ext.split("-")[-1].strip())
        else:
            self.vars["Team"].set("UNKNOWN")

        year_match = re.search(r'[\. \((](19\d{2}|20\d{2})[\. \)) warehouse]', filename)
        year = ""
        after_year_text = ""

        if year_match:
            year = year_match.group(1)
            after_year_text = filename[year_match.end():]
            title_raw = filename[:year_match.start()]
        else:
            after_year_text = filename
            title_raw = name_no_ext

        self.vars["Année"].set(year)

        lang_pattern = r"(MULTI|FRENCH|FR|VOSTFR|VO|FRA|ENGLISH|ENG)"
        lang_match = re.search(lang_pattern, after_year_text, re.I)
        detected_lang = lang_match.group(0).upper() if lang_match else "FRENCH"
        self.vars["Langue"].set(detected_lang)

        source_match = re.search(r"(BDRip|BRRip|BluRay|Web|HDTV|WEB-DL|DVD|R5)", filename, re.I)
        self.vars["Source"].set(source_match.group(0) if source_match else "BluRay")

        codec_match = re.search(r"(x264|x265|h264|h265|hevc|xvid|av1)", filename, re.I)
        self.vars["Codec"].set(codec_match.group(0).lower() if codec_match else "x264")

        is_multi_detected = bool(re.search(r"(MULTI)", after_year_text, re.I))
        self.is_multi.set(is_multi_detected)

        title_clean = title_raw.replace('.', ' ').replace('_', ' ').strip()
        title_clean = re.sub(r'[\[\{].*?[\}\]]', '', title_clean).strip()

        self.vars["Titre"].set(title_clean.title())

    def fetch_tmdb_data(self):
        manual_val = self.manual_tmdb.get().strip()
        movie_id = None
        try:
            if manual_val:
                if "themoviedb.org" in manual_val:
                    id_match = re.search(r"/movie/(\d+)", manual_val)
                    movie_id = id_match.group(1) if id_match else None
                elif manual_val.startswith("tt"):
                    find_url = f"https://api.themoviedb.org/3/find/{manual_val}?api_key={self.api_key}&language=fr-FR&external_source=imdb_id"
                    find_res = requests.get(find_url).json()
                    movie_id = find_res.get('movie_results')[0]['id'] if find_res.get('movie_results') else None
                else:
                    movie_id = manual_val

            if not movie_id:
                title = self.vars["Titre"].get()
                year = self.vars["Année"].get()
                search_url = f"https://api.themoviedb.org/3/search/movie?api_key={self.api_key}&query={title}&year={year}&language=fr-FR"
                search_res = requests.get(search_url).json()
                if not search_res.get('results'):
                    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={self.api_key}&query={title}&language=fr-FR"
                    search_res = requests.get(search_url).json()

                if search_res.get('results'):
                    movie_id = search_res['results'][0]['id']
                else:
                    messagebox.showerror("Introuvable", f"Film non trouvé : {title}")
                    return

            detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={self.api_key}&language=fr-FR&append_to_response=credits"
            response = requests.get(detail_url)
            movie_data = response.json()
            self.generate_bbcode(movie_data)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur : {str(e)}")

    def generate_bbcode(self, data):
        multi_tag = " [b][color=#ff0000]MULTi[/color][/b]" if self.is_multi.get() else ""
        director = next((m['name'] for m in data.get('credits', {}).get('crew', []) if m['job'] == 'Director'), "Inconnu")
        actors = ", ".join([a['name'] for a in data.get('credits', {}).get('cast', [])[:5]])
        poster_path = data.get('poster_path')
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""

        bbcode = f"""[center]
[img]{poster_url}[/img]

[b][size=20]{data.get('title')} ({data.get('release_date', '0000')[:4]})[/size][/b]
{multi_tag}

[b]Genre :[/b] {", ".join([g['name'] for g in data.get('genres', [])])}
[b]Réalisateur :[/b] {director}
[b]Acteurs :[/b] {actors}
[b]Note :[/b] {data.get('vote_average')}/10

[quote][b]Synopsis :[/b]
{data.get('overview', 'Aucun synopsis disponible.')}[/quote]

[b][color=#0000ff]Infos Release[/color][/b]
[b]Langue :[/b] {self.vars['Langue'].get()}
[b]Source :[/b] {self.vars['Source'].get()}
[b]Codec :[/b] {self.vars['Codec'].get()}
[b]Team :[/b] {self.vars['Team'].get()}
[/center]"""
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, bbcode.strip())

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output_text.get(1.0, tk.END))
        messagebox.showinfo("Succès", "BBCode copié !")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrezGenerator(root)
    root.mainloop()
