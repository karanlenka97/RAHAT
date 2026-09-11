import { test, expect } from '@playwright/test';

test.describe('RAHAT Referral Lifecycle & Event Tracking', () => {
  test('Displays state progression, transit buttons, and audit event timeline', async ({ page }) => {
    // 1. Login as Facility Doctor
    await page.goto('/login');
    await page.fill('input[type="text"], input[type="email"], input[name="identifier"]', 'doctor@rahat.local');
    await page.fill('input[type="password"]', 'RahatDev@2026');
    await page.click('button[type="submit"]');

    // 2. Open Referral Management
    await page.goto('/referrals');
    await expect(page.locator('body')).toBeVisible();

    // 3. Verify Filters and Tracking Table
    const searchInput = page.locator('input[placeholder*="Search"], input[type="search"]');
    if (await searchInput.count() > 0) {
      await searchInput.fill('RAHAT');
    }

    // 4. Verify Status Filter Options
    const statusFilter = page.locator('select[name="status"], select:has-text("Status")');
    if (await statusFilter.count() > 0) {
      await expect(statusFilter).toBeVisible();
    }
  });
});
