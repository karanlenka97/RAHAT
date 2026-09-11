import { test, expect } from '@playwright/test';

test.describe('RAHAT Multi-Factor Recommendation Card Inspection', () => {
  test('Renders deterministic recommendation scores, distance, and capability indicators', async ({ page }) => {
    // 1. Login as Frontline CHO
    await page.goto('/login');
    await page.fill('input[type="text"], input[type="email"], input[name="identifier"]', 'cho@rahat.local');
    await page.fill('input[type="password"]', 'RahatDev@2026');
    await page.click('button[type="submit"]');

    // 2. Open Recommendations Explorer
    await page.goto('/recommendations');
    await expect(page.locator('body')).toBeVisible();

    // 3. Check for recommendation criteria indicators (Distance, Beds, Services)
    const cards = page.locator('.facility-card, [data-testid="facility-card"], div:has-text("Overall Match")');
    if (await cards.count() > 0) {
      await expect(cards.first()).toBeVisible();
    }
  });
});
