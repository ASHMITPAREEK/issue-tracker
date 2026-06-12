import { test, expect } from '@playwright/test'

function uniqueEmail(prefix) {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 100000)}@example.com`
}

test.describe('Authentication', () => {
  test('a new user can register and lands on the dashboard', async ({ page }) => {
    const email = uniqueEmail('register')

    await page.goto('/register')
    await page.getByTestId('register-name').fill('New User')
    await page.getByTestId('register-email').fill(email)
    await page.getByTestId('register-password').fill('password123')
    await page.getByTestId('register-submit').click()

    await expect(page).toHaveURL('/')
    await expect(page.getByTestId('nav-username')).toHaveText('New User')
    await expect(page.getByTestId('dashboard-stats')).toBeVisible()
  })

  test('a registered user can log in with valid credentials', async ({ page }) => {
    const email = uniqueEmail('login')

    // Register first via the UI so we have known credentials.
    await page.goto('/register')
    await page.getByTestId('register-name').fill('Login User')
    await page.getByTestId('register-email').fill(email)
    await page.getByTestId('register-password').fill('password123')
    await page.getByTestId('register-submit').click()
    await expect(page).toHaveURL('/')

    // Log out, then log back in.
    await page.getByTestId('logout-button').click()
    await expect(page).toHaveURL('/login')

    await page.getByTestId('login-email').fill(email)
    await page.getByTestId('login-password').fill('password123')
    await page.getByTestId('login-submit').click()

    await expect(page).toHaveURL('/')
    await expect(page.getByTestId('nav-username')).toHaveText('Login User')
  })

  test('login fails with an incorrect password', async ({ page }) => {
    const email = uniqueEmail('badlogin')

    await page.goto('/register')
    await page.getByTestId('register-name').fill('Bad Login User')
    await page.getByTestId('register-email').fill(email)
    await page.getByTestId('register-password').fill('password123')
    await page.getByTestId('register-submit').click()
    await expect(page).toHaveURL('/')
    await page.getByTestId('logout-button').click()

    await page.getByTestId('login-email').fill(email)
    await page.getByTestId('login-password').fill('wrong-password')
    await page.getByTestId('login-submit').click()

    await expect(page).toHaveURL('/login')
    await expect(page.getByTestId('form-error')).toBeVisible()
  })

  test('unauthenticated users are redirected to login', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL('/login')
  })
})
