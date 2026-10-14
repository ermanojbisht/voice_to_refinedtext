"""Legacy window/menu smoke checks under a separate Xvfb desktop."""
from copy import deepcopy
import os
import sys
from unittest.mock import Mock

import pytest

pytestmark = [pytest.mark.desktop, pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Run with xvfb-run.')]


@pytest.mark.parametrize('enabled', [False, True])
def test_legacy_main_window_pipeline_and_optional_entry(tmp_path, monkeypatch, enabled):
    import customtkinter as ctk
    import main_gui
    from audio_to_idea.config import DEFAULTS, Settings
    import audio_to_idea.config as config
    module_cfg = deepcopy(DEFAULTS)
    module_cfg['integration']['enabled'] = enabled
    monkeypatch.setattr(config, 'load_settings', lambda *a, **kw: Settings(module_cfg, tmp_path / 'config.json', {}))
    engine = Mock(config={'MODE': 'refine'})
    engine.transcribe.return_value = 'raw voice'
    engine.refine.return_value = 'polished voice'
    monkeypatch.setattr(main_gui, 'VoiceEngine', lambda _: engine)
    monkeypatch.setattr(main_gui.subprocess, 'run', Mock())
    ctk.set_appearance_mode('dark')
    root = ctk.CTk()
    try:
        app = main_gui.VoiceAssistantGUI(root)
        app.run_voice_process()
        app.check_queue()
        assert 'polished voice' in app.result_text.get('1.0', 'end')
        assert engine.refine.call_args.args == ('raw voice',)
        def buttons(widget):
            found = []
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    found.append(child.cget('text'))
                found.extend(buttons(child))
            return found
        assert ('Audio to Ideas' in buttons(root)) == enabled
        assert 'Start Recording' in buttons(root) and 'Copy to Clipboard' in buttons(root)
    finally:
        for identifier in root.tk.call('after', 'info'):
            callback = root.tk.call('after', 'info', identifier)[0]
            # Cancel only callbacks registered by this root. Widgets own and
            # delete their own Tcl commands during destroy; deleting those via
            # root.after_cancel would corrupt their teardown bookkeeping.
            if callback in (root._tclCommands or []):
                root.after_cancel(identifier)
        root.destroy()


def test_legacy_tray_menu_without_state_or_audio_effects(monkeypatch):
    import tray_app
    import utils
    monkeypatch.setattr(utils, 'get_logger', Mock(return_value=Mock()))
    monkeypatch.setattr(tray_app.review_engine, 'init_logging', Mock())
    monkeypatch.setattr(tray_app.review_engine, 'check_startup_state', Mock(return_value=(None, None, None)))
    monkeypatch.setattr(tray_app.VoiceAssistantTray, '_init_wake_listener', lambda _: None)
    engine = Mock(config={'FEATURES': {'evening_review': True}, 'MODE': 'refine'})
    monkeypatch.setattr(tray_app, 'VoiceEngine', lambda _: engine)
    app = tray_app.VoiceAssistantTray()
    labels = [item.text for item in app.icon.menu.items]
    assert 'Start Recording' in labels and 'Start Evening Review' in labels
    assert 'Settings' in labels and 'Audio to Ideas' in labels
    assert app.is_in_review is False and app.is_recording is False
    assert not engine.record.called
