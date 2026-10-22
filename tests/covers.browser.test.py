"""Exercise actual local image files and catalog variants in Chromium."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('https://**/*', lambda route: route.abort())
    page.goto('http://127.0.0.1:8000')
    page.locator('#start').click()
    for _ in range(5):
        page.locator('#next').click()
    page.locator('[data-value="school"]').click()
    page.locator('#primary').select_option(label='school')
    page.locator('#next').click()
    page.locator('#next').click()
    page.evaluate('''() => {
      const recommend = matchingEngine.recommend.bind(matchingEngine);
      matchingEngine.recommend = (books, profile, limit, options) => {
        const target = books.find(b => b.catalogCoverVariants?.length > 1 &&
          b.recommendationReady !== false && b.available !== false);
        if (!target) throw new Error('No actual catalog book with multiple covers');
        Object.assign(profile, {level: target.levels?.[0] || 'gt',
          interests: target.interests.slice(0, 12), primaryInterest: target.interests[0] || '',
          storyPreferences: (target.storyTags || []).slice(0, 5), themes: {}, avoidTopics: []});
        return recommend([target], profile, limit, options);
      };
    }''')
    page.locator('#next').click()
    page.locator('[data-book]').first.click()
    page.wait_for_function("document.querySelector('dialog img[data-cover]').src.includes('/assets/covers/')")
    assert page.locator('[data-cover-variant]').count() >= 2
    original = page.locator('dialog img[data-cover]').get_attribute('src')
    page.locator('[data-cover-variant]').last.click()
    assert page.locator('dialog img[data-cover]').get_attribute('src') != original
    assert page.locator('[data-cover-variant]').last.get_attribute('aria-pressed') == 'true'
    page.wait_for_function("document.querySelector('dialog img[data-cover]').complete && document.querySelector('dialog img[data-cover]').naturalWidth > 70")
    assert 'druk kan afwijken' in page.locator('dialog figcaption').inner_text()
    assert page.locator('.cover-source a').count() == 1
    for width in [390, 768, 1280]:
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.keyboard.press('Escape')
    assert not page.locator('dialog').is_visible()
    assert not errors, errors
    print('PASS: actual local cover, variant selection, source attribution, edition caveat, three viewport sizes and Escape; external HTTPS blocked')
    browser.close()
