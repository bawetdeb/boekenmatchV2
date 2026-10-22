from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.route('https://**/*', lambda route: route.abort())
    page.goto('http://127.0.0.1:8000')
    page.locator('#start').click()
    total = page.evaluate('quizConfig.questions.length')
    assert total == 8
    for index in range(5):
        assert page.locator('progress').get_attribute('value') == str(index+1)
        if index == 1:
            for year in [1,2,3,4]:
                page.locator(f'[data-value="{year}"]').click()
                assert page.evaluate('appState.profile.schoolYear') == year
            page.locator('[data-value="1"]').click()
        page.locator('#next').click()
    page.locator('#next').click()
    assert 'Kies minstens' in page.locator('#validation').inner_text()
    for value in ['voetbal', 'Formule 1', 'fitness', 'vechtsport', 'basketbal', 'skateboarden', 'wintersport', 'andere sport', 'games', 'social media', 'YouTube', 'films']:
        page.locator(f'[data-value="{value}"]').click()
    assert page.evaluate('appState.profile.interests.length') == 12
    page.locator('[data-value="series"]').click()
    assert 'maximaal 12' in page.locator('#validation').inner_text()
    assert page.locator('[data-value="series"]').get_attribute('aria-pressed') == 'false'
    page.locator('#primary').select_option(label='voetbal')
    page.locator('#back').click()
    page.locator('[data-value="any"]').click()
    assert page.evaluate('appState.profile.readingDifficulty') is None
    page.locator('#next').click()
    assert page.locator('#primary').input_value() == 'voetbal'
    page.locator('#next').click()
    for value in ['spanning', 'humor', 'romantiek', 'sport', 'school']:
        page.locator(f'[data-value="{value}"]').click()
    page.locator('[data-value="horror"]').click()
    assert 'maximaal 5' in page.locator('#validation').inner_text()
    assert page.locator('[data-value="horror"]').get_attribute('aria-pressed') == 'false'
    page.locator('#next').click()
    page.locator('[data-theme="spanning"]').fill('5')
    assert page.locator('#out-spanning').inner_text() == '5'
    assert page.locator('progress').get_attribute('value') == '8'
    assert 'Ontdek mijn top 5' in page.locator('#next').inner_text()
    for key in ['realismFantasy', 'readingSpeed', 'maxPages']:
        assert page.evaluate(f'appState.profile.{key}') is None
    assert page.evaluate('appState.profile.avoidTopics') == []
    page.locator('#next').click()
    assert page.locator('.book-card').count() == 5
    assert page.evaluate('bookRepository.status.source') == 'aura'
    assert 'bevestigde titels' in page.locator('.notice').inner_text()
    first = page.locator('[data-book]').evaluate_all('(els)=>els.map(x=>x.dataset.book)')
    page.locator('[data-book]').first.hover()
    assert page.locator('.hover-summary').count() == 0
    assert not page.locator('dialog').is_visible()
    page.locator('[data-book]').first.click()
    assert page.locator('dialog').is_visible()
    assert page.locator('.match-explanation').is_visible()
    assert 'Waarom dit boek bij jou past' in page.locator('.match-explanation').inner_text()
    assert page.locator('.match-explanation li').count() > 0
    assert page.locator('.story-summary').is_visible()
    assert 'Beschikbaarheid' in page.locator('dialog').inner_text()
    assert 'laatste controle' in page.locator('dialog').inner_text()
    assert page.locator('dialog a').get_attribute('href').startswith('https://bogerman.auralibrary.nl/')
    page.keyboard.press('Escape')
    assert not page.locator('dialog').is_visible()
    page.locator('[data-feedback="1"]').first.click()
    assert page.locator('[data-feedback="1"][aria-pressed=true]').count() == 1
    assert page.evaluate('Object.keys(JSON.parse(sessionStorage.getItem("boekenmatch-feedback"))).length') == 1
    page.locator('#more').click()
    second = page.locator('[data-book]').evaluate_all('(els)=>els.map(x=>x.dataset.book)')
    assert not set(first) & set(second)
    for size in [{'width':390,'height':844},{'width':768,'height':1024},{'width':1280,'height':900}]:
        page.set_viewport_size(size)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), size
        page.locator('[data-book]').first.click()
        assert page.locator('dialog').is_visible()
        page.locator('#close').click()
    page.emulate_media(reduced_motion='reduce')
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path='/tmp/boekenmatch-mobile.png',full_page=True)
    page.locator('#edit').click()
    assert page.locator('progress').get_attribute('value') == '1'
    assert page.evaluate('getComputedStyle(document.querySelector(".question")).animationName') == 'none'
    page.reload()
    assert page.evaluate('Object.keys(appState.feedback).length') == 1
    assert not errors, errors
    print('PASS: 8 steps, school years 1–4, progress/back, 12-interest and 5-theme limits, neutral choices, sliders, removed preferences neutral, modal, feedback, unseen alternatives, responsive sizes, reduced motion, session reload; no JavaScript errors')
    browser.close()
