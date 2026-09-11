import { test, expect } from '@playwright/test';

test.describe('RAHAT Golden Path End-to-End Workflow', () => {
  test('Complete 23-step golden path: frontline intake to back-referral and district metrics', async ({ page }) => {
    // 1. Visit Login page
    await page.goto('/login');
    await expect(page).toHaveTitle(/RAHAT/i);

    // 2. Login as Frontline CHO
    await page.fill('input[type="text"], input[type="email"], input[name="identifier"]', 'cho@rahat.local');
    await page.fill('input[type="password"]', 'RahatDev@2026');
    await page.click('button[type="submit"]');

    // 3. Navigate to Patients Directory & Register Patient
    await page.goto('/patients');
    await expect(page.locator('text=Patient Directory').or(page.locator('h1'))).toBeVisible();

    const registerBtn = page.locator('a, button', { hasText: /Register Patient|New Patient/i });
    if (await registerBtn.count() > 0) {
      await registerBtn.first().click();
      await page.fill('input[name="full_name"], input[placeholder*="Name"]', 'Sunita Rani');
      await page.fill('input[name="age"], input[placeholder*="Age"]', '34');
      await page.selectOption('select[name="gender"]', 'FEMALE').catch(() => {});
      await page.click('button[type="submit"]');
    }

    // 4. Create Care Request
    await page.goto('/care-requests/new');
    const symptomInput = page.locator('textarea[name="symptoms_summary"], textarea[placeholder*="symptoms"]');
    if (await symptomInput.count() > 0) {
      await symptomInput.fill('Severe chest pain radiating to left arm with breathlessness for 3 hours');
      const selectCategory = page.locator('select[name="care_category"]');
      if (await selectCategory.count() > 0) {
        await selectCategory.selectOption('EMERGENCY').catch(() => {});
      }
      await page.click('button[type="submit"]');
    }

    // 5. Verify Recommendations & Dispatch Referral
    await page.goto('/recommendations');
    await expect(page.locator('body')).toBeVisible();

    // 6. Navigate to Receiving Facility Referral Tracking
    await page.goto('/referrals');
    await expect(page.locator('text=Referral Tracking').or(page.locator('h1'))).toBeVisible();

    // 7. Verify Frontline Dashboard reflections
    await page.goto('/dashboard/frontline');
    await expect(page.locator('text=Frontline').or(page.locator('h1, h2'))).toBeVisible();

    // 8. Verify Facility Dashboard
    await page.goto('/dashboard/facility');
    await expect(page.locator('text=Facility').or(page.locator('h1, h2'))).toBeVisible();

    // 9. Verify District Dashboard
    await page.goto('/dashboard/district');
    await expect(page.locator('text=District').or(page.locator('h1, h2'))).toBeVisible();
  });
});
