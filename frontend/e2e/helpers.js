import { expect } from '@playwright/test'

export function uniqueEmail(prefix) {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 100000)}@example.com`
}

/**
 * Registers a brand-new user via the UI and leaves the browser on the
 * dashboard, authenticated. Returns the credentials used.
 */
export async function registerNewUser(page, prefix = 'user') {
  const email = uniqueEmail(prefix)
  const password = 'password123'
  const name = `${prefix} Test User`

  await page.goto('/register')
  await page.getByTestId('register-name').fill(name)
  await page.getByTestId('register-email').fill(email)
  await page.getByTestId('register-password').fill(password)
  await page.getByTestId('register-submit').click()

  await expect(page).toHaveURL('/')

  return { email, password, name }
}

/**
 * Creates a project from the dashboard and navigates into it.
 */
export async function createProject(page, name, description = '') {
  await page.goto('/')
  await page.getByTestId('project-name-input').fill(name)
  if (description) {
    await page.getByTestId('project-description-input').fill(description)
  }
  await page.getByTestId('create-project-submit').click()

  const projectLink = page.getByRole('link', { name })
  await expect(projectLink).toBeVisible()
  await projectLink.click()

  await expect(page.getByTestId('project-title')).toHaveText(name)
}
