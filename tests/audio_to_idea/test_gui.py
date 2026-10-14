"""Exercise Tk under Xvfb; all recording/model/desktop effects are isolated."""
from copy import deepcopy
import os
from pathlib import Path
import time
from unittest.mock import Mock

import pytest
from audio_to_idea.config import DEFAULTS, Settings

pytestmark = [pytest.mark.desktop, pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Run with xvfb-run for GUI tests.')]


def test_gui_queue_revision_settings_and_screenshot(tmp_path, monkeypatch):
    import customtkinter as ctk
    import audio_to_idea.gui as gui
    import audio_to_idea.config as config
    # A previous legacy-window smoke test may import gui while config loading
    # is patched. Restore the real loader for this settings round-trip check.
    monkeypatch.setattr(gui, 'load_settings', config.load_settings)
    from audio_to_idea.jobs import JobService
    from test_config_models import model
    from test_audio_exports import wav
    from test_jobs_synthesis import FakeASR, FakeLLM
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    cfg['extra'] = {'preserve': True}
    cfg['synthesis']['model'] = 'fake'
    cfg['synthesis']['mode'] = 'ideas_actions'  # Retain coverage of the original structured mode.
    settings = Settings(cfg, tmp_path / 'settings.json', {})
    monkeypatch.setattr(gui, 'JobService', lambda c: JobService(c, FakeASR, FakeLLM))
    monkeypatch.setattr(gui.messagebox, 'showerror', lambda *a, **kw: pytest.fail(str(a)))
    ctk.set_appearance_mode('dark')
    root = ctk.CTk()
    app = gui.AudioToIdeaApp(root, settings)
    try:
        source = wav(tmp_path / 'meeting.wav')
        app.add([source])
        app.select(app.items[0])
        assert app.save_edit() is False
        app.start(True)
        deadline = time.monotonic() + 10
        while (app.busy() or app.items[0]['result'] is None) and time.monotonic() < deadline:
            root.update()
            time.sleep(.03)
        root.update()
        assert app.items[0]['status'] == 'complete'
        app.select(app.items[0])
        assert 'S00001' in app.transcript.get('1.0', 'end-1c')
        assert 'Core Operational Bottlenecks' in app.ideas.get('1.0', 'end-1c')
        assert '**Source Audio:**' not in app.ideas.get('1.0', 'end-1c')
        app.transcript.delete('1.0', 'end')
        app.transcript.insert('1.0', '[S00001] Corrected 124 किलोमीटर')
        app.select(app.items[0])
        assert '124' in app.transcript.get('1.0', 'end-1c')  # Clicking again must retain edits.
        assert app.save_edit()
        window = gui.SettingsWindow(app)
        root.update()
        assert set(window.entries) == set(gui.HELP)
        window.entries['asr.cpu_threads'][0].set('2')
        window.save()
        assert app.settings.data['extra']['preserve'] is True
        assert app.settings.data['asr']['cpu_threads'] == 2
        root.update()
        from PIL import ImageGrab
        ImageGrab.grab().save('/tmp/audio2idea_gui_20261014.png')
    finally:
        root.after_cancel(app.poll_id)
        root.destroy()


@pytest.mark.parametrize('appearance', ['light', 'dark'])
def test_appearance_persistence_and_minimum_layout(tmp_path, monkeypatch, appearance):
    import customtkinter as ctk
    import audio_to_idea.gui as gui
    from audio_to_idea.storage import read_json
    from PIL import ImageGrab
    cfg = deepcopy(DEFAULTS)
    cfg['ui']['appearance'] = appearance
    root = ctk.CTk()
    app = gui.AudioToIdeaApp(root, Settings(cfg, tmp_path / 'settings.json', {}))
    try:
        assert ctk.get_appearance_mode().lower() == appearance
        assert app.process_button.cget('state') == 'disabled'
        assert app.cancel_button.cget('state') == 'disabled'
        app.add([tmp_path / 'site inspection.wav'])
        app.select(app.items[0])
        assert app.process_button.cget('state') == 'normal'
        app.ideas.configure(state='normal')
        app.ideas.delete('1.0', 'end')
        app.render_ideas('# Inspection findings\n- Repair the bridge [S00001; 00:00:12].')
        app.ideas.configure(state='disabled')
        app.change_appearance(appearance.title())
        assert read_json(app.settings.path) == {'ui': {'appearance': appearance}}
        assert app.ideas.tag_cget('heading', 'foreground') == gui.colour(gui.ACCENT)
        # Let debounced gradient painting settle before capturing the window.
        deadline = time.monotonic() + .12
        while time.monotonic() < deadline:
            root.update(); time.sleep(.01)
        root.update()
        bbox = (root.winfo_rootx(), root.winfo_rooty(), root.winfo_rootx()+root.winfo_width(), root.winfo_rooty()+root.winfo_height())
        ImageGrab.grab(bbox=bbox).save(f'/tmp/audio2idea_modern_{appearance}_20261014.png')
        root.geometry('980x700')
        app.toggle_context()
        root.update()
        for widget in [app.transcript, app.ideas, app.process_button, app.progress]:
            assert widget.winfo_rooty() + widget.winfo_height() <= root.winfo_rooty() + root.winfo_height()
            assert widget.winfo_rootx() + widget.winfo_width() <= root.winfo_rootx() + root.winfo_width()
        assert app.transcript.winfo_height() >= 100
        ImageGrab.grab(bbox=(0, 0, 980, 700)).save(f'/tmp/audio2idea_compact_{appearance}_20261014.png')
        app.change_appearance('Dark' if appearance == 'light' else 'Light')
        assert app.ideas.tag_cget('heading', 'foreground') == gui.colour(gui.ACCENT)
        app.change_appearance('System')
        assert read_json(app.settings.path)['ui']['appearance'] == 'system'
    finally:
        root.after_cancel(app.poll_id)
        root.destroy()


@pytest.mark.parametrize('appearance', ['light', 'dark'])
def test_button_and_arrow_contrast_across_states(tmp_path, appearance):
    """Guard the actual visible colours, including CTk's disabled foreground."""
    import customtkinter as ctk
    import audio_to_idea.gui as gui
    def luminance(hex_colour):
        rgb = [int(hex_colour[i:i+2], 16) / 255 for i in (1, 3, 5)]
        values = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055)**2.4 for c in rgb]
        return sum(c*w for c, w in zip(values, [.2126, .7152, .0722]))
    def contrast(fg, bg):
        a, b = sorted([luminance(fg), luminance(bg)])
        return (b + .05) / (a + .05)
    cfg = deepcopy(DEFAULTS); cfg['ui']['appearance'] = appearance
    root = ctk.CTk(); app = gui.AudioToIdeaApp(root, Settings(cfg, tmp_path / 'settings.json', {}))
    try:
        for state in ['normal', 'disabled', 'normal']:
            for button in [app.process_button, app.transcribe_button, app.retry_button, app.cancel_button]:
                button.configure(state=state)
                fg = gui.colour(button.cget('text_color_disabled' if state == 'disabled' else 'text_color'))
                bg = gui.colour(button.cget('fg_color'))
                assert contrast(fg, bg) >= 4.5, (appearance, state, fg, bg)
        for menu in [app.mode_menu, app.appearance_menu]:
            assert contrast(gui.colour(menu.cget('text_color')), gui.colour(menu.cget('button_color'))) >= 4.5
        root.update()
        app.change_appearance('Dark' if appearance == 'light' else 'Light')
        root.geometry('1000x740')
        deadline = time.monotonic() + .12
        while time.monotonic() < deadline:
            root.update(); time.sleep(.01)
        assert app.backdrop._photo is not None
        assert app.backdrop._photo.width() == app.backdrop.winfo_width()
    finally:
        root.after_cancel(app.poll_id); root.destroy()


def test_discovery_remains_responsive_and_save_keeps_overrides_transient(tmp_path, monkeypatch):
    import threading
    import customtkinter as ctk
    import audio_to_idea.gui as gui
    import audio_to_idea.config as config
    from audio_to_idea.storage import read_json
    monkeypatch.setattr(gui, 'load_settings', config.load_settings)
    path = tmp_path / 'settings.json'
    path.write_text('{"asr": {"device": "cpu"}, "extension": {"keep": true}}')
    settings = config.load_settings(path, {'asr.device': 'cuda'}, environ={}, legacy_path=tmp_path / 'none')
    started, release = threading.Event(), threading.Event()
    def slow_discover(_):
        started.set()
        release.wait(5)
        return []
    monkeypatch.setattr(gui, 'discover', slow_discover)
    root = ctk.CTk()
    app = gui.AudioToIdeaApp(root, settings)
    window = gui.SettingsWindow(app)
    try:
        window.discover()
        assert started.wait(1)
        assert window.discovery_button.cget('state') == 'disabled'
        # Tk can still process a callback while the disk scan is blocked.
        tick = []
        root.after(0, lambda: tick.append(True))
        root.update()
        assert tick
        window.entries['ui.appearance'][0].set('light')
        window.save()  # Closing during a scan must cancel its UI poll safely.
        stored = read_json(path)
        assert stored['asr'] == {'device': 'cpu'}
        assert stored['extension']['keep'] is True
        assert stored['ui']['appearance'] == 'light'
        assert app.settings.data['asr']['device'] == 'cpu'
    finally:
        release.set()
        root.after_cancel(app.poll_id)
        root.destroy()


def test_legacy_launchers_use_current_interpreter(tmp_path, monkeypatch):
    import ast
    import sys
    import types
    root = Path(__file__).parents[2]
    for filename, clsname in [('tray_app.py', 'VoiceAssistantTray'), ('main_gui.py', 'VoiceAssistantGUI')]:
        tree = ast.parse((root / filename).read_text())
        cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == clsname)
        method = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == 'open_audio_to_idea')
        popen = Mock()
        scope = {'sys': sys, 'subprocess': types.SimpleNamespace(Popen=popen)}
        exec(compile(ast.Module(body=[method], type_ignores=[]), filename, 'exec'), scope)
        scope['open_audio_to_idea'](types.SimpleNamespace(script_dir=str(root)))
        assert popen.call_args.args[0] == [sys.executable, '-m', 'audio_to_idea', 'gui']
        assert popen.call_args.kwargs['cwd'] == str(root)


def test_clean_default_mode_and_prompt_editor(tmp_path, monkeypatch):
    import customtkinter as ctk
    import audio_to_idea.gui as gui
    from audio_to_idea.jobs import JobService
    from audio_to_idea.storage import read_json
    from audio_to_idea.templates import load_template, MODES
    from test_config_models import model
    from test_audio_exports import wav
    from test_jobs_synthesis import FakeASR, FakeLLM
    cfg = deepcopy(DEFAULTS)
    cfg['asr']['model_path'] = str(model(tmp_path / 'model'))
    cfg['synthesis']['model'] = 'fake'
    FakeLLM.fail = False
    monkeypatch.setattr(gui, 'JobService', lambda c: JobService(c, FakeASR, FakeLLM))
    errors = []
    monkeypatch.setattr(gui.messagebox, 'showerror', lambda *a, **k: errors.append(a))
    root = ctk.CTk()
    app = gui.AudioToIdeaApp(root, Settings(cfg, tmp_path / 'settings.json', {}))
    editor = None
    try:
        assert app.mode_var.get() == '1. Clean paragraph'
        app.add([wav(tmp_path / 'meeting.wav')])
        app.start(True)
        deadline = time.monotonic() + 10
        while (app.busy() or app.items[0]['result'] is None) and time.monotonic() < deadline:
            root.update(); time.sleep(.03)
        root.update()
        result = app.items[0]['result']
        assert result['status'] == 'complete' and result['synthesis_mode'] == 'clean_paragraph'
        assert app.ideas.get('1.0', 'end-1c').strip() == 'Inspect 123 किलोमीटर'
        editor = app.edit_prompt()
        editor.preview()
        assert 'Inspect 123 किलोमीटर' in editor.preview_box.get('1.0', 'end-1c')
        editor.editor.delete('1.0', 'end')
        editor.editor.insert('1.0', 'Tailor this recording. {transcript}\nContext: {context}\nLanguage: {output_language}')
        editor.save()
        path = tmp_path / 'audio_to_idea_prompts' / 'clean_paragraph.txt'
        assert path.is_file() and 'Tailor' in load_template(app.settings.data).text
        assert read_json(app.settings.path)['synthesis']['prompt_directory'] == str(path.parent)
        before = path.read_bytes()
        editor.editor.delete('1.0', 'end'); editor.editor.insert('1.0', 'Invalid missing input')
        editor.save()
        assert errors and path.read_bytes() == before
        editor.restore(); editor.save()
        assert 'Clean the transcript' in path.read_text()
        editor.window.destroy(); editor = None
        app.change_mode(MODES['concise_summary'])
        assert read_json(app.settings.path)['synthesis']['mode'] == 'concise_summary'
        assert 'Summarize the transcript briefly' in load_template(app.settings.data).text
        app.change_mode(MODES['clean_paragraph'])
        root.update()
        from PIL import ImageGrab
        ImageGrab.grab(bbox=(0, 0, 1280, 860)).save('/tmp/audio2idea_modes_gui_20261014.png')
    finally:
        if editor:
            editor.window.destroy()
        root.after_cancel(app.poll_id); root.destroy()
