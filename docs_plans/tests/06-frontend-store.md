# Frontend — Zustand store

**Директория:** `UI-UX/UI Final/frontend/src/store/__tests__/` (создать новую)

---

## 1. `__tests__/uiStore.test.ts` (~200 строк)

**Файл:** `uiStore.ts`

**Сценарии:**

### State — начальные значения
- `activeTab` = "chat"
- `themeMode` = "dark"
- `workMode` = "demo"
- `apiStatus` = "checking"
- `currentRole` = ""
- `currentUserId` = null
- `adminUsers` = `ADMIN_USERS` (из seed)
- `focusMode` = false

### Actions — auth
- `login(userId)`: `currentUserId` = userId, `currentRole` = роль пользователя
- `login(userId=1)`: admin → `currentRole` = "system_admin"
- `logout()`: `currentUserId` = null, `currentRole` = "", `chatMessages` = [], `currentGatewaySessionId` = null
- `setCurrentRole("engineer")`: `currentRole` = "engineer"

### Actions — navigation
- `setActiveTab("search")`: `activeTab` = "search"
- `setActiveTab("chat")`: `activeTab` = "chat"

### Actions — theme
- `setThemeMode("light")`: `themeMode` = "light"
- `setThemeMode("dark")`: `themeMode` = "dark"

### Actions — work mode
- `setWorkMode("prod")`: `workMode` = "prod"
- `setWorkMode("demo")`: `workMode` = "demo"
- `toggleWorkMode()`: переключение demo ↔ prod

### Actions — focus mode
- `setFocusMode(true)`: `focusMode` = true
- `setFocusMode(false)`: `focusMode` = false

### Actions — api status
- `setApiStatus("connected")`: `apiStatus` = "connected"
- `setApiStatus("error")`: `apiStatus` = "error"

### Actions — admin users
- `setAdminUsers([...])`: `adminUsers` обновлён
- `updateAdminUser(1, { role: "admin" })`: `adminUsers[1].role` = "admin"
- `addAdminAuditLogItem({...})`: элемент добавлен в `adminAuditLog`

### Actions — chat messages
- `setChatMessages([msg1, msg2])`: `chatMessages` = [msg1, msg2]
- `appendChatMessages(msg3)`: `chatMessages` = [msg1, msg2, msg3]
- `setCurrentGatewaySessionId("session-1")`: `currentGatewaySessionId` = "session-1"

### Сложные transitions
- `login(admin)` + `setActiveTab("admin")` → админка доступна
- `logout()` → `activeTab` не сбрасывается
- `updateAdminUser` → user обновлён в списке, сохраняются остальные
