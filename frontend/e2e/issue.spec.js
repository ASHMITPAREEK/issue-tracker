import { test, expect } from '@playwright/test'
import { registerNewUser, createProject } from './helpers.js'

test.describe('Issues', () => {
  test('a user can create an issue on a project', async ({ page }) => {
    await registerNewUser(page, 'issuecreate')
    await createProject(page, `Issue Project ${Date.now()}`)

    await page.getByTestId('toggle-issue-form').click()
    await page.getByTestId('issue-form').waitFor()

    const issueTitle = `Fix login bug ${Date.now()}`
    await page.getByTestId('issue-title-input').fill(issueTitle)
    await page.getByTestId('issue-description-input').fill('Login button does nothing on click')
    await page.getByTestId('issue-priority-input').selectOption('High')
    await page.getByTestId('issue-form-submit').click()

    const row = page.locator('tr', { hasText: issueTitle })
    await expect(row).toBeVisible()
    await expect(row.getByText('High')).toBeVisible()
    await expect(row.locator('select[data-testid^="issue-status-select-"]')).toHaveValue('Todo')
  })

  test('creating an issue with a blank title shows a validation error', async ({ page }) => {
    await registerNewUser(page, 'issueblank')
    await createProject(page, `Issue Blank Project ${Date.now()}`)

    await page.getByTestId('toggle-issue-form').click()
    await page.getByTestId('issue-form').waitFor()

    await page.getByTestId('issue-title-input').fill('   ')
    await page.getByTestId('issue-form-submit').click()

    await expect(page.getByTestId('issue-form-error')).toBeVisible()
  })

  test('an issue status can be changed from the issue table', async ({ page }) => {
    await registerNewUser(page, 'issuestatus')
    await createProject(page, `Issue Status Project ${Date.now()}`)

    await page.getByTestId('toggle-issue-form').click()
    await page.getByTestId('issue-form').waitFor()

    const issueTitle = `Status change issue ${Date.now()}`
    await page.getByTestId('issue-title-input').fill(issueTitle)
    await page.getByTestId('issue-form-submit').click()

    const row = page.locator('tr', { hasText: issueTitle })
    await expect(row).toBeVisible()

    const statusSelect = row.locator('select[data-testid^="issue-status-select-"]')
    await statusSelect.selectOption('In Progress')
    await expect(statusSelect).toHaveValue('In Progress')

    // Persists after reload.
    await page.reload()
    const reloadedRow = page.locator('tr', { hasText: issueTitle })
    const reloadedStatus = reloadedRow.locator('select[data-testid^="issue-status-select-"]')
    await expect(reloadedStatus).toHaveValue('In Progress')
  })

  test('issues can be filtered by status', async ({ page }) => {
    await registerNewUser(page, 'issuefilter')
    await createProject(page, `Issue Filter Project ${Date.now()}`)

    // Create two issues.
    for (const title of ['Todo Issue', 'Done Issue']) {
      await page.getByTestId('toggle-issue-form').click()
      await page.getByTestId('issue-form').waitFor()
      await page.getByTestId('issue-title-input').fill(`${title} ${Date.now()}`)
      await page.getByTestId('issue-form-submit').click()
      await page.getByTestId('issue-form').waitFor({ state: 'detached' })
    }

    await page.getByTestId('status-filter').selectOption('Todo')
    await expect(page.getByTestId('issue-table')).toContainText('Todo Issue')
  })

  test('the dashboard reflects newly created issues', async ({ page }) => {
    await registerNewUser(page, 'issuedash')
    await createProject(page, `Issue Dashboard Project ${Date.now()}`)

    await page.getByTestId('toggle-issue-form').click()
    await page.getByTestId('issue-form').waitFor()
    await page.getByTestId('issue-title-input').fill(`Dashboard issue ${Date.now()}`)
    await page.getByTestId('issue-form-submit').click()

    await page.goto('/')
    await expect(page.getByTestId('stat-total-issues').locator('.stat-value')).toHaveText('1')
    await expect(page.getByTestId('stat-open-issues').locator('.stat-value')).toHaveText('1')
  })
})
