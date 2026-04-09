## Root Cause
- The “Sign up” button in `Login` calls `onSwitchToRegister`, which in Home sets the view back to `welcome` instead of showing a registration flow.
- Evidence: `frontend/src/pages/Home.js:28-31` shows `<Login onLogin={handleLogin} onSwitchToRegister={() => setCurrentView('welcome')} />`.
- There is no `Register` component or route; therefore, clicking “Sign up” simply returns to the landing page.

## Constraints
- Do not modify AI service files or anything tied to the AI chat backend.
- Keep the existing chat behavior and Python/AI service intact.

## Proposed Changes
- Create a `Register` component for email/password registration (matching backend API).
- Wire Home to navigate to `register` view instead of `welcome` when “Sign up” is clicked.
- Add a route for `/register` in `App.js` or continue with Home’s view-based switch; prefer a route for consistency.
- Implement `authAPI.register(email, password, userType)` calling backend (e.g., `POST /auth/register`) without touching AI chat code.
- On successful registration: either auto-login or redirect to login with success message.
- Form validation and error messages based on backend responses.

## Detailed Steps
1. Add `Register` component under `frontend/src/components/Register.js` with fields: email, password, confirm password, userType (patient/staff), and a submit button.
2. Extend `frontend/src/services/api.js` with `authAPI.register(...)` only; leave chat and AI endpoints untouched.
3. Update `frontend/src/pages/Home.js` to handle `currentView === 'register'` and render `<Register onSwitchToLogin={() => setCurrentView('login')} />`.
4. Adjust `Login` “Sign up” button to call `onSwitchToRegister` which sets `currentView('register')`.
5. Optional: add `/register` route in `frontend/src/App.js` so direct navigation works; keep Home logic to avoid breaking existing landing behavior.
6. Show toast messages on success/failure; on success, navigate to login and prefill email or auto-login if preferred.

## Validation
- From Home, click “Healthcare Staff Login” then “Sign up” → registration form appears.
- Submit valid info → backend returns success → redirected to login or auto-logged-in; token persists via `AuthContext`.
- Ensure no changes to AI chat files or endpoints; chat continues to function.

## Files Impacted
- `frontend/src/pages/Home.js` (view handling for `register`).
- `frontend/src/components/Login.js` (Sign up button handler only).
- `frontend/src/components/Register.js` (new).
- `frontend/src/services/api.js` (add `authAPI.register` only).
- `frontend/src/App.js` (optional route for `/register`).

Do you want me to proceed with these frontend-only changes while leaving AI service files untouched?