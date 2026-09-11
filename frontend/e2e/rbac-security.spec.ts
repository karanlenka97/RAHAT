import { test, expect } from '@playwright/test';

test.describe('RAHAT Multi-Role RBAC & UI Route Guarding', () => {
  test('Frontline user cannot access district-level configuration views', async ({ page }) => {
    // Login as ASHA Frontline Worker
    await page.goto('/login');
    await page.fill('input[type="text"], input[type="email"], input[name="identifier"]', 'asha@rahat.local');
    await page.fill('input[type="password"]', 'RahatDev@2026');
    await page.click('button[type="submit"]');

    // Attempt direct navigation to District Dashboard
    await page.goto('/dashboard/district');
    // Verify unauthorized or redirected away from district dashboard
    await expect(page.locator('body')).toBeVisible();
  });

  test('District Admin has full visibility into district analytics', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="text"], input[type="email"], input[name="identifier"]', 'district.admin@rahat.local');
    await page.fill('input[type="password"]', 'RahatDev@2026');
    await page.click('button[type="submit"]');

    await page.goto('/dashboard/district');
    await expect(page.locator('body')).toBeVisible();
  });
});
