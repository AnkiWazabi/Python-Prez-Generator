import os
import re
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pymediainfo import MediaInfo

class PrezGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Générateur de Prez BBCode - TMDb & MediaInfo Pro")
        self.root.geometry("950x950")

        # Clé par défaut
        self.default_api_key = "4c22b77c619730b090a06963a508f4db"

        self.audio_tracks = []
        self.setup_ui()

    def get_full_language_name(self, code):
        """Convertit les codes ISO en noms complets français"""
        languages = {
            'fr': 'Français (TrueFrench)', 'fre': 'Français (TrueFrench)', 'fra': 'Français (TrueFrench)',
            'en': 'Anglais', 'eng': 'Anglais',
            'es': 'Espagnol', 'spa': 'Espagnol',
            'it': 'Italien', 'ita': 'Italien',
            'de': 'Allemand', 'ger': 'Allemand', 'deu': 'Allemand',
            'ja': 'Japonais', 'jpn': 'Japonais',
            'ru': 'Russe', 'rus': 'Russe',
            'ko': 'Coréen', 'kor': 'Coréen',
            'fr.ca': 'Français Canadien', 'fr-ca': 'Français Canadien'
        }
        return languages.get(code.lower(), code.title())

    def setup_ui(self):
        # 1. Sélection du fichier
        file_frame = ttk.LabelFrame(self.root, text=" 1. Sélection du fichier ", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(file_frame, text="Parcourir", command=self.browse_file).pack(side="right")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglets principaux
        self.tab_general = ttk.Frame(self.notebook, padding=10)
        self.tab_release = ttk.Frame(self.notebook, padding=10)
        self.tab_bbcode = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_general, text="Général (API)")
        self.notebook.add(self.tab_release, text="Technique (MediaInfo)")
        self.notebook.add(self.tab_bbcode, text="Résultat BBCode")

        self.setup_tab_general()
        self.setup_tab_release()
        self.setup_tab_bbcode()

    def setup_tab_general(self):
        # Zone Clé API
        api_frame = ttk.Frame(self.tab_general)
        api_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(api_frame, text="Clé API TMDb :", font=("Arial", 9, "bold")).pack(side="left")
        self.api_key_var = tk.StringVar(value=self.default_api_key)
        self.api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=45)
        self.api_entry.pack(side="left", padx=5)
        ttk.Button(api_frame, text="👁", width=3, command=self.toggle_api_visibility).pack(side="left")

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

    def setup_tab_release(self):
        video_frame = ttk.LabelFrame(self.tab_release, text=" Vidéo ", padding=10)
        video_frame.pack(fill="x", pady=5)
        self.video_vars = {
            "Qualité": tk.StringVar(), "Source": tk.StringVar(),
            "Format": tk.StringVar(), "Codec": tk.StringVar(),
            "Bitrate (kbps)": tk.StringVar(), "HDR": tk.StringVar()
        }
        for i, (name, var) in enumerate(self.video_vars.items()):
            ttk.Label(video_frame, text=f"{name} :").grid(row=i, column=0, sticky="w")
            ttk.Entry(video_frame, textvariable=var, width=35).grid(row=i, column=1, padx=10, pady=2)

        self.team_var = tk.StringVar()
        ttk.Label(video_frame, text="Team :").grid(row=6, column=0, sticky="w")
        ttk.Entry(video_frame, textvariable=self.team_var, width=35).grid(row=6, column=1, padx=10, pady=2)

        audio_container = ttk.LabelFrame(self.tab_release, text=" Audio ", padding=10)
        audio_container.pack(fill="both", expand=True, pady=10)
        btn_frame = ttk.Frame(audio_container)
        btn_frame.pack(anchor="e")
        ttk.Button(btn_frame, text="+ Ajouter Piste", command=self.add_audio_track_manual).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="✖ Supprimer Dernière", command=self.remove_audio_track).pack(side="left", padx=2)
        self.audio_notebook = ttk.Notebook(audio_container)
        self.audio_notebook.pack(fill="both", expand=True, pady=5)

    def setup_tab_bbcode(self):
        self.output_text = tk.Text(self.tab_bbcode, font=("Consolas", 10), bg="#f8f9fa")
        self.output_text.pack(fill="both", expand=True)
        ttk.Button(self.tab_bbcode, text="Copier le BBCode", command=self.copy_to_clipboard).pack(pady=10)

    def toggle_api_visibility(self):
        self.api_entry.config(show='' if self.api_entry.cget('show') == '*' else '*')

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Video files", "*.mkv *.mp4 *.avi")])
        if filename:
            self.file_path.set(filename)
            self.analyze_file(filename)

    def analyze_file(self, filepath):
        try:
            media_info = MediaInfo.parse(filepath)
            codec_map = {"AVC": "h264 (AVC)", "HEVC": "h265 (HEVC)", "AC-3": "AC3", "E-AC-3": "E-AC3", "DTS XLL": "DTS-HD MA", "MPEG Audio": "MP3"}
            channel_map = {"6": "5.1", "8": "7.1", "2": "2.0", "1": "1.0"}

            for track in self.audio_tracks:
                track["frame_ref"].destroy()
            self.audio_tracks = []

            video_track = next((t for t in media_info.tracks if t.track_type == 'Video'), None)
            gen_track = next((t for t in media_info.tracks if t.track_type == 'General'), None)

            # --- ANALYSE VIDÉO ---
            if video_track:
                # Logique HDR détaillée
                hdr_f = video_track.hdr_format or ""
                transfer = video_track.transfer_characteristics or ""
                if "Dolby Vision" in hdr_f:
                    res_hdr = "Dolby Vision" + (" / HDR10" if "HDR10" in hdr_f else "")
                elif "HDR10" in hdr_f or "SMPTE ST 2084" in transfer or "PQ" in transfer:
                    res_hdr = "HDR10"
                elif "HLG" in transfer or "arib std-b67" in transfer.lower():
                    res_hdr = "HLG"
                else:
                    res_hdr = "SDR (Standard Range)"
                self.video_vars["HDR"].set(res_hdr)

                w = int(video_track.width)
                h = int(video_track.height)
                if w >= 3400 or h >= 1944:#J'ai retiré 10% dans chaque seuil pour ceux qui s'amusent a retirer 2px en hauteur
                    q = "2160p (4K)"
                elif w >= 1728 or h >= 972:
                    q = "1080p"
                elif w >= 1152 or h >= 648:
                    q = "720p"
                else:
                    q = "SD"

                self.video_vars["Qualité"].set(f"{q} ({w}x{h})")
                self.video_vars["Codec"].set(codec_map.get(video_track.format, video_track.format))
                self.video_vars["Bitrate (kbps)"].set(int(video_track.bit_rate / 1000) if video_track.bit_rate else "Variable")

            # --- SOURCE & TEAM ---
            filename = os.path.basename(filepath)
            fn_upper = filename.upper()

            if gen_track:
                self.video_vars["Format"].set(gen_track.format)

            # Détection Source intelligente
            if any(x in fn_upper for x in ["BLURAY", "BD-RIP", "BDRIP", "BRRIP"]):
                self.video_vars["Source"].set("BluRay")
            elif any(x in fn_upper for x in ["WEB-DL", "WEBDL", "WEB.DL", "AMZN", "NF.WEB","WEB"]):
                self.video_vars["Source"].set("WEB-DL")
            elif "HDTV" in fn_upper:
                self.video_vars["Source"].set("HDTV")
            elif any(x in fn_upper for x in ["WEB-RIP", "WEBRIP", "WEB.RIP"]):
                self.video_vars["Source"].set("WEB-RIP")
            else:
                self.video_vars["Source"].set("")

            # Team : uniquement via nom de fichier (après le dernier tiret)
            name_no_ext = os.path.splitext(filename)[0]
            parts = name_no_ext.split("-")
            self.team_var.set(parts[-1].strip() if len(parts) > 1 else "UNKNOWN")

            # --- ANALYSE AUDIO ---
            for track in media_info.tracks:
                if track.track_type == 'Audio':
                    lang_raw = track.language or "fr"
                    lang_full = self.get_full_language_name(lang_raw)
                    channels = channel_map.get(str(track.channel_s), str(track.channel_s))
                    codec = codec_map.get(track.format, track.format)
                    bitrate = int(track.bit_rate / 1000) if track.bit_rate else "Variable"
                    self.add_audio_track_auto(lang_full, channels, codec, bitrate)

            # --- TITRE / ANNEE ---
            year_match = re.search(r'[\. \((](19\d{2}|20\d{2})[\. \))]', filename)
            if year_match:
                self.api_vars["Année"].set(year_match.group(1))
                self.api_vars["Titre"].set(filename[:year_match.start()].replace('.', ' ').strip().title())
            else:
                self.api_vars["Titre"].set(os.path.splitext(filename)[0].replace('.', ' ').strip().title())

        except Exception as e: messagebox.showerror("Erreur MediaInfo", str(e))

    def add_audio_track_auto(self, lang, channels, codec, bitrate):
        num = len(self.audio_tracks) + 1
        frame = ttk.Frame(self.audio_notebook, padding=10)
        self.audio_notebook.add(frame, text=f"Piste {num}")
        vars = {"Langue": tk.StringVar(value=lang), "Pistes (Canaux)": tk.StringVar(value=channels), "Codec": tk.StringVar(value=codec), "Bitrate (kbps)": tk.StringVar(value=bitrate), "frame_ref": frame}
        for i, (name, var) in enumerate(list(vars.items())[:-1]):
            ttk.Label(frame, text=f"{name} :").grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(frame, textvariable=var, width=40).grid(row=i, column=1, padx=10, pady=2)
        self.audio_tracks.append(vars)

    def add_audio_track_manual(self): self.add_audio_track_auto("Français", "5.1", "AC3", "640")

    def remove_audio_track(self):
        if len(self.audio_tracks) > 1:
            last = self.audio_tracks.pop()
            last["frame_ref"].destroy()

    def fetch_tmdb_data(self):
        api_key = self.api_key_var.get().strip()
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
            else: messagebox.showwarning("TMDb", "Aucun résultat trouvé.")
        except Exception as e: messagebox.showerror("Erreur", str(e))

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
        self.api_vars["Acteurs"].set(", ".join([a['name'] for a in data.get('credits', {}).get('cast', [])[:5]]))
        self.api_vars["Poster"].set(f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}")
        self.synopsis_text.delete(1.0, tk.END)
        self.synopsis_text.insert(tk.END, data.get('overview', ''))

    def generate_bbcode(self):
        hdr_val = self.video_vars['HDR'].get()
        hdr_tag = ""
        if "Dolby Vision" in hdr_val:
            hdr_tag = " [b][color=#CC00CC][DOLBY ViSiON][/color][/b]"
        elif "HDR" in hdr_val or "HLG" in hdr_val:
            hdr_tag = " [b][color=#FF8000][HDR][/color][/b]"

        audio_bbcode = ""
        for i, track in enumerate(self.audio_tracks):
            audio_bbcode += f"[b]Piste Audio {i+1} :[/b] {track['Langue'].get()} | {track['Codec'].get()} ({track['Pistes (Canaux)'].get()}) @ {track['Bitrate (kbps)'].get()} kbps\n"

        bbcode = f"""[center]
[img]{self.api_vars['Poster'].get()}[/img]

[b][size=22]{self.api_vars['Titre'].get().upper()}{hdr_tag}[/size][/b]
[b][i]{self.api_vars['Titre Original'].get()} ({self.api_vars['Année'].get()})[/i][/b]

[b]Réalisateur :[/b] {self.api_vars['Réalisateur'].get()}
[b]Acteurs :[/b] {self.api_vars['Acteurs'].get()}
[b]Genre :[/b] {self.api_vars['Genres'].get()}
[b]Durée :[/b] {self.api_vars['Durée'].get()}
[b]Note :[/b] {self.api_vars['Note'].get()}

[quote][b]Synopsis :[/b]
{self.synopsis_text.get(1.0, tk.END).strip()}[/quote]

[b][color=#0000ff]INFOS VIDÉO[/color][/b]
[b]Qualité :[/b] {self.video_vars['Qualité'].get()} | [b]Source :[/b] {self.video_vars['Source'].get()}
[b]Format :[/b] {self.video_vars['Format'].get()} | [b]Codec :[/b] {self.video_vars['Codec'].get()}
[b]Bitrate :[/b] {self.video_vars['Bitrate (kbps)'].get()} kbps | [b]HDR :[/b] {hdr_val}

[b][color=#0000ff]INFOS AUDIO[/color][/b]
{audio_bbcode}
[b]Team :[/b] {self.team_var.get()}
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
