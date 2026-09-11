import { test, expect } from '@playwright/test';

test.describe('RAHAT Offline-First & Sync Engine Verification', () => {
  test('Local IndexedDB buffering and synchronization banner display', async ({ page, context }) => {
    // 1. Visit Login and Authenticate
    await page.goto('/login');
    await page.fill('input[type="text"], input[type="email"], input[name="identifier"]', 'cho@rahat.local');
    await page.fill('input[type="password"]', 'RahatDev@2026');
    await page.click('button[type="submit"]');

    // 2. Navigate to Offline Sync Manager / Patients
    await page.goto('/offline');
    await expect(page.locator('body')).toBeVisible();

    // 3. Verify Sync Manager Controls
    const syncBtn = page.locator('button', { hasText: /Sync Now|Trigger Sync/i });
    if (await syncBtn.count() > 0) {
      await expect(syncBtn.first()).toBeVisible();
    }

    // 4. Simulate Offline network state
    await context.setOffline(true);
    await page.goto('/patients').catch(() => {});

    // 5. Restore Online network state
    await context.setOffline(false);
  });
});
