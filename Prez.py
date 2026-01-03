import os
import re
import requests
import zlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pymediainfo import MediaInfo

class PrezGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Prez Generator")
        self.root.geometry("950x980")

        self.default_api_key = ""
        self.audio_tracks = []
        self.sub_tracks = []
        self.setup_ui()

    def calculate_crc32(self, filepath):
        try:
            crc = 0
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data: break
                    crc = zlib.crc32(data, crc)
            return "%08X" % (crc & 0xFFFFFFFF)
        except Exception as e:
            return "Erreur"

    def get_full_language_name(self, code):
        languages = {
            'fr': 'Français', 'fre': 'Français', 'fra': 'Français',
            'en': 'Anglais', 'eng': 'Anglais',
            'es': 'Espagnol', 'spa': 'Espagnol',
            'it': 'Italien', 'ita': 'Italien',
            'de': 'Allemand', 'ger': 'Allemand', 'deu': 'Allemand',
            'ja': 'Japonais', 'jpn': 'Japonais',
            'ru': 'Russe', 'rus': 'Russe',
            'ko': 'Coréen', 'kor': 'Coréen',
            'fr.ca': 'Français Canadien', 'fr-ca': 'Français Canadien'
        }
        if not code: return "Inconnue"
        clean_code = code.split('/')[0].strip().lower()
        return languages.get(clean_code, clean_code.title())

    def setup_ui(self):
        file_frame = ttk.LabelFrame(self.root, text=" 1. Sélection du fichier ", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(file_frame, text="Parcourir", command=self.browse_file).pack(side="right")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

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

        btn_frame = ttk.Frame(self.tab_general)
        btn_frame.grid(row=12, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="🔍 RÉCUPÉRER DEPUIS TMDB", width=30, command=self.fetch_tmdb_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⚙️ GÉNÉRER LE BBCODE", width=30, command=self.generate_bbcode).pack(side="left", padx=5)

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

        self.use_crc32 = tk.BooleanVar(value=False)
        ttk.Checkbutton(video_frame, text="Inclure le CRC32 (Calculé à la génération)", variable=self.use_crc32).grid(row=7, column=1, sticky="w", pady=5)

        container = ttk.Frame(self.tab_release)
        container.pack(fill="both", expand=True)

        audio_container = ttk.LabelFrame(container, text=" Audio ", padding=10)
        audio_container.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        btn_a = ttk.Frame(audio_container)
        btn_a.pack(anchor="e")
        ttk.Button(btn_a, text="+", width=3, command=self.add_audio_track_manual).pack(side="left")
        ttk.Button(btn_a, text="✖", width=3, command=self.remove_audio_track).pack(side="left")
        self.audio_notebook = ttk.Notebook(audio_container)
        self.audio_notebook.pack(fill="both", expand=True)

        sub_container = ttk.LabelFrame(container, text=" Sous-titres ", padding=10)
        sub_container.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        btn_s = ttk.Frame(sub_container)
        btn_s.pack(anchor="e")
        ttk.Button(btn_s, text="+", width=3, command=self.add_sub_track_manual).pack(side="left")
        ttk.Button(btn_s, text="✖", width=3, command=self.remove_sub_track).pack(side="left")
        self.sub_notebook = ttk.Notebook(sub_container)
        self.sub_notebook.pack(fill="both", expand=True)

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
            sub_format_map = {"UTF-8": "SRT", "SSA": "ASS", "ASS": "ASS", "PGS": "PGS", "VobSub": "VobSub"}

            for track in self.audio_tracks: track["frame_ref"].destroy()
            for track in self.sub_tracks: track["frame_ref"].destroy()
            self.audio_tracks, self.sub_tracks = [], []

            general_track = next((t for t in media_info.tracks if t.track_type == 'General'), None)
            video_track = next((t for t in media_info.tracks if t.track_type == 'Video'), None)

            if video_track:
                hdr_f = video_track.hdr_format or ""
                transfer = video_track.transfer_characteristics or ""
                res_hdr = "SDR"
                if "Dolby Vision" in hdr_f: res_hdr = "Dolby Vision" + (" / HDR10" if "HDR10" in hdr_f else "")
                elif "HDR10" in hdr_f or "PQ" in transfer: res_hdr = "HDR10"
                self.video_vars["HDR"].set(res_hdr)

                w, h = int(video_track.width), int(video_track.height)
                if w >= 3400 or h >= 1944: q = "2160p (4K)"
                elif w >= 1728 or h >= 972: q = "1080p"
                elif w >= 1152 or h >= 648: q = "720p"
                else: q = "SD"

                self.video_vars["Qualité"].set(f"{q} ({w}x{h})")
                self.video_vars["Codec"].set(codec_map.get(video_track.format, video_track.format))
                self.video_vars["Bitrate (kbps)"].set(int(video_track.bit_rate / 1000) if video_track.bit_rate else "Variable")

            fn = os.path.basename(filepath)
            fn_upper = fn.upper()

            if general_track:
                fmt = general_track.format
                if fmt == "MPEG-4": fmt = "MP4"
                if fmt == "Matroska": fmt = "MKV"
                self.video_vars["Format"].set(fmt)

            source = "WEB-DL"
            if any(x in fn_upper for x in ["BLURAY", "BLU-RAY", "BD-RIP", "BDRIP", "BRRIP", "BR-RIP"]):
                source = "BluRay"
            elif any(x in fn_upper for x in ["HDTV", "TV-RIP", "TVRIP"]):
                source = "HDTV"
            elif any(x in fn_upper for x in ["WEB-RIP", "WEBRIP", "WEB.RIP"]):
                source = "WEB-RIP"
            elif any(x in fn_upper for x in ["REMUX"]):
                source = "Remux BluRay"

            self.video_vars["Source"].set(source)

            name_no_ext = os.path.splitext(fn)[0]
            self.team_var.set(name_no_ext.split("-")[-1].strip() if "-" in name_no_ext else "UNKNOWN")

            year_match = re.search(r'[\. \((](19\d{2}|20\d{2})[\. \))]', fn)
            self.api_vars["Année"].set(year_match.group(1) if year_match else "")
            self.api_vars["Titre"].set(fn[:year_match.start()].replace('.', ' ').strip().title() if year_match else name_no_ext.replace('.', ' ').title())

            for track in media_info.tracks:
                if track.track_type == 'Audio':
                    lang = self.get_full_language_name(track.language)
                    codec = codec_map.get(track.format, track.format)
                    br = int(track.bit_rate / 1000) if track.bit_rate else "Variable"
                    self.add_audio_track_auto(lang, codec, br)
                elif track.track_type == 'Text':
                    lang = self.get_full_language_name(track.language)
                    raw_fmt = track.format
                    clean_fmt = sub_format_map.get(raw_fmt, raw_fmt)
                    encoding = "UTF-8" if raw_fmt == "UTF-8" else ""
                    self.add_sub_track_auto(lang, clean_fmt, encoding)

        except Exception as e: messagebox.showerror("Erreur MediaInfo", str(e))

    def add_audio_track_auto(self, lang, codec, bitrate):
        frame = ttk.Frame(self.audio_notebook, padding=5)
        self.audio_notebook.add(frame, text=f"A:{len(self.audio_tracks)+1}")
        vars = {"Langue": tk.StringVar(value=lang), "Codec": tk.StringVar(value=codec), "Bitrate": tk.StringVar(value=bitrate), "frame_ref": frame}
        for i, (k, v) in enumerate(list(vars.items())[:-1]):
            ttk.Label(frame, text=k).grid(row=i, column=0, sticky="w")
            ttk.Entry(frame, textvariable=v, width=15).grid(row=i, column=1)
        self.audio_tracks.append(vars)

    def add_sub_track_auto(self, lang, format, encoding=""):
        frame = ttk.Frame(self.sub_notebook, padding=5)
        self.sub_notebook.add(frame, text=f"S:{len(self.sub_tracks)+1}")
        vars = {"Langue": tk.StringVar(value=lang), "Format": tk.StringVar(value=format), "Encodage": tk.StringVar(value=encoding), "frame_ref": frame}
        for i, (k, v) in enumerate(list(vars.items())[:-1]):
            ttk.Label(frame, text=k).grid(row=i, column=0, sticky="w")
            ttk.Entry(frame, textvariable=v, width=15).grid(row=i, column=1)
        self.sub_tracks.append(vars)

    def add_audio_track_manual(self): self.add_audio_track_auto("Français", "AC3", "640")
    def add_sub_track_manual(self): self.add_sub_track_auto("Français", "SRT", "UTF-8")
    def remove_audio_track(self):
        if self.audio_tracks: self.audio_tracks.pop()["frame_ref"].destroy()
    def remove_sub_track(self):
        if self.sub_tracks: self.sub_tracks.pop()["frame_ref"].destroy()

    def fetch_tmdb_data(self):
        api_key = self.api_key_var.get().strip()
        title = self.api_vars["Titre"].get()
        year = self.api_vars["Année"].get()
        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title}&year={year}&language=fr-FR"
        try:
            res = requests.get(url).json()
            if res.get('results'):
                data = requests.get(f"https://api.themoviedb.org/3/movie/{res['results'][0]['id']}?api_key={api_key}&language=fr-FR&append_to_response=credits").json()
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
                self.api_vars["Poster"].set(f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '')}")
                self.synopsis_text.delete(1.0, tk.END)
                self.synopsis_text.insert(tk.END, data.get('overview', ''))
                messagebox.showinfo("TMDb", "Infos récupérées !")
        except Exception as e: messagebox.showerror("Erreur", str(e))

    def generate_bbcode(self):
        crc = ""
        if self.use_crc32.get() and self.file_path.get():
            self.root.title("Calcul du CRC32...")
            self.root.update_idletasks()
            crc = f" | [b]CRC32 :[/b] {self.calculate_crc32(self.file_path.get())}"
            self.root.title("Python Prez Generator")

        hdr_v = self.video_vars['HDR'].get()
        h_tag = " [b][color=#CC00CC][DOLBY ViSiON][/color][/b]" if "Dolby" in hdr_v else " [b][color=#FF8000][HDR][/color][/b]" if "HDR" in hdr_v else ""

        audio_list = "".join([f"[b]Piste Audio {i+1} :[/b] {t['Langue'].get()} | {t['Codec'].get()} @ {t['Bitrate'].get()} kbps\n" for i, t in enumerate(self.audio_tracks)])

        sub_section = ""
        if self.sub_tracks:
            sub_entries = [f"[b]Sous-titre {i+1} :[/b] {t['Langue'].get()} ({t['Format'].get()}{' ['+t['Encodage'].get()+']' if t['Encodage'].get() else ''})" for i, t in enumerate(self.sub_tracks)]
            sub_section = f"\n[b][color=#0000ff]INFOS SOUS-TITRES[/color][/b]\n" + "\n".join(sub_entries) + "\n"

        bbcode = f"""[center]
[img]{self.api_vars['Poster'].get()}[/img]

[b][size=22]{self.api_vars['Titre'].get().upper()}{h_tag}[/size][/b]
[b][i]{self.api_vars['Titre Original'].get()} ({self.api_vars['Année'].get()})[/i][/b]

[quote][b]Synopsis :[/b]
{self.synopsis_text.get(1.0, tk.END).strip()}[/quote]

[b][color=#0000ff]INFOS VIDÉO[/color][/b]
[b]Qualité :[/b] {self.video_vars['Qualité'].get()} | [b]Source :[/b] {self.video_vars['Source'].get()}
[b]Format :[/b] {self.video_vars['Format'].get()} | [b]Codec :[/b] {self.video_vars['Codec'].get()}
[b]Bitrate :[/b] {self.video_vars['Bitrate (kbps)'].get()} kbps | [b]HDR :[/b] {hdr_v}

[b][color=#0000ff]INFOS AUDIO[/color][/b]
{audio_list}
{sub_section}
[b]Team :[/b] {self.team_var.get()}{crc}
[b]Lien TMDb :[/b] [url]{self.api_vars['Lien TMDb'].get()}[/url]
[/center]"""
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, bbcode.strip())
        self.notebook.select(2)

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output_text.get(1.0, tk.END).strip())
        messagebox.showinfo("Succès", "BBCode copié !")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrezGenerator(root)
    root.mainloop()
