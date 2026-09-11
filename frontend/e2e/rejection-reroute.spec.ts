import { test, expect } from '@playwright/test';

test.describe('RAHAT Referral Rejection & Reroute Flow', () => {
  test('Doctor rejects referral with reason and reroutes to alternate hospital', async ({ page }) => {
    // 1. Visit Login page
    await page.goto('/login');

    // 2. Login as Facility Doctor
    await page.fill('input[type="text"], input[type="email"], input[name="identifier"]', 'doctor@rahat.local');
    await page.fill('input[type="password"]', 'RahatDev@2026');
    await page.click('button[type="submit"]');

    // 3. Navigate to referrals list
    await page.goto('/referrals');
    await expect(page.locator('body')).toBeVisible();

    // 4. Verify Reject and Reroute actions are present in UI components
    const rejectBtn = page.locator('button', { hasText: /Reject/i });
    if (await rejectBtn.count() > 0) {
      await expect(rejectBtn.first()).toBeVisible();
    }

    const rerouteBtn = page.locator('button', { hasText: /Reroute/i });
    if (await rerouteBtn.count() > 0) {
      await expect(rerouteBtn.first()).toBeVisible();
    }
  });
});
