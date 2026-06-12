import { test, expect } from '@playwright/test'
import { registerNewUser, createProject, uniqueEmail } from './helpers.js'

test.describe('Projects', () => {
  test('a logged-in user can create a project', async ({ page }) => {
    await registerNewUser(page, 'projcreate')

    const projectName = `Website Revamp ${Date.now()}`
    await createProject(page, projectName, 'Revamp the marketing site')

    await expect(page.getByTestId('project-title')).toHaveText(projectName)

    // Dashboard reflects the new project.
    await page.goto('/')
    await expect(page.getByTestId('dashboard-stats')).toBeVisible()
    await expect(page.getByRole('link', { name: projectName })).toBeVisible()
  })

  test('creating a project with a blank name shows a validation error', async ({ page }) => {
    await registerNewUser(page, 'projblank')

    await page.getByTestId('project-name-input').fill('   ')
    await page.getByTestId('create-project-submit').click()

    await expect(page.getByTestId('create-project-error')).toBeVisible()
  })

  test('creating a project with a duplicate name shows an error', async ({ page }) => {
    await registerNewUser(page, 'projdup')

    const projectName = `Duplicate Project ${Date.now()}`
    await page.getByTestId('project-name-input').fill(projectName)
    await page.getByTestId('create-project-submit').click()
    await expect(page.getByRole('link', { name: projectName })).toBeVisible()

    // Try to create it again.
    await page.getByTestId('project-name-input').fill(projectName)
    await page.getByTestId('create-project-submit').click()

    await expect(page.getByTestId('create-project-error')).toBeVisible()
  })

  test('a project can be archived and unarchived', async ({ page }) => {
    await registerNewUser(page, 'projarchive')

    const projectName = `Archivable Project ${Date.now()}`
    await page.getByTestId('project-name-input').fill(projectName)
    await page.getByTestId('create-project-submit').click()

    const projectItem = page.getByTestId(/project-item-/).filter({ hasText: projectName })
    await projectItem.getByRole('button', { name: 'Archive' }).click()

    // No longer visible by default.
    await expect(page.getByRole('link', { name: projectName })).not.toBeVisible()

    // Visible again with "Show archived" toggled on.
    await page.getByTestId('show-archived-toggle').check()
    await expect(page.getByRole('link', { name: projectName })).toBeVisible()

    const archivedItem = page.getByTestId(/project-item-/).filter({ hasText: projectName })
    await archivedItem.getByRole('button', { name: 'Unarchive' }).click()
    await expect(archivedItem.getByRole('button', { name: 'Archive' })).toBeVisible()
  })
})
