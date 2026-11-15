"""Drive the real SEVEN app in a visible terminal and save native SVG screens.

Uses Textual's Pilot against the unmodified application, with headless=False.
No fake responses, monkeypatches or image reconstruction. The isolated chat
database is local to output/. Run with the article's .venv Python from Windows
Terminal. --headless is available for a reproduction check without a window.
"""
from __future__ import annotations
import asyncio
import datetime
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SEVEN = Path(sys.argv[1])
os.environ['XDG_DATA_HOME'] = str(ROOT / 'output/tui-data')
os.environ['XDG_CONFIG_HOME'] = str(ROOT / 'output/tui-config')
os.environ['LEMONADE_BASE_URL'] = 'http://127.0.0.1:8081/v1'
os.environ['LEMONADE_TIMEOUT_SECONDS'] = '120'
for path in (SEVEN, SEVEN / 'apps/elia'):
    sys.path.insert(0, str(path))

async def main():
    import elia_chat.database.models
    from elia_chat.app import Elia
    from elia_chat.config import LaunchConfig
    from elia_chat.database.database import create_database, sqlite_file_name
    from elia_chat.widgets.prompt_input import PromptInput
    from elia_chat.widgets.chat import Chat
    from textual.widgets import RadioSet
    if not sqlite_file_name.exists():
        sqlite_file_name.parent.mkdir(parents=True, exist_ok=True)
        await create_database()
    app = Elia(config=LaunchConfig.get_current())
    captures = ROOT / 'assets/captures'
    captures.mkdir(parents=True, exist_ok=True)
    log = []
    def record(name, note):
        app.save_screenshot(filename=name + '.svg', path=str(captures))
        log.append({'file': 'assets/captures/' + name + '.svg', 'label': note,
            'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'local_profile': app.runtime_config.local_profile,
            'cloud_profile': app.runtime_config.cloud_profile})
        (ROOT / 'evidence/walkthrough.json').write_text(json.dumps(log, indent=2) + '\n', encoding='utf-8')
    async with app.run_test(headless='--headless' in sys.argv, size=(118, 38)) as pilot:
        await pilot.pause(4)
        record('01-home', 'SEVEN home, clean session')
        await pilot.press('f1'); await pilot.pause(3)
        record('02-help', 'Open built-in keyboard help')
        await pilot.press('escape'); await pilot.pause(1)
        await pilot.press('ctrl+o'); await pilot.pause(4)
        record('03-profiles', 'Inspect the software energy profiles')
        local = app.screen.query_one('#local-profiles', RadioSet)
        local.focus()
        await pilot.press('down', 'space'); await pilot.pause(3)
        record('04-profile-changed', 'Change the session energy profile; inference hardware stays the same')
        await pilot.press('escape'); await pilot.pause(2)
        questions = [
            ('05-local', 'What is the capital of France?', 'A local inference request'),
            ('06-api', 'What is the weather in Toronto?', 'Live-data branch; unavailable weather credentials remain visible'),
            ('07-cloud', 'Explain quantum chromodynamics.', 'Cloud branch; missing cloud credentials remain visible'),
        ]
        for name, question, note in questions:
            prompt = app.screen.query_one(PromptInput)
            prompt.focus()
            await pilot.press(*list(question))
            await pilot.pause(3)
            record(name + '-prompt', note + ' — input')
            await pilot.press('ctrl+j'); await pilot.pause(1)
            record(name + '-working', note + ' — routing')
            for _ in range(120):
                await pilot.pause(1)
                chat = app.screen.query_one(Chat)
                if chat.allow_input_submit:
                    break
            await pilot.pause(4)
            record(name + '-answer', note + ' — actual outcome')
            if name == '05-local':
                await pilot.press('f2'); await pilot.pause(4)
                record('05-local-details', 'Inspect the saved chat information')
                await pilot.press('escape'); await pilot.pause(1)
            await pilot.press('escape'); await pilot.pause(2)
        record('08-history', 'The real application history after the walkthrough')
        await pilot.pause(10)

if __name__ == '__main__':
    asyncio.run(main())
