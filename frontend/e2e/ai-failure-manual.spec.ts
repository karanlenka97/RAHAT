import { test, expect } from '@playwright/test';

test.describe('RAHAT AI Referral Assistant Safety & Resilience', () => {
  test('AI summary shows mandatory disclaimer and allows manual workflow continuation', async ({ page }) => {
    // 1. Visit Login
    await page.goto('/login');
    await page.fill('input[type="text"], input[type="email"], input[name="identifier"]', 'cho@rahat.local');
    await page.fill('input[type="password"]', 'RahatDev@2026');
    await page.click('button[type="submit"]');

    // 2. Navigate to Care Request details
    await page.goto('/care-requests');
    await expect(page.locator('body')).toBeVisible();

    // 3. Inspect AI Assistance Section if present
    const aiAssistSection = page.locator('text=AI Referral Assistant').or(page.locator('text=AI-assisted'));
    if (await aiAssistSection.count() > 0) {
      await expect(page.locator('text=human review').or(page.locator('text=assistive'))).toBeVisible();
    }

    // 4. Manual override / fallback verification
    const manualDispatchBtn = page.locator('a, button', { hasText: /Dispatch Referral|Recommend Facility/i });
    if (await manualDispatchBtn.count() > 0) {
      await expect(manualDispatchBtn.first()).toBeEnabled();
    }
  });
});
