"""CustomTkinter front end: workers emit events, only Tk's thread draws widgets.

Settings live in a separate file. An active job receives a snapshot so saving
settings cannot change its model or output destination halfway through a run.
"""
from copy import deepcopy
import json
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
from textwrap import shorten
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .config import DEFAULTS, ROOT, load_settings, update_settings
from .jobs import JobService, destination, inputs, save_transcript_edit
from .models import discover, doctor
from .storage import read_json, atomic_write
from .templates import MODES, BUILTINS, Template, load_template, validate_template
from .watcher import Watcher

from .ui_theme import BG, SURFACE, FIELD, TEXT, SUBTLE, ACCENT, PRIMARY, PRIMARY_HOVER, SELECTED, HOVER, colour, secondary, primary, option_menu, combo_box, tabs as themed_tabs, GradientFrame

HELP = {
    'synthesis.mode': ('Default processing mode', 'Clean paragraph improves readability; concise summary shortens; ideas and actions extracts evidence-linked findings. All preserve Hindi/English/mixed speech in source-language mode.'),
    'synthesis.prompt_directory': ('Custom prompt folder', 'Optional folder containing clean_paragraph.txt, concise_summary.txt and ideas_actions.txt. Missing mode files use the packaged templates. Edit prompt opens a preview/editor.'),
    'synthesis.prompt_file': ('Prompt file override', 'Optional custom UTF-8 template for the selected mode. Requires {transcript}; optional {context} and {output_language}. Switching modes in the toolbar clears this single-file override.'),
    'ui.appearance': ('Window appearance', 'System follows the appearance reported by your desktop. Choose Light or Dark explicitly if your desktop does not report it.'),
    'integration.enabled': ('Show Audio to Ideas in the app', 'Applies to the tray/main window the next time they start. CLI always remains available.'),
    'asr.backend': ('Speech engine', 'Choose speech recognition backend: faster-whisper, transcribe-cpp (Nemotron/Whisper/Voxtral GGUF), or handy-cli.'),
    'asr.active_profile': ('Active ASR model profile', 'Fast selection from model_profiles (e.g. nemotron_fast, whisper_turbo, hinglish_apex). When set, overrides backend and model_path.'),
    'asr.model_profiles': ('Available model profiles', 'Dictionary of named ASR profiles mapping to GGUF, CTranslate2, or binary models.'),
    'asr.model_id': ('Cached model repository', 'Choose a repository ID or alias such as large-v3. A model folder overrides this value.'),
    'asr.model_path': ('Model folder', 'Optional complete snapshot containing model.bin. Raw OpenAI/Transformers weights need another backend.'),
    'asr.cache_root': ('Model cache folder', 'Where downloaded models are stored on this PC. Change this path when moving to another computer.'),
    'asr.revision': ('Snapshot revision', 'Optional explicit snapshot identifier. A broken main reference is never silently replaced.'),
    'asr.device': ('Processing hardware', 'Auto tries CUDA then CPU. An explicit CUDA choice reports failure rather than switching hardware.'),
    'asr.compute_type': ('Model precision', 'Auto chooses a supported precision. Advanced: float16 for CUDA, int8 for CPU.'),
    'asr.cpu_threads': ('CPU threads', 'Number of CPU inference threads; leave room for the rest of your system.'),
    'asr.language': ('Recording language', 'Auto supports mixed Hindi/English. Use hi or en to request a specific language.'),
    'asr.word_timestamps': ('Word timing', 'Improves overlap merging; ASR timestamps are estimates that should be reviewed.'),
    'asr.offline': ('Offline mode', 'Use complete downloaded models and local Ollama only. No external requests.'),
    'asr.allow_downloads': ('Allow model downloads', 'Off by default. Requires offline mode to be off; discovery/doctor never downloads.'),
    'audio.sample_rate': ('Preparation sample rate', '16000 Hz is required by this ASR backend; original audio is preserved.'),
    'audio.normalize': ('Normalize volume', 'Optional loudness adjustment; may also amplify background noise. Starts off.'),
    'audio.target_lufs': ('Target loudness (LUFS)', 'Used only when volume normalization is enabled.'),
    'audio.true_peak_db': ('True peak ceiling (dB)', 'Used only for normalization; default -2 dB helps avoid clipping.'),
    'audio.chunk_seconds': ('Chunk duration (seconds)', 'Shorter windows improve recovery and limit how long other inference waits.'),
    'audio.overlap_seconds': ('Overlap (seconds)', 'Protects boundary speech. Must be smaller than the chunk; audio is never cross-faded.'),
    'synthesis.backend': ('Text processing engine', 'Local Ollama cleans paragraphs, creates summaries or extracts ideas.'),
    'synthesis.host': ('Ollama address', 'Usually http://localhost:11434. Remote addresses require offline mode to be off.'),
    'synthesis.model': ('Text processing model', 'Separate from Whisper. Blank inherits the existing English refiner if configured.'),
    'synthesis.temperature': ('Idea generation temperature', 'Lower values reduce variation; evidence still requires review.'),
    'synthesis.timeout_seconds': ('Response timeout (seconds)', 'Maximum time waiting for a response packet from the model service.'),
    'synthesis.context_tokens': ('Model context budget', 'Must fit your chosen model. Long transcripts are extracted in smaller sections.'),
    'synthesis.output_language': ('Processed output language', 'source preserves Hindi, English and their mix; choose English or Hindi to translate explicitly.'),
    'synthesis.context_profile': ('Default context profile', 'Optional JSON profile or UTF-8 text/Markdown background file.'),
    'output.directory': ('Output folder', 'Blank writes beside each recording. Folder batches preserve their subdirectories.'),
    'output.formats': ('Transcript formats', 'JSON list, e.g. ["txt", "srt"]. Canonical transcript JSON is always saved internally.'),
    'output.save_metadata': ('Save processing metadata', 'Records source identity, model revision, languages and warnings beside outputs.'),
    'output.overwrite': ('Reprocess existing jobs', 'Re-runs ASR and ideas. Unrelated files and manual output edits remain protected.'),
    'jobs.workers': ('Batch workers', 'One worker avoids competing models and excessive memory use in this release.'),
    'jobs.gpu_busy_policy': ('When inference is busy', 'queue waits; error reports contention; cpu uses CPU ASR when hardware is auto.'),
    'jobs.release_asr_before_synthesis': ('Release Whisper before ideas', 'Frees this job’s model memory before Ollama. Does not unload another process’s model.'),
    'watch.poll_seconds': ('Folder polling interval (seconds)', 'How often watch mode looks for new recordings.'),
    'watch.stable_seconds': ('Copy stability time (seconds)', 'Wait this long without size/modified-time changes before trying a new recording.'),
    'watch.recursive': ('Watch subfolders', 'Generated outputs and processing workspaces are excluded.'),
}

CHOICES = {
    'synthesis.mode': list(MODES),
    'ui.appearance': ['system', 'light', 'dark'],
    'asr.backend': ['faster-whisper', 'transcribe-cpp', 'handy-cli'],
    'asr.active_profile': ['', 'nemotron_fast', 'whisper_turbo', 'whisper_large_v3', 'hinglish_apex'],
    'asr.device': ['auto', 'cpu', 'cuda', 'vulkan'],
    'asr.compute_type': ['auto', 'float16', 'int8', 'int8_float16', 'float32'],
    'asr.language': ['auto', 'hi', 'en'],
    'jobs.gpu_busy_policy': ['queue', 'cpu', 'error'],
    'synthesis.output_language': ['source', 'English', 'Hindi'],
}
SETTINGS_GROUPS = {
    'Models': ['asr', 'synthesis'], 'Audio': ['audio'],
    'Output': ['output'], 'Preferences': ['ui', 'integration', 'jobs', 'watch'],
}


class IdeaTextbox(ctk.CTkTextbox):
    """Keep native Tk heading colours in sync, including system theme changes."""
    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self.tag_config('heading', foreground=self._apply_appearance_mode(ACCENT), spacing1=8, spacing3=4)


class Tooltip:
    """Small supplemental hover help; essential instructions remain visible."""
    def __init__(self, widget, text):
        self.widget, self.text, self.window, self.pending = widget, text, None, None
        widget.bind('<Enter>', self.enter, add='+')
        widget.bind('<Leave>', self.leave, add='+')
        widget.bind('<ButtonPress>', self.leave, add='+')
        widget.bind('<Destroy>', self.leave, add='+')

    def enter(self, _=None):
        self.pending = self.widget.after(600, self.show)

    def show(self):
        self.pending = None
        if not self.widget.winfo_exists():
            return
        self.window = tk.Toplevel(self.widget)
        self.window.overrideredirect(True)
        self.window.geometry(f'+{self.widget.winfo_rootx()+12}+{self.widget.winfo_rooty()+self.widget.winfo_height()+6}')
        tk.Label(self.window, text=self.text, wraplength=360, justify='left', bg=colour(SURFACE),
                 fg=colour(TEXT), padx=10, pady=8).pack()

    def leave(self, _=None):
        if self.pending:
            self.widget.after_cancel(self.pending)
            self.pending = None
        if self.window:
            if self.window.winfo_exists():
                self.window.destroy()
            self.window = None


class SettingsWindow:
    def __init__(self, app):
        self.app = app
        self.window = ctk.CTkToplevel(app.root)
        self.window.title('Audio to Ideas — Settings')
        self.window.geometry('840x760')
        self.window.minsize(720, 550)
        self.window.configure(fg_color=BG)
        self.window.transient(app.root)
        self.entries = {}
        ctk.CTkLabel(self.window, text='Settings apply to new jobs. Existing Voice Refiner and Review settings are kept separately.',
                     wraplength=740).pack(padx=20, pady=12)
        ctk.CTkLabel(self.window, text=f'Settings file: {app.settings.path}', wraplength=740, text_color=SUBTLE).pack()
        tabs = themed_tabs(self.window)
        tabs.pack(fill='both', expand=True, padx=15, pady=10)
        frames, next_rows = {}, {}
        for title, sections in SETTINGS_GROUPS.items():
            tabs.add(title)
            scroll = ctk.CTkScrollableFrame(tabs.tab(title), fg_color=SURFACE)
            scroll.pack(fill='both', expand=True)
            scroll.grid_columnconfigure(1, weight=1)
            for section in sections:
                frames[section] = scroll
            next_rows[scroll] = 0
        for section, defaults in DEFAULTS.items():
            if not isinstance(defaults, dict):
                continue
            scroll = frames[section]
            row = next_rows[scroll]
            ctk.CTkLabel(scroll, text=section.replace('_', ' ').title(), text_color=ACCENT,
                         font=('', 16, 'bold')).grid(row=row, column=0, columnspan=3, sticky='w', pady=(14, 6))
            row += 1
            for key, default in defaults.items():
                dotted = f'{section}.{key}'
                if dotted not in HELP:
                    continue
                label, help_text = HELP[dotted]
                ctk.CTkLabel(scroll, text=label).grid(row=row, column=0, sticky='w', padx=8)
                value = app.settings.data[section][key]
                if isinstance(default, bool):
                    variable = tk.BooleanVar(value=value)
                    widget = ctk.CTkSwitch(scroll, text='', variable=variable)
                else:
                    variable = tk.StringVar(value=json.dumps(value) if isinstance(value, (list, dict)) else ('' if value is None else str(value)))
                    if dotted == 'asr.active_profile':
                        prof_choices = [''] + list(app.settings.data.get('asr', {}).get('model_profiles', {}).keys())
                        for c in CHOICES.get(dotted, []):
                            if c not in prof_choices:
                                prof_choices.append(c)
                        widget = combo_box(scroll, variable=variable, values=prof_choices)
                    elif dotted in CHOICES:
                        # Editable comboboxes retain advanced values/language codes.
                        widget = combo_box(scroll, variable=variable, values=CHOICES[dotted])
                    else:
                        widget = ctk.CTkEntry(scroll, textvariable=variable, fg_color=FIELD, text_color=TEXT)
                widget.grid(row=row, column=1, sticky='ew', padx=8, pady=3)
                Tooltip(widget, help_text)
                self.entries[dotted] = (variable, default)
                if dotted in {'asr.model_path', 'asr.cache_root', 'output.directory', 'synthesis.context_profile',
                              'synthesis.prompt_directory', 'synthesis.prompt_file'}:
                    secondary(scroll, text='Browse', width=70,
                                  command=lambda d=dotted: self.browse(d)).grid(row=row, column=2)
                row += 1
                source = app.settings.sources.get(dotted, 'default')
                ctk.CTkLabel(scroll, text=help_text + f'  Current source: {source}.', text_color=SUBTLE,
                             wraplength=700, justify='left', anchor='w').grid(row=row, column=0, columnspan=3, sticky='w', padx=8)
                row += 1
            next_rows[scroll] = row
        self.initial = self.draft()
        self.discovery_events = queue.Queue()
        self.discovery_poll = None
        self.window.bind('<Destroy>', self.destroyed, add='+')
        bar = ctk.CTkFrame(self.window, fg_color='transparent')
        bar.pack(fill='x', padx=20, pady=12)
        primary(bar, text='Save settings', command=self.save).pack(side='left', padx=5)
        self.discovery_button = secondary(bar, text='Discover models', command=self.discover)
        self.discovery_button.pack(side='left', padx=5)
        secondary(bar, text='Close', command=self.window.destroy).pack(side='right')

    def browse(self, dotted):
        path = filedialog.askopenfilename(parent=self.window) if dotted in {'synthesis.context_profile', 'synthesis.prompt_file'} else filedialog.askdirectory(parent=self.window)
        if path:
            self.entries[dotted][0].set(path)

    def draft(self):
        data = deepcopy(self.app.settings.data)
        for dotted, (variable, default) in self.entries.items():
            section, key = dotted.split('.')
            value = variable.get()
            if isinstance(default, bool):
                pass
            elif isinstance(default, int):
                value = int(value)
            elif isinstance(default, float):
                value = float(value)
            elif isinstance(default, (list, dict)):
                value = json.loads(value)
            else:
                value = value.strip() or None
            data[section][key] = value
        return data

    def save(self):
        try:
            data = self.draft()
            changes = {f'{section}.{key}': value for section in DEFAULTS if isinstance(DEFAULTS[section], dict)
                       for key, value in data[section].items() if key in DEFAULTS[section]
                       and value != self.initial[section][key]}
            update_settings(self.app.settings.path, changes, fallback=self.app.settings.data)
            self.app.settings = load_settings(self.app.settings.path)
            self.app.apply_appearance(self.app.settings.data['ui']['appearance'])
            self.app.refresh_mode()
            self.app.status.set('Settings saved. New jobs use these settings; environment overrides still take priority.')
            self.window.destroy()
        except Exception as exc:
            messagebox.showerror('Settings not saved', str(exc), parent=self.window)

    def discover(self):
        try:
            data = self.draft()
        except Exception as exc:
            messagebox.showerror('Model discovery', str(exc), parent=self.window)
            return
        self.discovery_button.configure(state='disabled', text='Scanning cache…')
        def work():
            try:
                self.discovery_events.put((discover(data['asr']), None))
            except Exception as exc:
                self.discovery_events.put((None, str(exc)))
        # Even a slow removable/network disk must not block Tk's main thread.
        threading.Thread(target=work, daemon=True).start()
        self.discovery_poll = self.window.after(100, self.poll_discovery)

    def destroyed(self, event):
        if event.widget is self.window and self.discovery_poll:
            self.window.after_cancel(self.discovery_poll)
            self.discovery_poll = None

    def poll_discovery(self):
        self.discovery_poll = None
        try:
            models, error = self.discovery_events.get_nowait()
        except queue.Empty:
            self.discovery_poll = self.window.after(100, self.poll_discovery)
            return
        self.discovery_button.configure(state='normal', text='Discover models')
        if error:
            messagebox.showerror('Model discovery', error, parent=self.window)
            return
        try:
            dialog = ctk.CTkToplevel(self.window)
            dialog.title('Cached models — choose a complete snapshot')
            dialog.geometry('850x500')
            frame = ctk.CTkScrollableFrame(dialog)
            frame.pack(fill='both', expand=True, padx=10, pady=10)
            if not models:
                ctk.CTkLabel(frame, text='No Whisper snapshots found. Check the model cache folder.').pack()
            for item in models:
                description = f'{item["repository"]}\n{item["revision"]}\n' + ('Ready (assets found; model not loaded)' if item['compatible'] else '; '.join(item['problems']))
                if item['compatible']:
                    def select(m=item):
                        self.entries['asr.model_path'][0].set(m['path'])
                        self.entries['asr.model_id'][0].set(m['repository'])
                        self.entries['asr.revision'][0].set(m['revision'])
                        dialog.destroy()
                    primary(frame, text=description, anchor='w', command=select, height=70).pack(fill='x', pady=4)
                else:
                    ctk.CTkLabel(frame, text=description, wraplength=790, justify='left', text_color=SUBTLE).pack(fill='x', pady=8)
        except Exception as exc:
            messagebox.showerror('Model discovery', str(exc), parent=self.window)


class PromptEditor:
    """Edit a mode-specific personal copy; preview never calls the model."""
    def __init__(self, app):
        self.app = app
        self.mode = app.settings.data['synthesis']['mode']
        template = load_template(app.settings.data)
        self.window = ctk.CTkToplevel(app.root)
        self.window.title('Prompt — ' + MODES[self.mode])
        self.window.geometry('900x720')
        self.window.minsize(720, 550)
        self.window.configure(fg_color=BG)
        self.window.transient(app.root)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        ctk.CTkLabel(self.window, text=MODES[self.mode], font=('', 20, 'bold'), text_color=TEXT).pack(padx=16, pady=(14, 4), anchor='w')
        ctk.CTkLabel(self.window, text='Required: {transcript} exactly once. Optional: {context}, {output_language}.\n'
                     'Preview shows the template with up to 5,000 transcript characters; no request is sent.\n'
                     'The app enforces the JSON response and language/figure checks separately.',
                     justify='left', text_color=SUBTLE).pack(padx=16, pady=4, anchor='w')
        ctk.CTkLabel(self.window, text=f'Loaded from: {template.path}', wraplength=850, text_color=SUBTLE).pack(padx=16, anchor='w')
        self.tabs = themed_tabs(self.window)
        self.tabs.pack(fill='both', expand=True, padx=16, pady=8)
        self.tabs.add('Template'); self.tabs.add('Preview')
        self.editor = ctk.CTkTextbox(self.tabs.tab('Template'), wrap='word', fg_color=FIELD, text_color=TEXT, font=('', 14))
        self.editor.pack(fill='both', expand=True)
        self.editor.insert('1.0', template.text)
        self.initial = template.text.rstrip('\n')
        self.preview_box = ctk.CTkTextbox(self.tabs.tab('Preview'), wrap='word', fg_color=FIELD, text_color=TEXT)
        self.preview_box.pack(fill='both', expand=True)
        self.preview_box.configure(state='disabled')
        folder = app.settings.data['synthesis']['prompt_directory'] or str(app.settings.path.parent / 'audio_to_idea_prompts')
        self.folder = tk.StringVar(value=folder)
        paths = ctk.CTkFrame(self.window, fg_color='transparent')
        paths.pack(fill='x', padx=16, pady=4)
        ctk.CTkLabel(paths, text='Save custom folder', text_color=TEXT).pack(side='left', padx=(0, 8))
        ctk.CTkEntry(paths, textvariable=self.folder, fg_color=FIELD, text_color=TEXT).pack(side='left', fill='x', expand=True)
        secondary(paths, text='Browse', width=80, command=self.browse).pack(side='left', padx=(8, 0))
        ctk.CTkLabel(self.window, text=f'Saves {self.mode}.txt; other modes keep their own templates. Active jobs keep their prompt snapshot.',
                     text_color=SUBTLE, wraplength=850).pack(padx=16)
        bar = ctk.CTkFrame(self.window, fg_color='transparent')
        bar.pack(fill='x', padx=16, pady=12)
        primary(bar, text='Save custom prompt', command=self.save).pack(side='left')
        secondary(bar, text='Preview', command=self.preview).pack(side='left', padx=8)
        secondary(bar, text='Restore built-in text', command=self.restore, width=150).pack(side='left')
        secondary(bar, text='Close', command=self.close, width=80).pack(side='right')

    def browse(self):
        path = filedialog.askdirectory(parent=self.window)
        if path:
            self.folder.set(path)

    def restore(self):
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', (BUILTINS / f'{self.mode}.txt').read_text(encoding='utf-8'))

    def preview(self):
        try:
            text = validate_template(self.editor.get('1.0', 'end-1c'))
            source = 'यह एक sample recording है। Please review the inspection report.'
            result = (self.app.selected or {}).get('result') or {}
            if result.get('transcript_path'):
                data = read_json(result['transcript_path'])
                source = '\n'.join(f'[{s["id"]}] {s["text"]}' for s in data['segments'])[:5000]
            from .profiles import load_profile
            profile = load_profile(self.app.profile_var.get().strip() or None, self.app.context.get('1.0', 'end-1c'))
            language = profile.get('output_language') or self.app.settings.data['synthesis']['output_language']
            if language == 'source' and self.mode != 'ideas_actions':
                from .rewriting import source_language
                language = source_language(re.sub(r'^\[S\d+\] ', '', source, flags=re.M))
            rendered = Template(text, Path(), self.mode).render(source, profile['background'], language)
            self.preview_box.configure(state='normal')
            self.preview_box.delete('1.0', 'end')
            self.preview_box.insert('1.0', rendered)
            self.preview_box.configure(state='disabled')
            self.tabs.set('Preview')
        except Exception as exc:
            messagebox.showerror('Prompt preview', str(exc), parent=self.window)

    def save(self):
        try:
            text = validate_template(self.editor.get('1.0', 'end-1c'))
            folder = Path(self.folder.get().strip()).expanduser().resolve()
            # Personal templates cannot overwrite shipped or legacy prompts.
            if folder.is_relative_to(BUILTINS.resolve()) or folder.is_relative_to((ROOT / 'prompts').resolve()):
                raise ValueError('Choose a separate AudioToIdea custom prompt folder.')
            if not self.folder.get().strip():
                raise ValueError('Choose a custom prompt folder.')
            path = folder / f'{self.mode}.txt'
            atomic_write(path, text.rstrip() + '\n')
            update_settings(self.app.settings.path, {'synthesis.prompt_directory': str(folder),
                            'synthesis.prompt_file': None})
            self.app.settings.data['synthesis'].update(prompt_directory=str(folder), prompt_file=None)
            self.initial = text.rstrip('\n')
            self.app.status.set(f'Custom {MODES[self.mode]} prompt saved. New jobs use it; valid ASR is reused.')
        except Exception as exc:
            messagebox.showerror('Prompt not saved', str(exc), parent=self.window)

    def close(self):
        if self.editor.get('1.0', 'end-1c').rstrip('\n') != self.initial:
            if not messagebox.askyesno('Unsaved prompt', 'Discard unsaved prompt changes?', parent=self.window):
                return
        self.window.destroy()


class AudioToIdeaApp:
    def __init__(self, root, settings):
        self.root, self.settings = root, settings
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.worker = None
        self.items, self.rows = [], {}
        self.selected = None
        self.loaded_text = ''
        appearance = settings.data.get('ui', {}).get('appearance', 'system')
        ctk.set_appearance_mode(appearance)
        root.title('Audio to Ideas — Recordings, transcripts and actions')
        root.geometry('1280x860')
        root.minsize(980, 700)
        root.configure(fg_color=BG)
        self.backdrop = GradientFrame(root, backdrop=True)
        self.backdrop.place(x=0, y=0, relwidth=1, relheight=1)
        self.backdrop.lower()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(3, weight=1)

        header = GradientFrame(root)
        header.grid(row=0, column=0, columnspan=2, sticky='ew', padx=20, pady=(16, 8))
        ctk.CTkLabel(header, text='Audio to Ideas', font=('', 26, 'bold'), text_color=TEXT).pack(side='left', padx=(14, 0), pady=3)
        self.mode_var = tk.StringVar(value=MODES[settings.data['synthesis']['mode']])
        self.mode_menu = option_menu(header, values=list(MODES.values()), variable=self.mode_var,
            command=self.change_mode, width=205)
        self.mode_menu.pack(side='left', padx=(20, 8))
        Tooltip(self.mode_menu, HELP['synthesis.mode'][1])
        self.prompt_button = secondary(header, text='Edit prompt', command=self.edit_prompt, width=100)
        self.prompt_button.pack(side='left')
        Tooltip(self.prompt_button, 'Preview and edit a separate prompt for this mode. Changes apply to new jobs and preserve raw transcription.')
        self.appearance_var = tk.StringVar(value=appearance.title())
        self.appearance_menu = option_menu(header, values=['System', 'Light', 'Dark'],
            variable=self.appearance_var, command=self.change_appearance, width=110)
        self.appearance_menu.pack(side='right', padx=(10, 14))
        Tooltip(self.appearance_menu, HELP['ui.appearance'][1])
        ctk.CTkLabel(header, text='Appearance', text_color=SUBTLE).pack(side='right')
        toolbar = ctk.CTkFrame(root, fg_color='transparent')
        toolbar.grid(row=1, column=0, columnspan=2, sticky='ew', padx=20, pady=(0, 12))
        ctk.CTkLabel(toolbar, text='Turn saved recordings into useful, traceable ideas.', text_color=SUBTLE).pack(side='left')
        for text, callback, help_text in [
            ('Settings', lambda: SettingsWindow(self), 'Set models, hardware, paths, outputs and appearance for this PC.'),
            ('Check setup', self.check_setup, 'Validate assets and dependencies without loading a large model.'),
            ('Watch folder', self.watch, 'Process completed file copies automatically. Stop ends watching.'),
        ]:
            button = secondary(toolbar, text=text, command=callback, width=112)
            button.pack(side='right', padx=(8, 0))
            Tooltip(button, help_text)

        context_frame = GradientFrame(root)
        context_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=20, pady=(0, 12))
        context_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(context_frame, text='Project context', text_color=TEXT, font=('', 14, 'bold')).grid(row=0, column=0, padx=14, pady=10)
        self.profile_var = tk.StringVar(value=settings.data['synthesis']['context_profile'] or '')
        profile_paths = sorted((ROOT / 'profiles/audio_to_idea').glob('*.json')) + sorted((Path(__file__).parent / 'example_profiles').glob('*.json'))
        self.profile_choices = {'No profile': ''}
        for path in profile_paths:
            self.profile_choices[path.stem.replace('_', ' ').title()] = str(path)
        self.profile_choice = combo_box(context_frame, values=list(self.profile_choices), width=210, command=lambda choice: self.profile_var.set(self.profile_choices[choice]))
        self.profile_choice.set(next((name for name, path in self.profile_choices.items() if path == self.profile_var.get()), 'Custom profile'))
        self.profile_choice.grid(row=0, column=1, sticky='w', padx=8)
        self.context_button = secondary(context_frame, text='Add background', command=self.toggle_context, width=135)
        self.context_button.grid(row=0, column=2, padx=12)
        self.context_details = ctk.CTkFrame(context_frame, fg_color='transparent')
        self.context_details.grid_columnconfigure(0, weight=1)
        profile_entry = ctk.CTkEntry(self.context_details, textvariable=self.profile_var,
            placeholder_text='Optional JSON, text or Markdown profile', fg_color=FIELD, text_color=TEXT)
        profile_entry.grid(row=0, column=0, sticky='ew', padx=(14, 8), pady=(2, 8))
        Tooltip(profile_entry, 'A profile supplies project background and a glossary. You can also type background below.')
        secondary(self.context_details, text='Browse profile', command=self.choose_profile, width=125).grid(row=0, column=1, padx=(0, 14), pady=(2, 8))
        self.context = ctk.CTkTextbox(self.context_details, height=64, fg_color=FIELD, text_color=TEXT, wrap='word')
        self.context.grid(row=1, column=0, columnspan=2, sticky='ew', padx=14)
        ctk.CTkLabel(self.context_details, text='Optional background explains terms. It is not evidence of what was said.',
            text_color=SUBTLE).grid(row=2, column=0, columnspan=2, sticky='w', padx=14, pady=(2, 8))
        self.context_expanded = False

        sidebar = GradientFrame(root, width=236)
        sidebar.grid(row=3, column=0, sticky='nsew', padx=(20, 10))
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)
        self.queue_label = ctk.CTkLabel(sidebar, text='Recordings · 0', font=('', 16, 'bold'), text_color=TEXT, anchor='w')
        self.queue_label.grid(row=0, column=0, sticky='ew', padx=14, pady=(14, 8))
        imports = ctk.CTkFrame(sidebar, fg_color='transparent')
        imports.grid(row=1, column=0, sticky='ew', padx=12, pady=(0, 8))
        imports.grid_columnconfigure((0, 1), weight=1)
        secondary(imports, text='Add files', command=self.add_files, width=95).grid(row=0, column=0, padx=(0, 4), sticky='ew')
        secondary(imports, text='Add folder', command=self.add_folder, width=95).grid(row=0, column=1, padx=(4, 0), sticky='ew')
        self.queue_frame = ctk.CTkScrollableFrame(sidebar, width=208, fg_color='transparent')
        self.queue_frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=(0, 8))
        self.empty_queue = ctk.CTkLabel(self.queue_frame,
            text='No recordings yet\n\nAdd saved audio files\nto get started.\n\nMP3 · WAV · M4A · AAC\nFLAC · OGG · WEBM', text_color=SUBTLE, justify='left')
        self.empty_queue.pack(padx=8, pady=24, anchor='w')

        panels = ctk.CTkFrame(root, fg_color='transparent')
        panels.grid(row=3, column=1, sticky='nsew', padx=(0, 20))
        panels.grid_columnconfigure((0, 1), weight=1, uniform='panels')
        panels.grid_rowconfigure(0, weight=1)
        transcript_card = GradientFrame(panels)
        idea_card = GradientFrame(panels)
        for column, card, title, subtitle in [
            (0, transcript_card, 'Transcript', 'Review words and keep the segment IDs.'),
            (1, idea_card, 'Processed text', 'Clean paragraph · summary · ideas and actions'),
        ]:
            card.grid(row=0, column=column, sticky='nsew', padx=(0, 6) if column == 0 else (6, 0))
            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure(2, weight=1)
            ctk.CTkLabel(card, text=title, font=('', 18, 'bold'), text_color=TEXT, anchor='w').grid(row=0, column=0, sticky='ew', padx=16, pady=(12, 0))
            ctk.CTkLabel(card, text=subtitle, text_color=SUBTLE, anchor='w', wraplength=340, justify='left').grid(row=1, column=0, sticky='ew', padx=16, pady=(2, 6))
        tabs = themed_tabs(transcript_card, fg_color=FIELD)
        tabs.grid(row=2, column=0, sticky='nsew', padx=12)
        for tab in ['Editable', 'Raw ASR']:
            tabs.add(tab)
        self.transcript = ctk.CTkTextbox(tabs.tab('Editable'), wrap='word', font=('', 14), fg_color=FIELD, text_color=TEXT)
        self.transcript.pack(fill='both', expand=True)
        self.transcript.configure(state='disabled')
        self.raw = ctk.CTkTextbox(tabs.tab('Raw ASR'), wrap='word', font=('', 14), fg_color=FIELD, text_color=TEXT)
        self.raw.pack(fill='both', expand=True)
        self.raw.configure(state='disabled')
        self.ideas = IdeaTextbox(idea_card, wrap='word', font=('', 14), fg_color=FIELD, text_color=TEXT, corner_radius=8)
        self.ideas.grid(row=2, column=0, sticky='nsew', padx=12, pady=(12, 0))
        self.ideas.configure(state='disabled')
        self.save_button = secondary(transcript_card, text='Save transcript revision', command=self.save_edit)
        self.save_button.grid(row=3, column=0, pady=12)
        Tooltip(self.save_button, 'Preserves raw ASR. Regenerate ideas after saving corrected words.')
        self.output_button = secondary(idea_card, text='Open output folder', command=self.open_output)
        self.output_button.grid(row=3, column=0, pady=12)

        bar = ctk.CTkFrame(root, fg_color='transparent')
        bar.grid(row=4, column=0, columnspan=2, sticky='ew', padx=20, pady=(14, 8))
        self.process_button = primary(bar, text='Transcribe + process', command=lambda: self.start(True),
            height=38, font=('', 14, 'bold'))
        self.process_button.pack(side='left', padx=(0, 8))
        self.transcribe_button = secondary(bar, text='Transcript only', command=lambda: self.start(False))
        self.transcribe_button.pack(side='left', padx=(0, 8))
        self.retry_button = secondary(bar, text='Regenerate selected', command=self.retry, width=170)
        self.retry_button.pack(side='left')
        Tooltip(self.retry_button, 'Runs the selected mode with your current prompt and corrected transcript; valid ASR is reused.')
        self.cancel_button = secondary(bar, text='Stop', command=self.stop, width=100)
        self.cancel_button.pack(side='right')
        Tooltip(self.cancel_button, 'Stops at a safe checkpoint. Completed chunks remain saved for resume.')
        footer = ctk.CTkFrame(root, fg_color='transparent')
        footer.grid(row=5, column=0, columnspan=2, sticky='ew', padx=20, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        self.status = tk.StringVar(value='Ready. Add saved recordings to begin.')
        ctk.CTkLabel(footer, textvariable=self.status, anchor='w', text_color=SUBTLE,
            wraplength=800, justify='left').grid(row=0, column=0, sticky='ew')
        self.progress = ctk.CTkProgressBar(footer, width=180, height=6, progress_color=PRIMARY)
        self.progress.grid(row=0, column=1, padx=(14, 0))
        self.progress.set(0)
        self._progress_active = False
        self.update_controls()
        self.poll_id = root.after(100, self.poll)

    def refresh_mode(self):
        self.mode_var.set(MODES[self.settings.data['synthesis']['mode']])

    def change_mode(self, label):
        mode = next(key for key, value in MODES.items() if value == label)
        try:
            update_settings(self.settings.path, {'synthesis.mode': mode, 'synthesis.prompt_file': None})
            self.settings.data['synthesis'].update(mode=mode, prompt_file=None)
            self.status.set(f'{label} selected. Regenerate selected to process an existing transcript with this mode.')
        except Exception as exc:
            messagebox.showerror('Mode not saved', str(exc), parent=self.root)
        self.refresh_mode()

    def edit_prompt(self):
        try:
            return PromptEditor(self)
        except Exception as exc:
            messagebox.showerror('Prompt editor', str(exc), parent=self.root)

    def toggle_context(self):
        self.context_expanded = not self.context_expanded
        if self.context_expanded:
            self.context_details.grid(row=1, column=0, columnspan=3, sticky='ew')
        else:
            self.context_details.grid_remove()
        self.context_button.configure(text='Hide background' if self.context_expanded else 'Add background')

    def apply_appearance(self, appearance):
        ctk.set_appearance_mode(appearance)
        self.appearance_var.set(appearance.title())
        self.ideas.tag_config('heading', foreground=colour(ACCENT), spacing1=8, spacing3=4)

    def change_appearance(self, choice):
        previous = self.settings.data.get('ui', {}).get('appearance', 'system')
        try:
            # Save only this UI field; CLI/environment model choices stay transient.
            update_settings(self.settings.path, {'ui.appearance': choice.lower()})
            self.settings.data.setdefault('ui', {})['appearance'] = choice.lower()
            self.apply_appearance(choice.lower())
        except Exception as exc:
            self.apply_appearance(previous)
            messagebox.showerror('Appearance not saved', str(exc), parent=self.root)

    def update_controls(self):
        busy = self.busy()
        pending = any(item['status'] != 'complete' for item in self.items)
        for button in (self.process_button, self.transcribe_button):
            button.configure(state='normal' if pending and not busy else 'disabled')
        self.retry_button.configure(state='normal' if self.selected and not busy else 'disabled')
        result = (self.selected or {}).get('result') or {}
        self.save_button.configure(state='normal' if result.get('transcript_path') and not busy else 'disabled')
        self.output_button.configure(state='normal' if result.get('workspace') else 'disabled')
        self.cancel_button.configure(state='normal' if busy and not self.cancel.is_set() else 'disabled')
        self.mode_menu.configure(state='disabled' if busy else 'normal')
        if busy and not self._progress_active:
            self.progress.configure(mode='indeterminate')
            self.progress.start()
            self._progress_active = True
        elif not busy and self._progress_active:
            self.progress.stop()
            self.progress.configure(mode='determinate')
            self.progress.set(0)
            self._progress_active = False

    def stop(self):
        self.cancel.set()
        self.status.set('Stopping at the next safe checkpoint. Completed stages remain saved.')
        self.update_controls()

    def choose_profile(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[('Context profiles', '*.json *.md *.txt'), ('All files', '*')])
        if path:
            self.profile_var.set(path)
            self.profile_choice.set('Custom profile')

    def add(self, paths, input_root=None):
        for path in paths:
            source = Path(path).resolve()
            if any(i['source'] == source for i in self.items):
                continue
            output, name = destination(source, input_root or source, self.settings.data['output']['directory'])
            item = {'source': source, 'input_root': input_root or source, 'output': output, 'name': name, 'status': 'queued', 'result': None}
            self.items.append(item)
            button = secondary(self.queue_frame, text=self.queue_text(source, 'Queued'), height=60, width=190,
                               command=lambda i=item: self.select(i), anchor='w')
            button.pack(fill='x', pady=4)
            Tooltip(button, str(source))
            self.rows[source] = button
        if self.items:
            self.empty_queue.pack_forget()
        self.queue_label.configure(text=f'Recordings · {len(self.items)}')
        self.update_controls()

    @staticmethod
    def queue_text(source, status):
        # Keep long filenames/statuses inside the sidebar; hover exposes the path.
        name = source.name
        if len(name) > 26:
            name = name[:23] + '…'
        return name + '\n' + shorten(status, width=28, placeholder='…')

    def add_files(self):
        self.add(filedialog.askopenfilenames(parent=self.root, filetypes=[('Audio recordings', '*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.webm'), ('All files', '*')]))

    def add_folder(self):
        path = filedialog.askdirectory(parent=self.root)
        if path:
            try:
                self.add(inputs(path), Path(path).resolve())
            except Exception as exc:
                messagebox.showerror('Add folder', str(exc), parent=self.root)

    def busy(self):
        return self.worker is not None and self.worker.is_alive()

    def check_setup(self):
        settings = deepcopy(self.settings)
        def work():
            try:
                report = doctor(settings, include_discovery=True)
                self.events.put({'stage': 'diagnostics', 'message': json.dumps(report, ensure_ascii=False, indent=2)})
            except Exception as exc:
                self.events.put({'stage': 'warning', 'message': f'Setup check failed: {exc}'})
        threading.Thread(target=work, daemon=True).start()

    def unsaved(self):
        if self.selected and self.transcript.get('1.0', 'end-1c') != self.loaded_text:
            answer = messagebox.askyesnocancel('Unsaved transcript edits', 'Save a new transcript revision before continuing?', parent=self.root)
            if answer is None:
                return True
            if answer and not self.save_edit():
                return True
        return False

    def start(self, summary=True, selected_only=False):
        if self.busy():
            self.status.set('A job is already running. Cancel it or wait before starting another.')
            return
        if self.unsaved():
            return
        pending = [self.selected] if selected_only and self.selected else [i for i in self.items if i['status'] != 'complete']
        if not pending:
            self.status.set('Add recordings or select a completed recording to regenerate processed text.')
            return
        cfg = deepcopy(self.settings.data)
        targets = [(item, *destination(item['source'], item['input_root'], cfg['output']['directory'])) for item in pending]
        context, profile = self.context.get('1.0', 'end-1c'), self.profile_var.get().strip() or None
        self.cancel.clear()
        service = JobService(cfg)
        if summary:
            try:
                service.snapshot_prompt()
            except Exception as exc:
                messagebox.showerror('Cannot start processing', str(exc), parent=self.root)
                return
        def work():
            try:
                for item, output, name in targets:
                    if self.cancel.is_set():
                        break
                    self.events.put({'stage': 'running', 'message': f'Processing {item["source"].name}', 'source': str(item['source'])})
                    service.run(item['source'], output, name, summary, context, profile, self.cancel, self.events.put)
            except Exception as exc:
                self.events.put({'stage': 'failed', 'message': str(exc)})
            finally:
                self.events.put({'stage': 'idle', 'message': 'Queue stopped' if self.cancel.is_set() else 'Queue finished'})
        self.worker = threading.Thread(target=work, daemon=False)
        self.worker.start()
        self.update_controls()

    def retry(self):
        if not self.selected:
            self.status.set('Select a recording from the queue first.')
            return
        self.start(True, selected_only=True)

    def watch(self):
        if self.busy() or self.unsaved():
            return
        folder = filedialog.askdirectory(parent=self.root, title='Watch completed recordings in this folder')
        if not folder:
            return
        cfg = deepcopy(self.settings.data)
        context, profile = self.context.get('1.0', 'end-1c'), self.profile_var.get().strip() or None
        self.cancel.clear()
        service = JobService(cfg)
        try:
            service.snapshot_prompt()
        except Exception as exc:
            messagebox.showerror('Cannot watch folder', str(exc), parent=self.root)
            return
        def work():
            try:
                Watcher(service, folder, cfg['output']['directory'], True, context, profile, self.events.put).run(self.cancel)
            except Exception as exc:
                self.events.put({'stage': 'failed', 'message': str(exc)})
            finally:
                self.events.put({'stage': 'idle', 'message': 'Folder watch stopped'})
        self.worker = threading.Thread(target=work, daemon=False)
        self.worker.start()
        self.status.set(f'Watching {folder}. Waiting for completed copies; Cancel stops watch mode.')
        self.update_controls()

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                self.status.set(event.get('message', ''))
                if event.get('total'):
                    self.progress.stop()
                    self.progress.configure(mode='determinate')
                    self.progress.set(event['current'] / event['total'])
                elif event['stage'] in {'preparation', 'synthesis', 'running'} and self.busy():
                    self.progress.configure(mode='indeterminate')
                    self.progress.start()
                if event['stage'] == 'diagnostics':
                    window = ctk.CTkToplevel(self.root)
                    window.title('Audio to Ideas — Setup diagnostics')
                    window.geometry('850x600')
                    box = ctk.CTkTextbox(window)
                    box.pack(fill='both', expand=True)
                    box.insert('1.0', event['message'])
                    box.configure(state='disabled')
                if 'result' in event:
                    result = event['result']
                    source = Path(result['source'])
                    if source not in self.rows:
                        self.add([source])
                    item = next(i for i in self.items if i['source'] == source)
                    item.update(result=result, status=result['status'])
                    self.rows[source].configure(text=self.queue_text(source, result['status'].title()))
                    # Refresh regenerated results automatically, but never erase
                    # edits typed while the worker was running.
                    if not self.selected or (self.selected is item and self.transcript.get('1.0', 'end-1c') == self.loaded_text):
                        self.select(item, refresh=True)
                elif event.get('source'):
                    source = Path(event['source'])
                    if source not in self.rows:
                        self.add([source])
                    self.rows[source].configure(text=self.queue_text(source, 'Processing…'))
        except queue.Empty:
            pass
        self.update_controls()
        self.poll_id = self.root.after(100, self.poll)

    def select(self, item, refresh=False):
        if item is self.selected and not refresh:
            return
        if item is not self.selected and self.unsaved():
            return
        self.selected = item
        for queued in self.items:
            self.rows[queued['source']].configure(fg_color=SELECTED if queued is item else SURFACE)
        result = item.get('result')
        self.transcript.configure(state='normal')
        self.transcript.delete('1.0', 'end')
        self.loaded_text = ''
        for widget in [self.raw, self.ideas]:
            widget.configure(state='normal')
            widget.delete('1.0', 'end')
        if result and result.get('transcript_path'):
            try:
                data = read_json(result['transcript_path'])
                text = '\n'.join(f'[{s["id"]}] {s["text"]}' for s in data['segments'])
                self.transcript.insert('1.0', text)
                self.loaded_text = text
                manifest = read_json(Path(result['workspace']) / 'manifest.json')
                original = read_json(Path(result['workspace']) / manifest['transcript'])
                self.raw.insert('1.0', '\n'.join(f'[{s["id"]} {s["start"]:.2f}s] {s["text"]}' for s in original['segments']))
                idea_file = (Path(result['processed_path']) if result.get('processed_path') else
                             next((Path(p) for p in result['outputs'] if p.endswith('_idea.txt')), None))
                if idea_file and idea_file.exists():
                    # Plain paragraphs must not pass through Markdown cleanup,
                    # which could change literal #, **, or technical content.
                    text = idea_file.read_text(encoding='utf-8')
                    if result.get('synthesis_mode', 'ideas_actions') == 'ideas_actions':
                        self.render_ideas(text)
                    else:
                        self.ideas.insert('1.0', text)
                elif result.get('error'):
                    self.ideas.insert('1.0', 'Processed text unavailable. Transcript is preserved.\n\n' + result['error'])
            except Exception as exc:
                self.status.set(str(exc))
        else:
            self.raw.insert('1.0', 'Raw recognition will appear after transcription. The original recording is preserved.')
            self.ideas.insert('1.0', 'Choose a processing mode above, then Transcribe + process.\n\nClean paragraph is the default. For raw words only, choose Transcript only.')
            self.transcript.configure(state='disabled')
        for widget in [self.raw, self.ideas]:
            widget.configure(state='disabled')
        self.update_controls()

    def render_ideas(self, markdown):
        """Readable headings/bullets in Tk; exported Markdown stays unchanged."""
        # CustomTkinter manages font scaling itself; tag fonts are deliberately
        # unsupported. Color/spacing remain compatible with its DPI behavior.
        self.ideas.tag_config('heading', foreground=colour(ACCENT), spacing1=8, spacing3=4)
        for line in markdown.splitlines():
            heading = line.startswith('#')
            display = line.lstrip('#').strip() if heading else line.replace('**', '')
            if display.startswith('- '):
                display = '• ' + display[2:]
            if display.startswith('Transcript revision:'):
                display = re.sub(r'\b[0-9a-f]{64}\b', lambda m: m[0][:12] + '…', display)
            self.ideas.insert('end', display + '\n', ('heading',) if heading else ())

    def save_edit(self):
        if self.busy():
            self.status.set('Wait for processing to finish before saving transcript revisions.')
            return False
        if not self.selected or not (self.selected.get('result') or {}).get('transcript_path'):
            self.status.set('Select a recording with a completed transcript first.')
            return False
        try:
            text = self.transcript.get('1.0', 'end-1c')
            edits, current = {}, None
            for line in text.splitlines():
                match = re.match(r'^\[(S\d+)\]\s?(.*)$', line)
                if match:
                    current = match[1]
                    if current in edits:
                        raise ValueError('Duplicate segment ID: ' + current)
                    edits[current] = match[2]
                elif current:
                    edits[current] += '\n' + line
                elif line.strip():
                    raise ValueError('Keep segment IDs such as [S00001] at the start of each segment.')
            result = self.selected['result']
            path = save_transcript_edit(result['workspace'], edits)
            result['transcript_path'] = str(path)
            self.loaded_text = text
            self.selected['status'] = 'transcribed'
            self.rows[self.selected['source']].configure(text=self.queue_text(self.selected['source'], 'Edited · regenerate output'))
            self.ideas.configure(state='normal')
            self.ideas.insert('1.0', 'Transcript has a newer revision. Regenerate selected to update processed text.\n\n')
            self.ideas.configure(state='disabled')
            self.status.set('Transcript revision saved. Regenerate selected to update exports and processed text; ASR is reused.')
            self.update_controls()
            return True
        except Exception as exc:
            messagebox.showerror('Transcript not saved', str(exc), parent=self.root)
            return False

    def open_output(self):
        if self.selected and self.selected.get('result'):
            path = Path(self.selected['result']['workspace']).parents[1]
            subprocess.Popen(['xdg-open', str(path)])

    def close(self):
        if self.unsaved():
            return
        if self.busy():
            if not messagebox.askyesno('Stop processing?', 'Cancel and close after the next safe processing checkpoint? Completed stages remain saved.', parent=self.root):
                return
            self.cancel.set()
            self.status.set('Stopping safely… waiting for the current model call/checkpoint.')
            def wait():
                if self.busy():
                    self.root.after(100, wait)
                else:
                    self.root.after_cancel(self.poll_id)
                    self.root.destroy()
            wait()
        else:
            self.root.after_cancel(self.poll_id)
            self.root.destroy()


def launch(settings=None):
    settings = settings or load_settings()
    ctk.set_appearance_mode(settings.data['ui']['appearance'])
    root = ctk.CTk()
    AudioToIdeaApp(root, settings)
    root.mainloop()


if __name__ == '__main__':
    launch()
